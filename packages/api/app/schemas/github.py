"""
Schemas for GitHub API requests and responses.
"""

from typing import List, Optional
from pydantic import BaseModel, HttpUrl, Field


class GitHubUrlRequest(BaseModel):
    """Request schema for GitHub URL processing."""

    url: HttpUrl = Field(..., description="GitHub repository URL")


class GitHubContentItem(BaseModel):
    """Schema for a GitHub repository content item (file or directory)."""

    name: str = Field(..., description="Name of the file or directory")
    path: str = Field(
        ..., description="Path to the file or directory relative to the repository root"
    )
    sha: str = Field(..., description="SHA hash of the content")
    size: Optional[int] = Field(None, description="Size of the file in bytes (if a file)")
    type: str = Field(..., description="Type of content (file or dir)")
    download_url: Optional[str] = Field(
        None, description="URL to download the raw file (if a file)"
    )
    html_url: Optional[str] = Field(None, description="HTML URL to view the content on GitHub")
    token_estimate: Optional[int] = Field(0, description="Estimated token count for text content")


class GitHubContentsResponse(BaseModel):
    """Response schema for GitHub repository contents."""

    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    path: str = Field("", description="Current path within the repository")
    contents: List[GitHubContentItem] = Field(..., description="List of content items")


class GitHubFileRequest(BaseModel):
    """Request schema for GitHub file content."""

    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    path: str = Field(..., description="Path to the file within the repository")


class GitHubFileResponse(BaseModel):
    """Response schema for GitHub file content."""

    name: str = Field(..., description="Name of the file")
    path: str = Field(..., description="Path to the file relative to the repository root")
    sha: str = Field(..., description="SHA hash of the content")
    size: int = Field(..., description="Size of the file in bytes")
    content: Optional[str] = Field(None, description="Text content of the file (if text)")
    raw_url: Optional[str] = Field(None, description="URL to the raw file content")
    token_estimate: int = Field(0, description="Estimated token count for text content")


class TokenCalculationRequest(BaseModel):
    """Request schema for token calculation."""

    content: str = Field(..., description="Text content to calculate tokens for")


class TokenCalculationResponse(BaseModel):
    """Response schema for token calculation."""

    content_length: int = Field(..., description="Length of the content in characters")
    byte_size: int = Field(..., description="Size of the content in bytes")
    token_estimate: int = Field(..., description="Estimated token count")
