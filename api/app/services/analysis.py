"""Analysis service for the API."""

import logging
from typing import Dict, Any, List, Optional
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.config import settings
from app.db.models import AnalysisTask, Report, User
from app.db.session import get_db_session
from app.services.queue import QueueService, get_queue_service

logger = logging.getLogger(__name__)


class AnalysisService:
    """Service for managing analysis tasks."""

    def __init__(self, db: AsyncSession, queue_service: QueueService):
        """
        Initialize the analysis service.

        Args:
            db: Database session
            queue_service: Queue service
        """
        self.db = db
        self.queue_service = queue_service

    async def submit_analysis(
        self, user_id: str, github_url: str, options: Optional[Dict[str, Any]] = None
    ) -> AnalysisTask:
        """
        Submit a GitHub repository for analysis.

        Args:
            user_id: User ID
            github_url: GitHub repository URL
            options: Analysis options

        Returns:
            AnalysisTask: Created analysis task
        """
        # Create options dictionary if not provided
        if options is None:
            options = {}

        # Set default options if not provided
        if "model" not in options:
            options["model"] = settings.DEFAULT_MODEL
        if "temperature" not in options:
            options["temperature"] = float(settings.TEMPERATURE)

        # Get or set analysis_type
        analysis_type = options.get("analysis_type", "fast")

        # Create the task
        task = AnalysisTask(
            user_id=user_id,
            github_url=github_url,
            status="pending",
            options=options,
            progress=0,
            analysis_type=analysis_type,
        )

        # Add to database
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)

        # Enqueue the task for background processing
        task_id = str(task.id)
        await self.queue_service.enqueue_analysis(task_id, github_url, options)

        logger.info(f"Submitted analysis task: {task_id} for URL: {github_url}")

        return task

    async def get_user_tasks(
        self, user_id: str, limit: int = 10, offset: int = 0
    ) -> List[AnalysisTask]:
        """
        Get all analysis tasks for a user.

        Args:
            user_id: User ID
            limit: Maximum number of tasks to return
            offset: Number of tasks to skip

        Returns:
            List[AnalysisTask]: List of analysis tasks
        """
        query = (
            select(AnalysisTask)
            .where(AnalysisTask.user_id == user_id)
            .order_by(AnalysisTask.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_task(self, task_id: str, user_id: str) -> Optional[AnalysisTask]:
        """
        Get a specific analysis task.

        Args:
            task_id: Task ID
            user_id: User ID

        Returns:
            Optional[AnalysisTask]: Analysis task or None if not found
        """
        query = select(AnalysisTask).where(
            AnalysisTask.id == task_id, AnalysisTask.user_id == user_id
        )

        result = await self.db.execute(query)
        return result.scalars().first()

    async def cancel_task(self, task_id: str, user_id: str) -> Optional[AnalysisTask]:
        """
        Cancel an analysis task.

        Args:
            task_id: Task ID
            user_id: User ID

        Returns:
            Optional[AnalysisTask]: Updated task or None if not found
        """
        # Get the task
        task = await self.get_task(task_id, user_id)
        if not task:
            return None

        # Check if task can be canceled
        if task.status in ["completed", "failed"]:
            return None

        # Try to cancel the job
        job_canceled = await self.queue_service.cancel_job(str(task.id))

        # Update task status
        task.status = "failed"
        task.error_message = "Canceled by user"

        # Save changes
        await self.db.commit()
        await self.db.refresh(task)

        logger.info(f"Canceled analysis task: {task.id}")

        return task

    async def delete_task(self, task_id: str, user_id: str) -> bool:
        """
        Delete an analysis task from the database.

        Args:
            task_id: Task ID
            user_id: User ID

        Returns:
            bool: True if task was deleted, False otherwise
        """
        # Get the task
        task = await self.get_task(task_id, user_id)
        if not task:
            return False

        # If task is in progress, try to cancel the job first
        if task.status in ["pending", "in_progress"]:
            await self.queue_service.cancel_job(str(task.id))

        # Delete the task
        await self.db.delete(task)
        await self.db.commit()

        logger.info(f"Deleted analysis task: {task_id}")

        return True


# Dependency
async def get_analysis_service(
    db: AsyncSession = Depends(get_db_session),
    queue_service: QueueService = Depends(get_queue_service),
):
    """Get analysis service instance."""
    return AnalysisService(db, queue_service)
