"""
GitHub API service for interacting with GitHub repositories.
"""

import logging
import httpx
import re
from typing import List, Dict, Any, Optional, Union
from urllib.parse import urlparse

from app.config import settings

logger = logging.getLogger(__name__)


class GitHubService:
    """Service for interacting with GitHub repositories."""

    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize the GitHub service.

        Args:
            github_token: GitHub Personal Access Token (PAT) for authenticated requests
        """
        self.github_token = github_token or settings.GITHUB_TOKEN
        self.headers = {}
        if self.github_token:
            self.headers["Authorization"] = f"Bearer {self.github_token}"

    async def parse_github_url(self, github_url: str) -> Dict[str, str]:
        """
        Parse a GitHub repository URL to extract owner, repo name, and path.

        Args:
            github_url: GitHub repository URL

        Returns:
            Dict containing owner, repo, and path components

        Raises:
            ValueError: If the URL is not a valid GitHub repository URL
        """
        # Remove trailing slashes
        github_url = github_url.rstrip("/")

        # Parse with URL regex
        github_pattern = r"https?://github\.com/([^/]+)/([^/]+)(?:/tree/[^/]+/(.+))?"
        match = re.match(github_pattern, github_url)

        if not match:
            # Try alternative parsing with urlparse
            parsed_url = urlparse(github_url)
            if parsed_url.netloc == "github.com":
                parts = parsed_url.path.strip("/").split("/")
                if len(parts) >= 2:
                    owner, repo = parts[0], parts[1]
                    path = (
                        "/".join(parts[3:])
                        if len(parts) > 3 and parts[2] == "tree"
                        else ""
                    )
                    return {"owner": owner, "repo": repo, "path": path}

            raise ValueError(f"Invalid GitHub URL: {github_url}")

        owner, repo, path = match.groups()
        return {
            "owner": owner,
            "repo": repo,
            "path": path or "",  # Handle case where path is None
        }

    async def get_repository_contents(
        self, owner: str, repo: str, path: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Get contents of a GitHub repository at a specific path.

        Args:
            owner: Repository owner
            repo: Repository name
            path: Path within the repository (optional)

        Returns:
            List of content items (files and directories)

        Raises:
            HTTPError: If the GitHub API request fails
        """
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, timeout=30.0)
            response.raise_for_status()

            contents = response.json()
            return contents if isinstance(contents, list) else [contents]

    async def get_file_content(
        self, owner: str, repo: str, path: str
    ) -> Dict[str, Any]:
        """
        Get the content of a file in a GitHub repository.

        Args:
            owner: Repository owner
            repo: Repository name
            path: Path to the file within the repository

        Returns:
            Dict containing file content and metadata

        Raises:
            HTTPError: If the GitHub API request fails
        """
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, timeout=30.0)
            response.raise_for_status()

            file_data = response.json()

            # If the content is a file, decode the content
            content = None
            if "content" in file_data and file_data.get("type") == "file":
                import base64

                content = base64.b64decode(file_data["content"]).decode("utf-8")

            # Calculate token estimates
            byte_size = len(content.encode("utf-8")) if content else 0
            token_estimate = self._estimate_tokens(content) if content else 0

            return {
                "name": file_data.get("name", ""),
                "path": file_data.get("path", ""),
                "sha": file_data.get("sha", ""),
                "size": file_data.get("size", byte_size),
                "type": file_data.get("type", ""),
                "content": content,
                "token_estimate": token_estimate,
                "raw_url": file_data.get("download_url", ""),
            }

    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in a text string.
        Uses a simple heuristic of ~4 characters per token for English text.

        Args:
            text: Text content to estimate

        Returns:
            Estimated token count
        """
        if not text:
            return 0

        # Simple heuristic: ~4 characters per token for English text
        return max(1, len(text) // 4)


# Create a singleton instance
github_service = GitHubService()
