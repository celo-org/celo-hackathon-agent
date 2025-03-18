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
from src.utils.logger import logger


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

        # Define patterns to exclude from the repository
        exclude_patterns = [
            "node_modules",
            ".git",
            "__pycache__",
            "*.lock",
            "*.min.js",
            "*.min.css",
            "package-lock.json",
            "yarn.lock",
            "dist",
            "build",
            ".cache",
            ".env",
        ]

        try:
            # Use gitingest to get repository content
            start_time = time.time()
            logger.debug(f"Fetching repository data for {repo_owner}/{repo_name}")

            # Convert list to set before passing to ingest
            exclude_patterns_set = set(exclude_patterns)
            summary, tree, content = ingest(
                repo_url, exclude_patterns=exclude_patterns_set
            )

            logger.debug(f"Summary length: {len(summary) if summary else 0} chars")
            logger.debug(f"Tree data length: {len(tree) if tree else 0} chars")
            logger.debug(f"Content data length: {len(content) if content else 0} chars")
            
            # Log beginning and end of content for debugging
            if content:
                logger.debug(f"Content starts with: {content[:100]}...")
                logger.debug(f"Content ends with: ...{content[-100:]}")
            
            # If content is empty but tree has data, add dummy content
            if not content and tree:
                logger.warn("Empty content but tree data exists. Creating placeholder content.")
                content = f"```bash\ngit clone {repo_url}\n```"

            self.repo_data = {"summary": summary, "tree": tree, "content": content}
            elapsed = time.time() - start_time
            logger.debug(f"Fetched repository data for {repo_owner}/{repo_name} in {elapsed:.1f}s")

        except Exception as e:
            logger.error(f"Error fetching repository with Gitingest: {str(e)}")
            self.repo_data = None

        return repo_owner, repo_name

    def create_fallback_repo_details(
        self, repo_owner: str, repo_name: str, repo_url: str
    ) -> RepoDetails:
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
                "commit_history": {},
            },
            "main_languages": {},
            "license_type": None,
            "created_at": "",
            "size_kb": 0,
            "repo_type": None,
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
                f"https://github.com/{self.repo_owner}/{self.repo_name}",
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

            # Attempt to determine repository type based on languages and files
            repo_type = self._determine_repo_type(languages, self.repo_data["tree"])

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
                    "commit_history": {},
                },
                "main_languages": languages,
                "license_type": None,
                "created_at": "",
                "size_kb": 0,
                "repo_type": repo_type,
            }

            return repo_info

        except Exception as e:
            error_msg = f"Error extracting repository details: {str(e)}"
            print(error_msg)
            return self.create_fallback_repo_details(
                self.repo_owner,
                self.repo_name,
                f"https://github.com/{self.repo_owner}/{self.repo_name}",
            )

    def _determine_repo_type(self, languages: Dict[str, float], file_tree: str) -> str:
        """
        Determine repository type based on languages and files.

        Args:
            languages: Dictionary of languages and their percentages
            file_tree: String representation of repository file tree

        Returns:
            Repository type string
        """
        # Default to unknown
        repo_type = "unknown"

        # Check for common smart contract indicators
        if any(
            f in file_tree.lower()
            for f in ["truffle", "hardhat", "contracts/", "solidity", ".sol"]
        ):
            repo_type = "smart contract"

        # Check for web application indicators
        elif any(
            f in file_tree.lower()
            for f in ["index.html", "app.js", "webpack", "package.json", "public/"]
        ) and any(
            lang in languages for lang in ["JavaScript", "TypeScript", "HTML", "CSS"]
        ):
            repo_type = "web application"

        # Check for mobile app indicators
        elif (
            any(
                f in file_tree.lower()
                for f in [
                    "androidmanifest.xml",
                    "appdelegate.swift",
                    "app/build.gradle",
                ]
            )
            or "Kotlin" in languages
            or "Swift" in languages
        ):
            repo_type = "mobile application"

        # Check for backend/API indicators
        elif any(
            f in file_tree.lower()
            for f in ["controllers/", "routes/", "api/", "endpoints"]
        ):
            repo_type = "backend/api"

        # Check for library indicators
        elif "lib/" in file_tree.lower() or "/src/" in file_tree.lower():
            repo_type = "library/package"

        return repo_type

    def collect_code_samples(
        self, progress_callback=None
    ) -> Tuple[Dict[str, int], List[str]]:
        """
        Collect code samples and file metrics from repository.

        Args:
            progress_callback: Optional callback for progress updates

        Returns:
            Tuple of file metrics and code samples
        """
        if self.repo_data is None:
            # Return empty results if no repo data
            logger.warn("No repository data available for code sample collection")
            return {
                "file_count": 0,
                "test_file_count": 0,
                "doc_file_count": 0,
                "code_files_analyzed": 0,
            }, []

        # Initialize counters
        file_count = 0
        test_file_count = 0
        doc_file_count = 0

        # Code samples for analysis
        code_samples = []
        self.code_sample_files = []  # Clear previous file names

        if progress_callback:
            progress_callback("Analyzing repository structure")

        try:
            start_time = time.time()
            # Extract file tree from gitingest data
            tree = self.repo_data["tree"]
            content = self.repo_data["content"]

            # Process all files mentioned in the tree
            file_paths = []
            for line in tree.split("\n"):
                # Look for file entries in the tree
                if line and not line.endswith("/"):
                    file_path = line.strip()
                    file_paths.append(file_path)
                    file_count += 1

                    # Classify file types
                    if "test" in file_path.lower() or "spec" in file_path.lower():
                        test_file_count += 1

                    if file_path.lower().endswith(
                        (".md", ".rst", ".txt", ".doc", ".docx")
                    ):
                        doc_file_count += 1

            if progress_callback:
                progress_callback(f"Extracting code samples from {file_count} files")

            # Debug the content
            logger.debug(f"Content length: {len(content)}")
            logger.debug(f"Content first 100 chars: {content[:100]}")
            
            # Extract code samples from the content using both patterns
            # Pattern 1: Markdown triple backtick
            file_pattern1 = r"```\s*(\S+)\s*\n(.*?)```"
            # Pattern 2: Equal sign pattern from gitingest
            file_pattern2 = r"={10,}\nFile: (\S+)\n={10,}\n(.*?)(?=\n={10,}\nFile:|\Z)"
            
            # Try both patterns
            file_blocks1 = list(re.finditer(file_pattern1, content, re.DOTALL))
            file_blocks2 = list(re.finditer(file_pattern2, content, re.DOTALL))
            
            logger.debug(f"Found {len(file_blocks1)} markdown blocks and {len(file_blocks2)} gitingest blocks in content")
            
            # Combine results from both patterns
            file_blocks = file_blocks1.copy()
            
            # Add gitingest pattern matches
            for match in file_blocks2:
                file_blocks.append(match)
                
            logger.debug(f"Total file blocks found: {len(file_blocks)}")
            
            # If no file blocks found with markdown syntax, try extracting directly from structure
            if len(file_blocks) == 0:
                logger.warn("No file blocks found with markdown syntax. Attempting direct extraction.")
                # Try to extract files from tree structure
                file_paths = []
                for line in tree.split('\n'):
                    if line and not line.endswith('/'):
                        file_path = line.strip()
                        file_paths.append(file_path)
                
                # Take top 10 files for analysis if tree has files but no code blocks found
                if file_paths:
                    logger.debug(f"Found {len(file_paths)} files in tree structure. Using top 10.")
                    for file_path in file_paths[:10]:
                        code_samples.append(f"File: {file_path}\n\nNo content available\n\n")
                        self.code_sample_files.append(file_path)
                    
                    # Add a sample command if no real files found to avoid completely empty analysis
                    if not code_samples:
                        repo_url = f"https://github.com/{self.repo_owner}/{self.repo_name}"
                        code_samples.append(f"File: bash\n\ngit clone {repo_url}\n\n")
                        self.code_sample_files.append("bash")

            # Process all file blocks - no limits since we're using modern LLMs with large context
            for i, match in enumerate(file_blocks):
                file_path = match.group(1)
                file_content = match.group(2)
                
                logger.debug(f"Processing file block {i+1}: {file_path} - content length: {len(file_content)}")

                # Include all files regardless of size
                logger.debug(f"Including file: {file_path} - size: {len(file_content.strip())} chars")
                
                # No size limits - use full file content
                
                # Collect the code sample
                code_samples.append(f"File: {file_path}\n\n{file_content}\n\n")
                self.code_sample_files.append(file_path)
                
                if progress_callback and i % 10 == 0:  # update every 10 files
                    progress_callback(f"Processed {i+1}/{len(file_blocks)} files")
            
            # If no code samples found, add a placeholder
            if not code_samples:
                logger.warn("No code samples collected. Adding placeholder.")
                repo_url = f"https://github.com/{self.repo_owner}/{self.repo_name}"
                code_samples.append(f"File: bash\n\ngit clone {repo_url}\n\n")
                self.code_sample_files.append("bash")

            # Compile file metrics
            file_metrics = {
                "file_count": file_count,
                "test_file_count": test_file_count,
                "doc_file_count": doc_file_count,
                "code_files_analyzed": len(code_samples),
            }

            # Final progress update
            elapsed = time.time() - start_time
            if progress_callback:
                progress_callback(
                    f"Collected {len(code_samples)} code samples from {file_count} files"
                )
                
            logger.debug(f"Code sample collection completed in {elapsed:.2f}s")

            return file_metrics, code_samples

        except Exception as e:
            logger.error(f"Error collecting code samples: {str(e)}")

            # Return empty results on error
            if progress_callback:
                progress_callback(f"Error collecting code samples: {str(e)}")

            return {
                "file_count": 0,
                "test_file_count": 0,
                "doc_file_count": 0,
                "code_files_analyzed": 0,
            }, []

    def search_files_for_keywords(
        self, file_paths: List[str], keywords: List[str]
    ) -> List[Dict[str, str]]:
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
                        evidence.append({"file": file_path, "keyword": keyword})

        return evidence
