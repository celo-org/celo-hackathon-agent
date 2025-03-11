"""
GitHub repository access utilities using gitingest.
"""

import time
import re
from typing import Dict, List, Tuple, Any, Optional

from gitingest import ingest
from src.models.types import RepoDetails
from src.models.config import Config
from src.utils.timeout import GitHubAccessError, with_timeout


class GitHubRepository:
    """Class for interacting with GitHub repositories using gitingest."""
    
    def __init__(self, config: Config):
        """
        Initialize with configuration.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.repo_data = None
        self.repo_owner = None
        self.repo_name = None
        self.summary = None
        self.tree = None 
        self.content = None
    
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
        Set up repository connection using gitingest.
        
        Args:
            repo_url: URL of the GitHub repository
            
        Returns:
            Tuple of repository owner and name
        """
        # Parse GitHub URL to get owner and name
        repo_owner, repo_name = self.parse_github_url(repo_url)
        
        try:
            # Use gitingest to get repository data
            if progress_callback := getattr(self, 'progress_callback', None):
                progress_callback(f"Using gitingest to analyze repository {repo_owner}/{repo_name}")
            
            # Call gitingest to get repository data
            self.summary, self.tree, self.content = ingest(repo_url)
            self.repo_data = {
                "summary": self.summary,
                "tree": self.tree,
                "content": self.content
            }
            
        except Exception as e:
            error_msg = f"Error accessing repository {repo_owner}/{repo_name}: {str(e)}"
            print(error_msg)
            self.repo_data = None
        
        # Store repository info
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
            "language": ""
        }
    
    @with_timeout(30)
    def get_repository_details(self) -> RepoDetails:
        """
        Get repository details using the gitingest summary data.
        
        Returns:
            RepoDetails with repository information
        """
        # If we don't have the repo data, return fallback info
        if not self.repo_data or not self.summary:
            return self.create_fallback_repo_details(
                self.repo_owner, 
                self.repo_name, 
                f"https://github.com/{self.repo_owner}/{self.repo_name}"
            )
        
        try:
            # Extract repository information from gitingest summary
            # Parse languages from summary
            language_match = re.search(r"Most used language: ([A-Za-z\+\#]+)", self.summary)
            main_language = language_match.group(1) if language_match else ""
            
            # Get file counts
            file_count_match = re.search(r"Files: (\d+)", self.summary)
            file_count = int(file_count_match.group(1)) if file_count_match else 0
            
            # Try to extract more information if available
            stars_match = re.search(r"Stars: (\d+)", self.summary)
            stars = int(stars_match.group(1)) if stars_match else 0
            
            forks_match = re.search(r"Forks: (\d+)", self.summary)
            forks = int(forks_match.group(1)) if forks_match else 0
            
            # Create repository details object
            repo_info = {
                "name": self.repo_name,
                "description": self.summary.split("\n")[0] if self.summary else f"Repository for {self.repo_owner}/{self.repo_name}",
                "url": f"https://github.com/{self.repo_owner}/{self.repo_name}",
                "stars": stars,
                "forks": forks,
                "open_issues": 0,  # Not available from gitingest
                "last_update": "",  # Not available from gitingest
                "language": main_language
            }
            
            return repo_info
            
        except Exception as e:
            error_msg = f"Error getting repository details: {str(e)}"
            print(error_msg)
            raise GitHubAccessError(error_msg)
    
    def collect_code_samples(self, progress_callback=None) -> Tuple[Dict[str, int], List[str]]:
        """
        Collect code samples and file metrics from repository using gitingest.
        
        Args:
            progress_callback: Optional callback for progress updates
            
        Returns:
            Tuple of file metrics and code samples
        """
        # Store progress callback for future use
        self.progress_callback = progress_callback
        
        # Initialize counters
        file_count = 0
        test_file_count = 0
        doc_file_count = 0
        code_files_count = 0
        
        # Code samples for analysis
        code_samples = []
        
        if not self.repo_data or not self.content:
            if progress_callback:
                progress_callback("No repository data available. Unable to collect code samples.")
            return {
                "file_count": 0,
                "test_file_count": 0,
                "doc_file_count": 0,
                "code_files_analyzed": 0
            }, []
        
        if progress_callback:
            progress_callback("Processing repository data from gitingest...")
        
        start_time = time.time()
        
        # Process the content from gitingest to extract code samples
        content_sections = self.content.split("```")
        
        # If we have an odd number of sections, we have code blocks
        # The pattern is: text, code, text, code, ...
        if len(content_sections) > 1:
            # Extract file information and content from every other section (1, 3, 5, ...)
            for i in range(1, min(21, len(content_sections)), 2):  # Limit to 10 code sections (up to 21 sections)
                if i < len(content_sections):
                    section = content_sections[i]
                    lines = section.strip().split("\n")
                    
                    # First line might be the file type/name
                    if lines and ":" in lines[0]:
                        file_path = lines[0].split(":", 1)[1].strip()
                        file_content = "\n".join(lines[1:])
                    else:
                        # If no clear file path, use a generic name with index
                        file_path = f"file_{i//2}.txt"
                        file_content = "\n".join(lines)
                    
                    # Update counts based on file type
                    file_count += 1
                    
                    if "test" in file_path.lower() or "spec" in file_path.lower():
                        test_file_count += 1
                        
                    if file_path.lower().endswith((".md", ".rst", ".txt", ".doc", ".docx")):
                        doc_file_count += 1
                    
                    # Detect code files by common extensions
                    code_extensions = (".js", ".ts", ".jsx", ".tsx", ".py", ".java", ".sol", 
                                     ".go", ".rb", ".php", ".c", ".cpp", ".cs")
                    if any(file_path.lower().endswith(ext) for ext in code_extensions):
                        code_files_count += 1
                        
                        # Limit sample size
                        sample = file_content[:1000] + "..." if len(file_content) > 1000 else file_content
                        code_samples.append(f"File: {file_path}\n\n{sample}\n\n")
                        
                        if progress_callback and len(code_samples) % 3 == 0:
                            progress_callback(f"Collected {len(code_samples)} code samples...")
        else:
            # If no code blocks found, try to parse the content differently
            # Look for file sections in the raw content
            if progress_callback:
                progress_callback("No code blocks found. Parsing content for file sections...")
            
            file_sections = re.findall(r'([-\w./]+\.\w+)[\s\n]+(.+?)(?=[-\w./]+\.\w+|\Z)', self.content, re.DOTALL)
            
            for file_path, file_content in file_sections[:10]:  # Limit to 10 samples
                file_path = file_path.strip()
                file_content = file_content.strip()
                
                # Update counts
                file_count += 1
                
                if "test" in file_path.lower() or "spec" in file_path.lower():
                    test_file_count += 1
                    
                if file_path.lower().endswith((".md", ".rst", ".txt", ".doc", ".docx")):
                    doc_file_count += 1
                
                # Detect code files
                code_extensions = (".js", ".ts", ".jsx", ".tsx", ".py", ".java", ".sol", 
                                 ".go", ".rb", ".php", ".c", ".cpp", ".cs")
                if any(file_path.lower().endswith(ext) for ext in code_extensions):
                    code_files_count += 1
                    
                    # Limit sample size
                    sample = file_content[:1000] + "..." if len(file_content) > 1000 else file_content
                    code_samples.append(f"File: {file_path}\n\n{sample}\n\n")
                    
                    if progress_callback and len(code_samples) % 3 == 0:
                        progress_callback(f"Collected {len(code_samples)} code samples...")
        
        # If we still don't have enough code samples, extract them from the tree structure
        if len(code_samples) < 5 and self.tree:
            if progress_callback:
                progress_callback("Finding additional code samples from directory tree...")
            
            # Extract file paths from the tree
            file_paths = []
            for line in self.tree.split("\n"):
                if line.strip() and not line.strip().endswith("/"):
                    file_path = line.strip()
                    file_paths.append(file_path)
                    
                    # Update file counter
                    file_count += 1
                    
                    # Classify file type
                    if "test" in file_path.lower() or "spec" in file_path.lower():
                        test_file_count += 1
                        
                    if file_path.lower().endswith((".md", ".rst", ".txt", ".doc", ".docx")):
                        doc_file_count += 1
                    
                    # Check for code files
                    code_extensions = (".js", ".ts", ".jsx", ".tsx", ".py", ".java", ".sol", 
                                     ".go", ".rb", ".php", ".c", ".cpp", ".cs")
                    if any(file_path.lower().endswith(ext) for ext in code_extensions):
                        code_files_count += 1
        
        # Compile file metrics
        file_metrics = {
            "file_count": file_count,
            "test_file_count": test_file_count,
            "doc_file_count": doc_file_count,
            "code_files_analyzed": code_files_count
        }
        
        # Add some synthetic samples if we couldn't find any
        if not code_samples and self.summary:
            code_samples.append(f"Repository Summary:\n\n{self.summary}\n\n")
            if self.tree:
                code_samples.append(f"Repository Structure:\n\n{self.tree[:1000]}\n\n")
        
        # Final progress update
        if progress_callback:
            elapsed = time.time() - start_time
            progress_callback(f"Completed collecting {len(code_samples)} code samples in {elapsed:.1f}s")
        
        return file_metrics, code_samples
        
    def search_files_for_keywords(self, file_paths: List[str], keywords: List[str]) -> List[Dict[str, str]]:
        """
        Search repository content for keywords.
        
        Args:
            file_paths: List of file paths to search (not used, searching all content)
            keywords: List of keywords to search for
            
        Returns:
            List of evidence dictionaries
        """
        evidence = []
        
        if not self.repo_data or not self.content:
            return evidence
        
        # Search for keywords in the entire content
        content_lower = self.content.lower()
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in content_lower:
                # Try to find a file context for the keyword
                # Look for the keyword in context of a file mention
                pattern = r'([-\w./]+\.\w+)[\s\n]+[^/]*({})[^/]*'.format(re.escape(keyword_lower))
                matches = re.finditer(pattern, content_lower, re.IGNORECASE)
                
                # Add each match as evidence
                found = False
                for match in matches:
                    file_path = match.group(1)
                    evidence.append({
                        "file": file_path,
                        "keyword": keyword
                    })
                    found = True
                
                # If no file context found, add generic evidence
                if not found:
                    evidence.append({
                        "file": "repository_content",
                        "keyword": keyword
                    })
                
        return evidence