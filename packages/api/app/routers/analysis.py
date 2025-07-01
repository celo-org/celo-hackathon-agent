"""
Analysis router for the API.
"""

import logging

# Import from installed core package
import sys
from pathlib import Path

# Import from core package
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

# Add the core package to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "core" / "src"))

from file_parser import validate_github_url
from sqlalchemy.future import select

from app.db.models import AnalysisTask, User
from app.routers.auth import get_current_user
from app.schemas.analysis import (
    AnalysisSubmissionRequest,
    AnalysisSubmissionResponse,
    AnalysisTaskListResponse,
    AnalysisTaskResponse,
)
from app.services.analysis import AnalysisService, get_analysis_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/submit",
    response_model=AnalysisSubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def submit_analysis(
    analysis_data: AnalysisSubmissionRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    analysis_service: AnalysisService = Depends(get_analysis_service),
):
    """
    Submit GitHub repository for analysis.

    Args:
        analysis_data: Analysis request data
        current_user: Current authenticated user
        analysis_service: Analysis service

    Returns:
        AnalysisSubmissionResponse: Analysis task status
    """
    logger.debug(f"Analysis submission request from user {current_user.username}")
    logger.debug(f"Request data: {analysis_data}")

    # Validate GitHub URLs
    if not analysis_data.github_urls or len(analysis_data.github_urls) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one GitHub URL is required",
        )

    # For now, we only handle the first URL
    # In future phases, we could process multiple URLs in batch
    github_url = analysis_data.github_urls[0]

    # Validate GitHub URL
    logger.debug(f"Validating GitHub URL: {github_url}")
    if not validate_github_url(github_url):
        logger.warning(f"Invalid GitHub URL submitted: {github_url}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid GitHub repository URL",
        )
    logger.debug(f"GitHub URL validation passed: {github_url}")

    # Create options dictionary
    options = {}
    if analysis_data.options:
        options = analysis_data.options.model_dump()

    # Submit analysis
    task = await analysis_service.submit_analysis(
        user_id=str(current_user.id),
        github_url=github_url,
        options=options,
    )

    # Convert to response schema
    return {
        "task_id": str(task.id),
        "status": task.status,
        "github_url": task.github_url,
        "progress": task.progress,
        "submitted_at": task.created_at,
        "error_message": task.error_message,
        "completed_at": task.completed_at,
        "analysis_type": task.analysis_type or options.get("analysis_type", "fast"),
    }


@router.get("/tasks", response_model=AnalysisTaskListResponse)
async def get_analysis_tasks(
    current_user: Annotated[User, Depends(get_current_user)],
    analysis_service: AnalysisService = Depends(get_analysis_service),
    limit: int = 10,
    offset: int = 0,
):
    """
    Get all analysis tasks for the current user.

    Args:
        current_user: Current authenticated user
        analysis_service: Analysis service
        limit: Maximum number of tasks to return
        offset: Number of tasks to skip

    Returns:
        AnalysisTaskListResponse: List of analysis tasks
    """
    # Get tasks
    task_objects = await analysis_service.get_user_tasks(
        user_id=str(current_user.id),
        limit=limit,
        offset=offset,
    )

    # Count total tasks using the analysis service's db session
    total_query = select(AnalysisTask).where(AnalysisTask.user_id == current_user.id)
    total_result = await analysis_service.db.execute(total_query)
    total = len(total_result.scalars().all())

    # Convert tasks to response schema
    tasks = []
    for task in task_objects:
        tasks.append(
            {
                "task_id": str(task.id),
                "status": task.status,
                "github_url": task.github_url,
                "progress": task.progress,
                "submitted_at": task.created_at,
                "error_message": task.error_message,
                "completed_at": task.completed_at,
                "analysis_type": task.analysis_type or "fast",
            }
        )

    return {"tasks": tasks, "total": total}


@router.get("/tasks/{task_id}", response_model=AnalysisTaskResponse)
async def get_analysis_task(
    task_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    analysis_service: AnalysisService = Depends(get_analysis_service),
):
    """
    Get status of a specific analysis task.

    Args:
        task_id: Analysis task ID
        current_user: Current authenticated user
        analysis_service: Analysis service

    Returns:
        AnalysisTaskResponse: Analysis task status
    """
    # Get task
    task = await analysis_service.get_task(
        task_id=task_id,
        user_id=str(current_user.id),
    )

    # Check if task exists
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis task not found",
        )

    # Convert to response schema
    return {
        "task_id": str(task.id),
        "status": task.status,
        "github_url": task.github_url,
        "progress": task.progress,
        "submitted_at": task.created_at,
        "error_message": task.error_message,
        "completed_at": task.completed_at,
        "analysis_type": task.analysis_type or "fast",
    }


@router.delete("/tasks/{task_id}/cancel", response_model=AnalysisTaskResponse)
async def cancel_analysis_task(
    task_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    analysis_service: AnalysisService = Depends(get_analysis_service),
):
    """
    Cancel an analysis task if not completed.

    Args:
        task_id: Analysis task ID
        current_user: Current authenticated user
        analysis_service: Analysis service

    Returns:
        AnalysisTaskResponse: Analysis task status
    """
    # Cancel task
    task = await analysis_service.cancel_task(
        task_id=task_id,
        user_id=str(current_user.id),
    )

    # Check if task exists or can be canceled
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis task not found or cannot be canceled",
        )

    # Convert to response schema
    return {
        "task_id": str(task.id),
        "status": task.status,
        "github_url": task.github_url,
        "progress": task.progress,
        "submitted_at": task.created_at,
        "error_message": task.error_message,
        "completed_at": task.completed_at,
        "analysis_type": task.analysis_type or "fast",
    }


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_analysis_task(
    task_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    analysis_service: AnalysisService = Depends(get_analysis_service),
):
    """
    Permanently delete an analysis task.

    Args:
        task_id: Analysis task ID
        current_user: Current authenticated user
        analysis_service: Analysis service

    Returns:
        None: Returns 204 No Content on success
    """
    # Delete task
    success = await analysis_service.delete_task(
        task_id=task_id,
        user_id=str(current_user.id),
    )

    # Check if task exists and was deleted
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis task not found",
        )

    # Return no content
    return None
