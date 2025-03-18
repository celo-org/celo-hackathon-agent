"""
GitHub repository access utilities using Gitingest.
"""

import time
import os
import re
from typing import Dict, List, Tuple, Any, Optional
from gitingest import ingest

from src.models.types import RepoDetails
from src.models.config import Config


class GitHubRepository:
    """Class for interacting with GitHub repositories using Gitingest."""
    
    def __init__(self, config: Config):
        """
        Initialize with configuration.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.repo_owner = None
        self.repo_name = None
        self.code_sample_files = []  # Track filenames of collected code samples
        self.repo_data = None  # Will store repo data from gitingest
        
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
    
    def setup_repository(self, repo_url: str) -> Tuple[str, str]:
        """
        Set up GitHub repository data using Gitingest.
        
        Args:
            repo_url: URL of the GitHub repository
            
        Returns:
            Tuple of repository owner and name
        """
        # Parse GitHub URL to get owner and name
        repo_owner, repo_name = self.parse_github_url(repo_url)
        
        # Store repository info
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        
        try:
            # Use gitingest to get repository content
            print(f"Fetching repository data for {repo_owner}/{repo_name} using Gitingest...")
            summary, tree, content = ingest(repo_url)
            self.repo_data = {
                "summary": summary,
                "tree": tree,
                "content": content
            }
            print(f"Successfully fetched repository data for {repo_owner}/{repo_name}")
        except Exception as e:
            print(f"Error fetching repository with Gitingest: {str(e)}")
            self.repo_data = None
        
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
    
    def get_repository_details(self) -> RepoDetails:
        """
        Get repository details using repository data from Gitingest.
        
        Returns:
            RepoDetails with repository information
        """
        # If we don't have the repo data, return fallback info
        if self.repo_data is None:
            return self.create_fallback_repo_details(
                self.repo_owner, 
                self.repo_name, 
                f"https://github.com/{self.repo_owner}/{self.repo_name}"
            )
        
        try:
            # Extract information from gitingest summary
            summary = self.repo_data["summary"]
            
            # Parse languages from summary
            languages = {}
            language_pattern = r"Language: (.*?) \(([0-9.]+)%\)"
            for language_match in re.finditer(language_pattern, summary):
                if language_match:
                    lang_name = language_match.group(1)
                    lang_percent = float(language_match.group(2))
                    languages[lang_name] = lang_percent
            
            # Try to extract other metrics from summary
            stars = 0
            forks = 0
            open_issues = 0
            
            stars_match = re.search(r"Stars: (\d+)", summary)
            if stars_match:
                stars = int(stars_match.group(1))
                
            forks_match = re.search(r"Forks: (\d+)", summary)
            if forks_match:
                forks = int(forks_match.group(1))
            
            issues_match = re.search(r"Issues: (\d+)", summary)
            if issues_match:
                open_issues = int(issues_match.group(1))
            
            # Initialize with available details
            repo_info = {
                "name": self.repo_name,
                "description": "",  # Not easily available from gitingest
                "url": f"https://github.com/{self.repo_owner}/{self.repo_name}",
                "stars": stars,
                "forks": forks,
                "open_issues": open_issues,
                "last_update": "",
                "language": next(iter(languages.keys()), "") if languages else "",
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
                "main_languages": languages,
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
            
            return repo_info
            
        except Exception as e:
            error_msg = f"Error extracting repository details: {str(e)}"
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
        if self.repo_data is None:
            # Return empty results if no repo data
            return {
                "file_count": 0,
                "test_file_count": 0,
                "doc_file_count": 0,
                "code_files_analyzed": 0
            }, []
        
        # Initialize counters
        file_count = 0
        test_file_count = 0
        doc_file_count = 0
        
        # Code samples for analysis
        code_samples = []
        self.code_sample_files = []  # Clear previous file names
        
        if progress_callback:
            progress_callback("Analyzing repository structure...")
        
        try:
            # Extract file tree from gitingest data
            tree = self.repo_data["tree"]
            content = self.repo_data["content"]
            
            # Process all files mentioned in the tree
            file_paths = []
            for line in tree.split('\n'):
                # Look for file entries in the tree
                if line and not line.endswith('/'):
                    file_path = line.strip()
                    file_paths.append(file_path)
                    file_count += 1
                    
                    # Classify file types
                    if "test" in file_path.lower() or "spec" in file_path.lower():
                        test_file_count += 1
                        
                    if file_path.lower().endswith((".md", ".rst", ".txt", ".doc", ".docx")):
                        doc_file_count += 1
            
            if progress_callback:
                progress_callback(f"Found {file_count} files, extracting code samples...")
            
            # Extract code samples from the content
            file_pattern = r"```\s*(\S+)\s*\n(.*?)```"
            file_blocks = re.finditer(file_pattern, content, re.DOTALL)
            
            for i, match in enumerate(file_blocks):
                if progress_callback and i % 5 == 0:
                    progress_callback(f"Processed {i} code samples...")
                
                file_path = match.group(1)
                file_content = match.group(2)
                
                # Skip very small files
                if len(file_content.strip()) < 50:
                    continue
                
                # Collect the code sample
                code_samples.append(f"File: {file_path}\n\n{file_content}\n\n")
                self.code_sample_files.append(file_path)
            
            # Compile file metrics
            file_metrics = {
                "file_count": file_count,
                "test_file_count": test_file_count,
                "doc_file_count": doc_file_count,
                "code_files_analyzed": len(code_samples)
            }
            
            # Final progress update
            if progress_callback:
                progress_callback(f"Completed collecting {len(code_samples)} code samples from {file_count} files")
            
            return file_metrics, code_samples
            
        except Exception as e:
            print(f"Error collecting code samples: {str(e)}")
            
            # Return empty results on error
            if progress_callback:
                progress_callback(f"Error collecting code samples: {str(e)}")
                
            return {
                "file_count": 0,
                "test_file_count": 0,
                "doc_file_count": 0,
                "code_files_analyzed": 0
            }, []
    
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
        
        if self.repo_data is None:
            return evidence
        
        content = self.repo_data["content"]
        
        for file_path in file_paths:
            # Try to find the file content in the repository data
            file_pattern = f"```\\s*{re.escape(file_path)}\\s*\\n(.*?)```"
            file_match = re.search(file_pattern, content, re.DOTALL)
            
            if file_match:
                file_content = file_match.group(1)
                for keyword in keywords:
                    if keyword.lower() in file_content.lower():
                        evidence.append({
                            "file": file_path,
                            "keyword": keyword
                        })
        
        return evidence