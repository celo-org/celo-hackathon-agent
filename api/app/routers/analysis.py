"""
Analysis router for the API.
"""

import logging
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.config import settings
from app.db.session import get_db_session
from app.db.models import User, AnalysisTask
from app.routers.auth import get_current_user
from app.schemas.analysis import AnalysisCreate, AnalysisStatus, AnalysisTaskList
from app.services.analysis import AnalysisService, get_analysis_service
from app.services.queue import QueueService, get_queue_service
from src.file_parser import validate_github_url

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/submit", response_model=AnalysisStatus, status_code=status.HTTP_202_ACCEPTED
)
async def submit_analysis(
    analysis_data: AnalysisCreate,
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
        AnalysisStatus: Analysis task status
    """
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
    if not validate_github_url(github_url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid GitHub repository URL",
        )

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


@router.get("/tasks", response_model=AnalysisTaskList)
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
        AnalysisTaskList: List of analysis tasks
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


@router.get("/tasks/{task_id}", response_model=AnalysisStatus)
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
        AnalysisStatus: Analysis task status
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


@router.delete("/tasks/{task_id}/cancel", response_model=AnalysisStatus)
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
        AnalysisStatus: Analysis task status
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
