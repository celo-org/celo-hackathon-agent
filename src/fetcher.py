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
    # Python
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "__pycache__",
    ".pytest_cache",
    ".coverage",
    ".tox",
    ".nox",
    ".mypy_cache",
    ".ruff_cache",
    ".hypothesis",
    "poetry.lock",
    "Pipfile.lock",
    # JavaScript/FileSystemNode
    "node_modules",
    "bower_components",
    "package-lock.json",
    "yarn.lock",
    ".npm",
    ".yarn",
    ".pnpm-store",
    "bun.lock",
    "bun.lockb",
    # Java
    "*.class",
    "*.jar",
    "*.war",
    "*.ear",
    "*.nar",
    ".gradle/",
    "build/",
    ".settings/",
    ".classpath",
    "gradle-app.setting",
    "*.gradle",
    # IDEs and editors / Java
    ".project",
    # C/C++
    "*.o",
    "*.obj",
    "*.dll",
    "*.dylib",
    "*.exe",
    "*.lib",
    "*.out",
    "*.a",
    "*.pdb",
    # Swift/Xcode
    ".build/",
    "*.xcodeproj/",
    "*.xcworkspace/",
    "*.pbxuser",
    "*.mode1v3",
    "*.mode2v3",
    "*.perspectivev3",
    "*.xcuserstate",
    "xcuserdata/",
    ".swiftpm/",
    # Ruby
    "*.gem",
    ".bundle/",
    "vendor/bundle",
    "Gemfile.lock",
    ".ruby-version",
    ".ruby-gemset",
    ".rvmrc",
    # Rust
    "Cargo.lock",
    "**/*.rs.bk",
    # Java / Rust
    "target/",
    # Go
    "pkg/",
    # .NET/C#
    "obj/",
    "*.suo",
    "*.user",
    "*.userosscache",
    "*.sln.docstates",
    "packages/",
    "*.nupkg",
    # Go / .NET / C#
    "bin/",
    # Version control
    ".git",
    ".svn",
    ".hg",
    ".gitignore",
    ".gitattributes",
    ".gitmodules",
    # Images and media
    "*.svg",
    "*.png",
    "*.jpg",
    "*.jpeg",
    "*.gif",
    "*.ico",
    "*.pdf",
    "*.mov",
    "*.mp4",
    "*.mp3",
    "*.wav",
    # Virtual environments
    "venv",
    ".venv",
    "env",
    ".env",
    "virtualenv",
    # IDEs and editors
    ".idea",
    ".vscode",
    ".vs",
    "*.swo",
    "*.swn",
    ".settings",
    "*.sublime-*",
    # Temporary and cache files
    "*.log",
    "*.bak",
    "*.swp",
    "*.tmp",
    "*.temp",
    ".cache",
    ".sass-cache",
    ".eslintcache",
    ".DS_Store",
    "Thumbs.db",
    "desktop.ini",
    # Build directories and artifacts
    "build",
    "dist",
    "target",
    "out",
    "*.egg-info",
    "*.egg",
    "*.whl",
    "*.so",
    # Documentation
    "site-packages",
    ".docusaurus",
    ".next",
    ".nuxt",
    # Other common patterns
    ## Minified files
    "*.min.js",
    "*.min.css",
    ## Source maps
    "*.map",
    ## Terraform
    ".terraform",
    "*.tfstate*",
    ## Dependencies in various languages
    "vendor/",
    # Gitingest
    "digest.txt",
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


def fetch_single_repository(
    repo_url: str, include_metrics: bool = True, github_token: Optional[str] = None
) -> tuple[str, Dict[str, Any]]:
    """
    Fetch a single repository and return its code digest and metrics.

    Args:
        repo_url: Repository URL to fetch
        include_metrics: Whether to include GitHub metrics (default: True)
        github_token: GitHub API token for fetching metrics (optional)

    Returns:
        tuple[str, Dict[str, Any]]: Repository name and dictionary with content and metrics
    """
    exclude_patterns_set = set(EXCLUDE_PATTERNS)
    normalized_url = normalize_repo_url(repo_url)
    repo_name = get_repo_name(normalized_url)
    result = {"content": "", "metrics": {}}

    logger.info(f"Fetching repository content: {repo_name} ({normalized_url})")

    try:
        # Use gitingest to fetch the repository content
        summary, tree, content = ingest(
            normalized_url, exclude_patterns=exclude_patterns_set
        )

        # Log summary information
        logger.info(f"Successfully fetched {repo_name} content")
        logger.debug(f"Repository summary: {len(content)} characters")

        # Store the content in our results dictionary
        result["content"] = content

    except Exception as e:
        logger.error(f"Error fetching repository {repo_name} content: {str(e)}")
        # Include the error in content
        result["content"] = f"Error fetching repository: {str(e)}"

    # Fetch GitHub metrics if requested
    if include_metrics:
        logger.info(f"Fetching GitHub metrics for repository: {repo_name}")
        try:
            metrics_data = fetch_github_metrics([normalized_url], github_token)

            # Add metrics to result
            if repo_name in metrics_data:
                result["metrics"] = metrics_data[repo_name]
                logger.info(f"Added metrics for {repo_name}")
            else:
                # Look for potential repo name mismatches
                for metrics_repo_name, metrics in metrics_data.items():
                    if (
                        repo_name.lower() in metrics_repo_name.lower()
                        or metrics_repo_name.lower() in repo_name.lower()
                    ):
                        result["metrics"] = metrics
                        logger.info(
                            f"Added metrics for {repo_name} (matched from {metrics_repo_name})"
                        )
                        break
        except Exception as e:
            logger.error(f"Error fetching metrics for {repo_name}: {str(e)}")

    return repo_name, result


def fetch_repositories(
    repo_urls: List[str],
    include_metrics: bool = True,
    github_token: Optional[str] = None,
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

    # Process each repository individually
    for url in repo_urls:
        repo_name, repo_data = fetch_single_repository(
            url, include_metrics, github_token
        )
        results[repo_name] = repo_data

    logger.info(f"Fetched data for {len(results)} repositories successfully")
    return results
