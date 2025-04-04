"""
Repository fetching module for the AI Project Analyzer.

This module handles fetching and processing GitHub repositories using gitingest.
It also fetches GitHub metrics using the GitHub API.
"""

import logging
from typing import Dict, List, Any, Optional
from gitingest import ingest
from src.metrics import fetch_github_metrics

logger = logging.getLogger(__name__)

# Define exclusion patterns for repositories
EXCLUDE_PATTERNS = [
    "node_modules",
    ".git",
    "__pycache__",
    "*.lock",
    "*.min.js",
    "*.min.css",
    "package-lock.json",
    "pnpm-lock.yaml",
    "**/pnpm-lock.yaml",
    "**/package-lock.json",
    "**/jsdoc-automation/*",
    "bun.lock",
    "**/bun.lock",
    "yarn.lock",
    "**/yarn.lock",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "dist",
    "build",
    ".cache",
    ".env",
    "*.png",
    "*.jpg",
    "*.jpeg",
    "*.gif",
    "*.svg",
    "*.ico",
    "*.webp",
    "*.heic",
    "*.heif",
    "*.hevc",
    "**/build-info/*",
    "**/solcInputs/*",
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
                return f"{parts[github_index + 1]}/{parts[github_index + 2]}"

    # If we can't parse it, just return the URL as a fallback
    return url.replace("https://", "").replace("http://", "").replace("/", "_")


def fetch_repositories(
    repo_urls: List[str], include_metrics: bool = True, github_token: Optional[str] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Fetch multiple repositories and return their code digests and metrics.

    Args:
        repo_urls: List of repository URLs to fetch
        include_metrics: Whether to include GitHub metrics (default: True)
        github_token: GitHub API token for fetching metrics (optional)

    Returns:
        Dict[str, Dict[str, Any]]: Dictionary mapping repository names to their data
    """
    results = {}
    exclude_patterns_set = set(EXCLUDE_PATTERNS)
    normalized_urls = [normalize_repo_url(url) for url in repo_urls]

    # Fetch code content
    for url in normalized_urls:
        repo_name = get_repo_name(url)

        logger.info(f"Fetching repository content: {repo_name} ({url})")

        try:
            # Use gitingest to fetch the repository content
            summary, tree, content = ingest(url, exclude_patterns=exclude_patterns_set)

            # Log summary information
            logger.info(f"Successfully fetched {repo_name} content")
            logger.debug(f"Repository summary: {len(content)} characters")

            # Store the content in our results dictionary
            results[repo_name] = {"content": content, "metrics": {}}

        except Exception as e:
            logger.error(f"Error fetching repository {repo_name} content: {str(e)}")
            # Create an entry even if content fetch fails
            results[repo_name] = {"content": f"Error fetching repository: {str(e)}", "metrics": {}}

    # Fetch GitHub metrics if requested
    if include_metrics:
        logger.info("Fetching GitHub metrics for repositories...")
        try:
            metrics_data = fetch_github_metrics(normalized_urls, github_token)

            # Add metrics to results
            for repo_name, metrics in metrics_data.items():
                if repo_name in results:
                    results[repo_name]["metrics"] = metrics
                    logger.info(f"Added metrics for {repo_name}")
                else:
                    # This should rarely happen, but handle the case where a repo name mismatch occurs
                    # Find the most likely match
                    for result_name in results.keys():
                        if (
                            repo_name.lower() in result_name.lower()
                            or result_name.lower() in repo_name.lower()
                        ):
                            results[result_name]["metrics"] = metrics
                            logger.info(
                                f"Added metrics for {result_name} (matched from {repo_name})"
                            )
                            break
        except Exception as e:
            logger.error(f"Error fetching metrics: {str(e)}")

    logger.info(f"Fetched data for {len(results)} repositories successfully")
    return results
