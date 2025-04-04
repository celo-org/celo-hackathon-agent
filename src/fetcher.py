"""
Repository fetching module for the AI Project Analyzer.

This module handles fetching and processing GitHub repositories using gitingest.
"""
import logging
import os
from typing import Dict, List, Set, Tuple
from gitingest import ingest
import tempfile

logger = logging.getLogger(__name__)

# Define exclusion patterns for repositories
EXCLUDE_PATTERNS = [
    "node_modules", ".git", "__pycache__",
    "*.lock", "*.min.js", "*.min.css",
    "package-lock.json", "pnpm-lock.yaml",
    "**/pnpm-lock.yaml", "**/package-lock.json",
    "**/jsdoc-automation/*", "bun.lock", "**/bun.lock",
    "yarn.lock", "**/yarn.lock", "CHANGELOG.md",
    "CONTRIBUTING.md", "dist", "build", ".cache", ".env",
    "*.png", "*.jpg", "*.jpeg", "*.gif", "*.svg", "*.ico",
    "*.webp", "*.heic", "*.heif", "*.hevc",
    "**/build-info/*", "**/solcInputs/*",
]


def normalize_repo_url(url: str) -> str:
    """
    Normalize a repository URL to ensure it's in the correct format.
    
    Args:
        url: The repository URL to normalize
        
    Returns:
        str: The normalized URL
    """
    # Strip whitespace
    url = url.strip()
    
    # If URL doesn't start with http/https, assume it's a GitHub repository
    if not url.startswith(("http://", "https://")):
        # If it's a GitHub shorthand (username/repo), convert to full URL
        if "/" in url and not url.startswith("github.com"):
            url = f"https://github.com/{url}"
        else:
            url = f"https://{url}"
    
    # Remove trailing slashes
    url = url.rstrip("/")
    
    logger.debug(f"Normalized URL: {url}")
    return url


def get_repo_name(url: str) -> str:
    """
    Extract the repository name from a URL.
    
    Args:
        url: The repository URL
        
    Returns:
        str: The repository name (org/repo format)
    """
    # Handle GitHub URLs
    if "github.com" in url:
        # Extract org/repo part from URL
        parts = url.replace("https://", "").replace("http://", "").split("/")
        if "github.com" in parts:
            github_index = parts.index("github.com")
            if len(parts) > github_index + 2:
                return f"{parts[github_index+1]}/{parts[github_index+2]}"
    
    # If we can't parse it, just return the URL as a fallback
    return url.replace("https://", "").replace("http://", "").replace("/", "_")


def fetch_repositories(repo_urls: List[str]) -> Dict[str, str]:
    """
    Fetch multiple repositories and return their code digests.
    
    Args:
        repo_urls: List of repository URLs to fetch
        
    Returns:
        Dict[str, str]: Dictionary mapping repository names to their code digests
    """
    results = {}
    exclude_patterns_set = set(EXCLUDE_PATTERNS)
    
    for url in repo_urls:
        repo_url = normalize_repo_url(url)
        repo_name = get_repo_name(repo_url)
        
        logger.info(f"Fetching repository: {repo_name} ({repo_url})")
        
        try:
            # Use gitingest to fetch the repository content
            summary, tree, content = ingest(
                repo_url, exclude_patterns=exclude_patterns_set
            )
            
            # Log summary information
            logger.info(f"Successfully fetched {repo_name}")
            logger.debug(f"Repository summary: {len(content)} characters")
            
            # Store the content in our results dictionary
            results[repo_name] = content
            
        except Exception as e:
            logger.error(f"Error fetching repository {repo_name}: {str(e)}")
            # Continue with other repositories even if one fails
    
    logger.info(f"Fetched {len(results)} repositories successfully")
    return results