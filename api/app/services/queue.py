"""Queue service for background tasks."""

import logging
from redis import Redis
from rq import Queue
from typing import Dict, Any, Optional

from app.config import settings

logger = logging.getLogger(__name__)


class QueueService:
    """Service for managing background jobs."""

    def __init__(self):
        """Initialize the queue service."""
        self.redis = Redis.from_url(settings.REDIS_URL)
        self.queue = Queue(name="analysis", connection=self.redis)

    async def enqueue_analysis(self, task_id: str, github_url: str, options: Dict[str, Any]) -> str:
        """
        Enqueue an analysis task.

        Args:
            task_id: UUID of the analysis task
            github_url: GitHub repository URL
            options: Analysis options

        Returns:
            str: Job ID
        """
        logger.info(f"Enqueuing analysis task: {task_id} for {github_url}")

        # Add job to queue
        from app.worker import analyze_repository

        job = self.queue.enqueue(
            analyze_repository,
            args=(task_id, github_url, options),
            job_id=task_id,
            result_ttl=86400,  # Store result for 24 hours
            timeout=3600,  # 1 hour timeout for long analyses
        )

        return job.id

    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get the status of a job.

        Args:
            job_id: Job ID

        Returns:
            Dict[str, Any]: Job status information
        """
        job = self.queue.fetch_job(job_id)

        if not job:
            return {"status": "not_found"}

        return {
            "status": job.get_status(),
            "result": job.result,
            "enqueued_at": job.enqueued_at,
            "started_at": job.started_at,
            "ended_at": job.ended_at,
            "exc_info": job.exc_info,
        }

    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a job if it hasn't started.

        Args:
            job_id: Job ID

        Returns:
            bool: True if job was cancelled, False otherwise
        """
        job = self.queue.fetch_job(job_id)

        if not job or job.get_status() != "queued":
            return False

        job.cancel()
        return True


# Dependency
async def get_queue_service():
    """Get queue service instance."""
    return QueueService()
