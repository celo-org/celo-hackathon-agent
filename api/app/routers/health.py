"""
Health check router for the API.
"""

import logging
import time
import sys
from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from api.app.config import settings
from api.app.db.session import get_db_session

logger = logging.getLogger(__name__)

router = APIRouter()

# Store application start time
start_time = time.time()


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.
    
    Returns:
        Dict[str, Any]: Health status
    """
    return {
        "status": "healthy",
        "version": settings.API_VERSION,
        "uptime": int(time.time() - start_time),
        "environment": "development" if settings.DEBUG else "production",
    }


@router.get("/dependencies")
async def dependencies_health(
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    Check health of dependencies.
    
    Args:
        db: Database session
        
    Returns:
        Dict[str, Any]: Dependencies health status
    """
    health_data = {
        "database": "unknown",
        "ipfs": "unknown",
        "llm_service": "unknown",
    }
    
    # Check database connection
    try:
        # Simple query to test database connection
        result = await db.execute(text("SELECT 1"))
        await result.fetchone()
        health_data["database"] = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        health_data["database"] = f"unhealthy: {str(e)}"
    
    # Check Google API key (for LLM service)
    if settings.GOOGLE_API_KEY:
        health_data["llm_service"] = "configured"
    else:
        health_data["llm_service"] = "unconfigured"
    
    # IPFS is considered configured if IPFS_URL is set
    if settings.IPFS_URL:
        health_data["ipfs"] = "configured"
    else:
        health_data["ipfs"] = "unconfigured"
    
    # Add system info
    health_data["system_info"] = {
        "python_version": sys.version,
        "api_version": settings.API_VERSION,
    }
    
    return health_data