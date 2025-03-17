"""
GitHub repository access utilities.
"""

import base64
import time
import concurrent.futures
from typing import Dict, List, Tuple, Any, Optional

from src.models.types import RepoDetails
from src.models.config import Config
from src.utils.timeout import GitHubAccessError, with_timeout


class GitHubRepository:
    """Class for interacting with GitHub repositories."""
    
    def __init__(self, config: Config):
        """
        Initialize with configuration.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.repo = None
        self.repo_owner = None
        self.repo_name = None
        self.code_sample_files = []  # Track filenames of collected code samples
    
    def parse_github_url(self, repo_url: str) -> Tuple[str, str]:
        """
        Parse a GitHub URL to extract owner and repository name.
        
        Args:
            repo_url: URL of the GitHub repository
            
        Returns:
            Tuple of repository owner and name
            
        Raises:
            ValueError: If the URL is not a valid GitHub repository URL
        """
        # Extract repo owner and name from URL
        repo_parts = repo_url.strip("/").split("/")
        if "github.com" not in repo_url or len(repo_parts) < 5:
            raise ValueError(f"Invalid GitHub URL: {repo_url}")
        
        repo_owner = repo_parts[-2]
        repo_name = repo_parts[-1]
        
        return repo_owner, repo_name
    
    def connect_to_github_api(self, repo_owner: str, repo_name: str) -> Any:
        """
        Connect to GitHub API and get repository object.
        
        Args:
            repo_owner: Owner of the repository
            repo_name: Name of the repository
            
        Returns:
            GitHub repository object or None if connection fails
        """
        if not self.config.github_token:
            print(f"No GitHub token provided. Using limited repository information for {repo_owner}/{repo_name}")
            return None
        
        # If we have a token, use PyGithub for direct access
        try:
            from github import Github
            
            # Initialize GitHub client
            g = Github(self.config.github_token)
            
            # Get repository
            repo = g.get_repo(f"{repo_owner}/{repo_name}")
            
            # Simple check if repository exists and is accessible
            _ = repo.name
            
            return repo
            
        except Exception as e:
            error_msg = f"Error accessing repository {repo_owner}/{repo_name}: {str(e)}"
            print(error_msg)
            raise GitHubAccessError(error_msg)
    
    def setup_repository(self, repo_url: str) -> Tuple[str, str]:
        """
        Set up GitHub connection for a repository.
        
        Args:
            repo_url: URL of the GitHub repository
            
        Returns:
            Tuple of repository owner and name
        """
        # Parse GitHub URL to get owner and name
        repo_owner, repo_name = self.parse_github_url(repo_url)
        
        try:
            # Connect to GitHub API and get repository object
            self.repo = self.connect_to_github_api(repo_owner, repo_name)
        except GitHubAccessError:
            # If we can't access the repository, set repo to None
            self.repo = None
        
        # Store repository info regardless of API success
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        
        return repo_owner, repo_name
    
    def create_fallback_repo_details(self, repo_owner: str, repo_name: str, repo_url: str) -> RepoDetails:
        """
        Create fallback repository details when repository access fails.
        
        Args:
            repo_owner: Owner of the repository
            repo_name: Name of the repository
            repo_url: URL of the repository
            
        Returns:
            RepoDetails with basic information
        """
        return {
            "name": repo_name,
            "description": f"Repository for {repo_owner}/{repo_name}",
            "url": repo_url,
            "stars": 0,
            "forks": 0,
            "open_issues": 0,
            "last_update": "",
            "language": "",
            "contributors": [],
            "total_contributors": 0,
            "commit_stats": {
                "total_commits": 0,
                "first_commit_date": "",
                "latest_commit_date": "",
                "commit_frequency": 0.0,
                "commit_history": {}
            },
            "main_languages": {},
            "license_type": None,
            "created_at": "",
            "size_kb": 0,
            "pull_requests": {
                "open": 0,
                "closed": 0,
                "merged": 0,
                "total": 0
            }
        }
    
    @with_timeout(30)
    def get_total_contributor_count(self) -> int:
        """
        Get the total number of contributors for a repository.
        
        Returns:
            Total number of contributors
        """
        if self.repo is None:
            return 0
            
        try:
            # Get contributor count - count all contributors
            contributors = self.repo.get_contributors()
            # This could be expensive for large repos, so we'll use pagination
            # and count efficiently
            
            contributor_count = 0
            for _ in contributors:
                contributor_count += 1
                if contributor_count > 100:  # Cap at 100 for performance reasons
                    break
                    
            return contributor_count
        except Exception as e:
            print(f"Error counting repository contributors: {str(e)}")
            return 0
    
    @with_timeout(60)  # Increased timeout for PR stats
    def get_pull_request_stats(self) -> Dict[str, int]:
        """
        Get pull request statistics for the repository.
        
        Returns:
            Dictionary with PR statistics
        """
        if self.repo is None:
            return {
                "open": 0,
                "closed": 0,
                "merged": 0,
                "total": 0
            }
            
        try:
            # Get open PRs count - use totalCount which is faster than fetching all PRs
            try:
                open_prs = self.repo.get_pulls(state='open').totalCount
            except Exception as e:
                print(f"Error getting open PRs count: {str(e)}")
                open_prs = 0
            
            # Get closed PRs count
            try:
                closed_prs = self.repo.get_pulls(state='closed').totalCount
            except Exception as e:
                print(f"Error getting closed PRs count: {str(e)}")
                closed_prs = 0
            
            # Get merged PRs (subset of closed)
            merged_prs_count = 0
            
            # Only sample closed PRs if there are any
            if closed_prs > 0:
                try:
                    # Limit the sample to max 20 to avoid timeouts
                    sample_size = min(20, closed_prs)
                    sample_closed_prs = list(self.repo.get_pulls(state='closed')[:sample_size])
                    
                    if sample_closed_prs:
                        merged_count = sum(1 for pr in sample_closed_prs if pr.merged)
                        # Calculate merge percentage and estimate total merged
                        merge_percentage = merged_count / len(sample_closed_prs)
                        merged_prs_count = int(closed_prs * merge_percentage)
                except Exception as e:
                    print(f"Error sampling closed PRs: {str(e)}")
            
            return {
                "open": open_prs,
                "closed": closed_prs,
                "merged": merged_prs_count,
                "total": open_prs + closed_prs
            }
        except Exception as e:
            print(f"Error getting pull request stats: {str(e)}")
            return {
                "open": 0,
                "closed": 0,
                "merged": 0,
                "total": 0
            }
    
# Method removed as its functionality is now in get_top_contributors_details
    
    def get_top_contributors_details(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get detailed information about top contributors.
        
        Args:
            limit: Number of top contributors to fetch details for
            
        Returns:
            List of dictionaries with contributor details
        """
        if self.repo is None:
            return []
            
        try:
            # First get basic contributor info
            basic_contributors = self.get_repository_contributors(limit=limit)
            
            if not basic_contributors:
                return []
                
            # Process contributors sequentially to avoid signal errors
            detailed_contributors = []
            
            for contributor in basic_contributors:
                username = contributor["login"]
                try:
                    # Get contributor details with a longer timeout
                    contributor_details = {}
                    
                    # Only try to get details if we have a GitHub token
                    if self.config.github_token:
                        from github import Github
                        try:
                            g = Github(self.config.github_token)
                            user = g.get_user(username)
                            
                            contributor_details = {
                                "username": user.login,
                                "name": user.name,
                                "company": user.company,
                                "location": user.location,
                                "email": user.email,
                                "bio": user.bio,
                                "followers": user.followers,
                                "following": user.following,
                                "twitter_username": user.twitter_username,
                                "blog": user.blog,
                                "public_repos": user.public_repos,
                                "profile_url": user.html_url
                            }
                        except Exception as detail_error:
                            print(f"Error getting details for {username}: {str(detail_error)}")
                            contributor_details = {
                                "username": username,
                                "profile_url": f"https://github.com/{username}"
                            }
                    else:
                        contributor_details = {
                            "username": username,
                            "profile_url": f"https://github.com/{username}"
                        }
                    
                    # Find the basic contributor info
                    basic_info = contributor
                    
                    # Merge basic and detailed info
                    merged_info = {**basic_info, **contributor_details}
                    detailed_contributors.append(merged_info)
                except Exception as e:
                    print(f"Error processing contributor {username}: {str(e)}")
                    # Add basic info anyway
                    detailed_contributors.append(contributor)
            
            # Sort by contributions
            detailed_contributors.sort(key=lambda x: x.get("contributions", 0), reverse=True)
            
            return detailed_contributors
            
        except Exception as e:
            print(f"Error getting top contributors details: {str(e)}")
            return []
    
    @with_timeout(90)  # Increased timeout for repository details
    def get_repository_details(self) -> RepoDetails:
        """
        Get repository details using GitHub API.
        
        Returns:
            RepoDetails with repository information
        """
        # If we don't have the repo object, return fallback info
        if self.repo is None:
            return self.create_fallback_repo_details(
                self.repo_owner, 
                self.repo_name, 
                f"https://github.com/{self.repo_owner}/{self.repo_name}"
            )
        
        try:
            # Initialize with basic details
            repo_info = {
                "name": self.repo.name,
                "description": self.repo.description or "",
                "url": self.repo.html_url,
                "stars": self.repo.stargazers_count,
                "forks": self.repo.forks_count,
                "open_issues": self.repo.open_issues_count,
                "last_update": self.repo.updated_at.isoformat() if self.repo.updated_at else "",
                "language": self.repo.language or "",
                "contributors": [],
                "detailed_contributors": [],
                "total_contributors": 0,
                "commit_stats": {
                    "total_commits": 0,
                    "first_commit_date": "",
                    "latest_commit_date": "",
                    "commit_frequency": 0.0,
                    "commit_history": {}
                },
                "main_languages": {},
                "license_type": self.repo.license.name if self.repo.license else None,
                "created_at": self.repo.created_at.isoformat() if self.repo.created_at else "",
                "size_kb": self.repo.size,
                "pull_requests": {
                    "open": 0,
                    "closed": 0,
                    "merged": 0,
                    "total": 0
                }
            }
            
            # Get data in try/except blocks to ensure we get as much as possible
            try:
                # Get total contributor count
                total_contributors = self.get_total_contributor_count()
                repo_info["total_contributors"] = total_contributors
            except Exception as e:
                print(f"Error getting contributor count: {str(e)}")
            
            try:
                # Get top contributors list (limited to top 5 for display)
                contributors = self.get_repository_contributors(limit=5)
                repo_info["contributors"] = contributors
            except Exception as e:
                print(f"Error getting contributors: {str(e)}")
            
            try:
                # Get commit statistics
                commit_stats = self.get_repository_commit_stats()
                repo_info["commit_stats"] = commit_stats
            except Exception as e:
                print(f"Error getting commit stats: {str(e)}")
            
            try:
                # Get main languages
                languages = self.get_repository_languages()
                repo_info["main_languages"] = languages
            except Exception as e:
                print(f"Error getting languages: {str(e)}")
            
            try:
                # Get pull request stats
                pr_stats = self.get_pull_request_stats()
                repo_info["pull_requests"] = pr_stats
            except Exception as e:
                print(f"Error getting PR stats: {str(e)}")
            
            try:
                # Get detailed information for top contributors
                detailed_contributors = self.get_top_contributors_details(limit=5)
                repo_info["detailed_contributors"] = detailed_contributors
            except Exception as e:
                print(f"Error getting detailed contributor info: {str(e)}")
            
            return repo_info
            
        except Exception as e:
            error_msg = f"Error getting repository details: {str(e)}"
            print(error_msg)
            return self.create_fallback_repo_details(
                self.repo_owner, 
                self.repo_name, 
                f"https://github.com/{self.repo_owner}/{self.repo_name}"
            )
    
    def collect_code_samples(self, progress_callback=None) -> Tuple[Dict[str, int], List[str]]:
        """
        Collect code samples and file metrics from repository.
        
        Args:
            progress_callback: Optional callback for progress updates
            
        Returns:
            Tuple of file metrics and code samples
        """
        # Get repository contents
        contents = self.repo.get_contents("")
        
        # Initialize counters
        file_count = 0
        test_file_count = 0
        doc_file_count = 0
        
        # Process files recursively
        files_to_process = list(contents)
        processed_paths = set()
        
        # Code samples for analysis
        code_samples = []
        code_file_paths = []
        self.code_sample_files = []  # Clear previous file names
        
        # Maximum files to process to avoid excessive API calls
        max_files_to_process = 100
        files_processed = 0
        last_update_time = 0
        update_interval = 0.5  # Update progress every 0.5 seconds
        
        import time
        start_time = time.time()
        
        # Process repository files
        while files_to_process and files_processed < max_files_to_process:
            content = files_to_process.pop(0)
            if content.path in processed_paths:
                continue
            
            processed_paths.add(content.path)
            files_processed += 1
            
            # Update progress periodically
            current_time = time.time()
            if progress_callback and (current_time - last_update_time) > update_interval:
                last_update_time = current_time
                progress_callback(f"Collecting code samples - processed {files_processed} files, found {len(code_samples)} code samples")
            
            if content.type == "dir":
                try:
                    # Add directory contents to processing queue
                    dir_contents = self.repo.get_contents(content.path)
                    if isinstance(dir_contents, list):
                        files_to_process.extend(dir_contents)
                    else:
                        files_to_process.append(dir_contents)
                except Exception:
                    # Skip directories we can't access
                    continue
                    
            elif content.type == "file":
                file_count += 1
                file_path = content.path
                
                # Classify file types
                if "test" in file_path.lower() or "spec" in file_path.lower():
                    test_file_count += 1
                    
                if file_path.lower().endswith((".md", ".rst", ".txt", ".doc", ".docx")):
                    doc_file_count += 1
                    
                # Collect code file samples
                code_extensions = (".js", ".ts", ".jsx", ".tsx", ".py", ".java", ".sol", 
                                  ".go", ".rb", ".php", ".c", ".cpp", ".cs", ".html", ".css", ".scss", ".json")
                if file_path.lower().endswith(code_extensions):
                    try:
                        # Add to code file paths
                        code_file_paths.append(file_path)
                        
                        # Only sample up to 15 code files (increased from 10 for deep analysis)
                        if len(code_samples) < 15:
                            file_content = self.repo.get_contents(file_path).decoded_content.decode('utf-8')
                            # Limit sample size
                            sample = file_content[:1500] + "..." if len(file_content) > 1500 else file_content
                            code_samples.append(f"File: {file_path}\n\n{sample}\n\n")
                            # Store file path for deep code analysis
                            self.code_sample_files.append(file_path)
                    except Exception:
                        # Skip files that can't be decoded
                        continue
        
        # Compile file metrics
        file_metrics = {
            "file_count": file_count,
            "test_file_count": test_file_count,
            "doc_file_count": doc_file_count,
            "code_files_analyzed": len(code_file_paths)
        }
        
        # Final progress update
        if progress_callback:
            elapsed = time.time() - start_time
            progress_callback(f"Completed collecting {len(code_samples)} code samples from {file_count} files in {elapsed:.1f}s")
        
        return file_metrics, code_samples
        
    def search_files_for_keywords(self, file_paths: List[str], keywords: List[str]) -> List[Dict[str, str]]:
        """
        Search specific files for keywords.
        
        Args:
            file_paths: List of file paths to search
            keywords: List of keywords to search for
            
        Returns:
            List of evidence dictionaries
        """
        evidence = []
        
        for file_path in file_paths:
            try:
                content = self.repo.get_contents(file_path)
                if content and content.type == "file":
                    content_str = base64.b64decode(content.content).decode('utf-8')
                    for keyword in keywords:
                        if keyword.lower() in content_str.lower():
                            evidence.append({
                                "file": file_path,
                                "keyword": keyword
                            })
            except Exception:
                # File doesn't exist, skip
                continue
                
        return evidence
        
    @with_timeout(30)
    def get_repository_contributors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get repository contributors using GitHub API.
        
        Args:
            limit: Maximum number of contributors to return
            
        Returns:
            List of contributor details
        """
        if self.repo is None:
            return []
            
        try:
            contributors = []
            for contributor in self.repo.get_contributors()[:limit]:
                contributors.append({
                    "login": contributor.login,
                    "profile_url": contributor.html_url,
                    "contributions": contributor.contributions,
                    "avatar_url": contributor.avatar_url if hasattr(contributor, "avatar_url") else None
                })
            return contributors
        except Exception as e:
            print(f"Error getting repository contributors: {str(e)}")
            return []
            
    @with_timeout(45)  # This can take longer so we give it more time
    def get_repository_commit_stats(self) -> Dict[str, Any]:
        """
        Get repository commit statistics.
        
        Returns:
            Dictionary with commit stats
        """
        if self.repo is None:
            return {
                "total_commits": 0,
                "first_commit_date": "",
                "latest_commit_date": "",
                "commit_frequency": 0.0,
                "commit_history": {}
            }
            
        try:
            import datetime
            from collections import defaultdict
            
            # Get commit count (limitation: only counts recent commits)
            commit_count = 0
            first_commit = None
            latest_commit = None
            commit_dates = []
            monthly_commits = defaultdict(int)
            
            # Sample commits with a maximum to avoid timeouts
            max_commits_to_process = 300
            
            # Get commits (sorted newest to oldest)
            commits = self.repo.get_commits()
            
            for i, commit in enumerate(commits):
                if i >= max_commits_to_process:
                    break
                
                if commit.commit.author and commit.commit.author.date:
                    commit_date = commit.commit.author.date
                    commit_dates.append(commit_date)
                    
                    # Track the first and latest commits
                    if latest_commit is None or commit_date > latest_commit:
                        latest_commit = commit_date
                    if first_commit is None or commit_date < first_commit:
                        first_commit = commit_date
                    
                    # Group by year-month for history
                    month_key = f"{commit_date.year}-{commit_date.month:02d}"
                    monthly_commits[month_key] += 1
                
                commit_count += 1
            
            # Calculate commit frequency (commits per week)
            commit_frequency = 0.0
            if first_commit and latest_commit and first_commit != latest_commit:
                # Calculate weeks between first and latest commit
                weeks_diff = (latest_commit - first_commit).days / 7.0
                if weeks_diff > 0:
                    commit_frequency = commit_count / weeks_diff
            
            # Sort monthly commits by date
            sorted_monthly_commits = dict(sorted(
                monthly_commits.items(), 
                key=lambda x: (int(x[0].split('-')[0]), int(x[0].split('-')[1]))
            ))
            
            # Limit to last 12 months if there are many
            if len(sorted_monthly_commits) > 12:
                last_12_months = list(sorted_monthly_commits.items())[-12:]
                sorted_monthly_commits = dict(last_12_months)
            
            return {
                "total_commits": commit_count,
                "first_commit_date": first_commit.isoformat() if first_commit else "",
                "latest_commit_date": latest_commit.isoformat() if latest_commit else "",
                "commit_frequency": round(commit_frequency, 2),
                "commit_history": sorted_monthly_commits
            }
            
        except Exception as e:
            print(f"Error getting repository commit stats: {str(e)}")
            return {
                "total_commits": 0,
                "first_commit_date": "",
                "latest_commit_date": "",
                "commit_frequency": 0.0,
                "commit_history": {}
            }
            
    @with_timeout(20)
    def get_repository_languages(self) -> Dict[str, float]:
        """
        Get repository language breakdown.
        
        Returns:
            Dictionary with language percentages
        """
        if self.repo is None:
            return {}
            
        try:
            # Get languages dict from GitHub API (bytes per language)
            languages_bytes = self.repo.get_languages()
            
            if not languages_bytes:
                return {}
                
            # Calculate total bytes
            total_bytes = sum(languages_bytes.values())
            
            if total_bytes == 0:
                return {}
                
            # Convert to percentages
            languages_percent = {
                lang: round((bytes_count / total_bytes) * 100, 1)
                for lang, bytes_count in languages_bytes.items()
            }
            
            # Sort by percentage (descending)
            sorted_languages = dict(sorted(
                languages_percent.items(), 
                key=lambda x: x[1], 
                reverse=True
            ))
            
            # Limit to top 5 languages
            return dict(list(sorted_languages.items())[:5])
            
        except Exception as e:
            print(f"Error getting repository languages: {str(e)}")
            return {}