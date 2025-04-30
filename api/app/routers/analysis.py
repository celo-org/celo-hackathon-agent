"""
Analysis router for the API.
"""

import logging
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from api.app.config import settings
from api.app.db.session import get_db_session
from api.app.db.models import User, AnalysisTask
from api.app.routers.auth import get_current_user
from api.app.schemas.analysis import AnalysisCreate, AnalysisStatus, AnalysisTaskList

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/submit", response_model=AnalysisStatus, status_code=status.HTTP_202_ACCEPTED)
async def submit_analysis(
    analysis_data: AnalysisCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db_session),
):
    """
    Submit GitHub repository for analysis.
    
    Args:
        analysis_data: Analysis request data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        AnalysisStatus: Analysis task status
    """
    # For Phase 1, we'll just create a placeholder task
    # In Phase 2, we'll implement the actual analysis queue
    
    # TODO: Add validation for GitHub URLs
    
    # Create a new analysis task for the first URL
    # In Phase 2, we'll handle multiple URLs properly
    github_url = analysis_data.github_urls[0]
    
    # Create options dictionary
    options = {}
    if analysis_data.options:
        options = analysis_data.options.model_dump()
    
    # Create the task
    task = AnalysisTask(
        user_id=current_user.id,
        github_url=github_url,
        status="pending",
        options=options,
    )
    
    # Add to database
    db.add(task)
    await db.commit()
    await db.refresh(task)
    
    logger.info(f"Created new analysis task: {task.id} for URL: {github_url}")
    
    # Return task status
    return task


@router.get("/tasks", response_model=AnalysisTaskList)
async def get_analysis_tasks(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db_session),
    limit: int = 10,
    offset: int = 0,
):
    """
    Get all analysis tasks for the current user.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        limit: Maximum number of tasks to return
        offset: Number of tasks to skip
        
    Returns:
        AnalysisTaskList: List of analysis tasks
    """
    # Query tasks for the current user
    query = (
        select(AnalysisTask)
        .where(AnalysisTask.user_id == current_user.id)
        .order_by(AnalysisTask.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    # Get total task count
    total_query = (
        select(AnalysisTask)
        .where(AnalysisTask.user_id == current_user.id)
    )
    total_result = await db.execute(total_query)
    total = len(total_result.scalars().all())
    
    return {"tasks": tasks, "total": total}


@router.get("/tasks/{task_id}", response_model=AnalysisStatus)
async def get_analysis_task(
    task_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db_session),
):
    """
    Get status of a specific analysis task.
    
    Args:
        task_id: Analysis task ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        AnalysisStatus: Analysis task status
    """
    # Query the task
    query = (
        select(AnalysisTask)
        .where(AnalysisTask.id == task_id, AnalysisTask.user_id == current_user.id)
    )
    
    result = await db.execute(query)
    task = result.scalars().first()
    
    # Check if task exists
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis task not found",
        )
    
    return task


@router.delete("/tasks/{task_id}", response_model=AnalysisStatus)
async def cancel_analysis_task(
    task_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db_session),
):
    """
    Cancel an analysis task if not completed.
    
    Args:
        task_id: Analysis task ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        AnalysisStatus: Analysis task status
    """
    # Query the task
    query = (
        select(AnalysisTask)
        .where(AnalysisTask.id == task_id, AnalysisTask.user_id == current_user.id)
    )
    
    result = await db.execute(query)
    task = result.scalars().first()
    
    # Check if task exists
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis task not found",
        )
    
    # Check if task can be canceled
    if task.status in ["completed", "failed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Task cannot be canceled in '{task.status}' state",
        )
    
    # Cancel the task
    task.status = "failed"
    task.error_message = "Canceled by user"
    
    await db.commit()
    await db.refresh(task)
    
    logger.info(f"Canceled analysis task: {task.id}")
    
    return task