"""Analysis service for the API."""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.config import settings
from app.db.models import AnalysisTask, Report, User
from app.services.queue import QueueService

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
        self, 
        user_id: str, 
        github_url: str, 
        options: Optional[Dict[str, Any]] = None
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
        
        # Create the task
        task = AnalysisTask(
            user_id=user_id,
            github_url=github_url,
            status="pending",
            options=options,
            progress=0,
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
        self, 
        user_id: str, 
        limit: int = 10, 
        offset: int = 0
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
        query = (
            select(AnalysisTask)
            .where(AnalysisTask.id == task_id, AnalysisTask.user_id == user_id)
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

# Dependency
async def get_analysis_service(
    db: AsyncSession,
    queue_service: QueueService,
):
    """Get analysis service instance."""
    return AnalysisService(db, queue_service)