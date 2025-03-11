"""
Repository analysis tools for examining GitHub repositories.
"""

from typing import Dict, List, Any, Optional, Tuple
import os
from langchain.tools import tool, StructuredTool
from pydantic import BaseModel, Field

from src.analyzer.github_repo import GitHubRepository
from src.models.config import Config
from src.models.types import RepoDetails

class RepoUrlInput(BaseModel):
    """Input for repository tools."""
    repo_url: str = Field(..., description="URL of the GitHub repository to analyze")

class CodeSamplesInput(BaseModel):
    """Input for code samples collection."""
    repo_url: str = Field(..., description="URL of the GitHub repository to analyze")
    max_samples: int = Field(10, description="Maximum number of code samples to collect")

class RepositoryStructureInput(BaseModel):
    """Input for repository structure exploration."""
    repo_url: str = Field(..., description="URL of the GitHub repository to analyze")
    max_depth: int = Field(3, description="Maximum directory depth to explore")
    include_files: bool = Field(True, description="Whether to include files in the output")

# Initialize GitHub repository with configuration
def get_github_repo() -> GitHubRepository:
    """Get a GitHubRepository instance with the current configuration."""
    config = Config.from_file()
    return GitHubRepository(config)

@tool("fetch_repository_metadata", args_schema=RepoUrlInput, return_direct=False)
def fetch_repository_metadata(repo_url: str) -> Dict[str, Any]:
    """
    Fetch metadata about a GitHub repository, such as stars, forks, description, etc.
    
    Args:
        repo_url: URL of the GitHub repository to analyze
        
    Returns:
        Dictionary containing repository metadata
    """
    github_repo = get_github_repo()
    repo_owner, repo_name = github_repo.setup_repository(repo_url)
    
    # Get repository details
    try:
        repo_details = github_repo.get_repository_details()
        return {
            "success": True,
            "metadata": repo_details,
            "repo_owner": repo_owner,
            "repo_name": repo_name
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "repo_owner": repo_owner,
            "repo_name": repo_name
        }

@tool("collect_code_samples", args_schema=CodeSamplesInput, return_direct=False)
def collect_code_samples(repo_url: str, max_samples: int = 10) -> Dict[str, Any]:
    """
    Collect representative code samples from a GitHub repository for analysis.
    
    Args:
        repo_url: URL of the GitHub repository to analyze
        max_samples: Maximum number of code samples to collect
        
    Returns:
        Dictionary containing code samples and metrics
    """
    github_repo = get_github_repo()
    repo_owner, repo_name = github_repo.setup_repository(repo_url)
    
    # Define a progress callback
    progress_updates = []
    def progress_callback(message):
        progress_updates.append(message)
    
    try:
        # Collect code samples
        file_metrics, code_samples = github_repo.collect_code_samples(progress_callback)
        
        # Limit samples to requested number
        limited_samples = code_samples[:max_samples]
        
        return {
            "success": True,
            "repo_owner": repo_owner,
            "repo_name": repo_name,
            "metrics": file_metrics,
            "sample_count": len(limited_samples),
            "code_samples": limited_samples,
            "progress": progress_updates
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "repo_owner": repo_owner,
            "repo_name": repo_name,
            "progress": progress_updates
        }

@tool("explore_repository_structure", args_schema=RepositoryStructureInput, return_direct=False)
def explore_repository_structure(repo_url: str, max_depth: int = 3, include_files: bool = True) -> Dict[str, Any]:
    """
    Explore the directory structure of a GitHub repository to understand its organization.
    
    Args:
        repo_url: URL of the GitHub repository to analyze
        max_depth: Maximum directory depth to explore
        include_files: Whether to include files in the output
        
    Returns:
        Dictionary containing repository structure information
    """
    github_repo = get_github_repo()
    repo_owner, repo_name = github_repo.setup_repository(repo_url)
    
    if not github_repo.repo:
        return {
            "success": False,
            "error": f"Could not access repository {repo_owner}/{repo_name}",
            "repo_owner": repo_owner,
            "repo_name": repo_name
        }
    
    try:
        # Get repository structure
        structure = _explore_directory("", github_repo, max_depth, include_files)
        
        return {
            "success": True,
            "repo_owner": repo_owner,
            "repo_name": repo_name,
            "structure": structure
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "repo_owner": repo_owner,
            "repo_name": repo_name
        }

def _explore_directory(path: str, github_repo: GitHubRepository, max_depth: int, include_files: bool) -> Dict[str, Any]:
    """Recursively explore directory structure."""
    if max_depth <= 0:
        return {"type": "directory", "name": os.path.basename(path or "root"), "truncated": True}
    
    try:
        contents = github_repo.repo.get_contents(path)
        
        if not isinstance(contents, list):
            contents = [contents]
        
        result = {
            "type": "directory",
            "name": os.path.basename(path or "root"),
            "contents": []
        }
        
        dirs = []
        files = []
        
        for item in contents:
            if item.type == "dir":
                if max_depth > 1:
                    dirs.append(_explore_directory(item.path, github_repo, max_depth - 1, include_files))
                else:
                    dirs.append({"type": "directory", "name": os.path.basename(item.path), "truncated": True})
            elif item.type == "file" and include_files:
                files.append({"type": "file", "name": os.path.basename(item.path), "size": item.size})
        
        # Sort directories and files by name
        result["contents"] = sorted(dirs, key=lambda x: x["name"]) + sorted(files, key=lambda x: x["name"])
        
        return result
    except Exception as e:
        return {"type": "directory", "name": os.path.basename(path or "root"), "error": str(e)}

def get_repository_tools() -> List[StructuredTool]:
    """Get all repository analysis tools."""
    return [
        fetch_repository_metadata,
        collect_code_samples,
        explore_repository_structure
    ]