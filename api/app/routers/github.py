"""
GitHub API router for interacting with GitHub repositories.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional

from app.services.github import github_service
from app.schemas.github import (
    GitHubUrlRequest,
    GitHubContentsResponse,
    GitHubFileRequest,
    GitHubFileResponse,
    TokenCalculationRequest,
    TokenCalculationResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/parse-url", response_model=Dict[str, str])
async def parse_github_url(request: GitHubUrlRequest):
    """
    Parse a GitHub repository URL to extract owner, repo name, and path.
    """
    try:
        url_components = await github_service.parse_github_url(str(request.url))
        return url_components
    except ValueError as e:
        logger.error(f"Error parsing GitHub URL: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error parsing GitHub URL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.get("/contents", response_model=GitHubContentsResponse)
async def get_repository_contents(
    owner: str = Query(..., description="Repository owner"),
    repo: str = Query(..., description="Repository name"),
    path: str = Query("", description="Path within the repository"),
):
    """
    Get contents of a GitHub repository at a specific path.
    """
    try:
        contents = await github_service.get_repository_contents(owner, repo, path)

        # Add token estimates to file entries
        for item in contents:
            if item.get("type") == "file":
                item["token_estimate"] = github_service._estimate_tokens(
                    ""
                )  # Placeholder, will be calculated when file is accessed

        return {
            "owner": owner,
            "repo": repo,
            "path": path,
            "contents": contents,
        }
    except Exception as e:
        logger.exception(f"Error getting repository contents: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error getting repository contents: {str(e)}"
        )


@router.get("/file-content", response_model=GitHubFileResponse)
async def get_file_content(
    owner: str = Query(..., description="Repository owner"),
    repo: str = Query(..., description="Repository name"),
    path: str = Query(..., description="Path to the file within the repository"),
):
    """
    Get the content of a file in a GitHub repository.
    """
    try:
        file_data = await github_service.get_file_content(owner, repo, path)
        return file_data
    except Exception as e:
        logger.exception(f"Error getting file content: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error getting file content: {str(e)}"
        )


@router.post("/calculate-tokens", response_model=TokenCalculationResponse)
async def calculate_tokens(request: TokenCalculationRequest):
    """
    Calculate the number of tokens in a text string.
    """
    try:
        content = request.content
        content_length = len(content)
        byte_size = len(content.encode("utf-8"))
        token_estimate = github_service._estimate_tokens(content)

        return {
            "content_length": content_length,
            "byte_size": byte_size,
            "token_estimate": token_estimate,
        }
    except Exception as e:
        logger.exception(f"Error calculating tokens: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error calculating tokens: {str(e)}"
        )
