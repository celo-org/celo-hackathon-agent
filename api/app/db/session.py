"""
Database session management for the API server.
"""

import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.ext.declarative import declarative_base

from api.app.config import settings

# Replace postgresql:// with postgresql+asyncpg:// for async SQLAlchemy
DATABASE_URL = str(settings.DATABASE_URL).replace(
    "postgresql://", "postgresql+asyncpg://"
)

logger = logging.getLogger(__name__)

# Create async engine
engine = create_async_engine(
    DATABASE_URL, 
    echo=settings.DEBUG,
    future=True,
)

# Create async session factory
async_session_factory = async_sessionmaker(
    engine, 
    expire_on_commit=False,
    autoflush=False,
)

# Create declarative base for SQLAlchemy models
Base = declarative_base()


async def get_db_session() -> AsyncSession:
    """
    Get a database session.
    This function is used as a FastAPI dependency.
    """
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_db_and_tables():
    """Create database tables if they don't exist."""
    async with engine.begin() as conn:
        # Import models to ensure they're registered with Base metadata
        from api.app.db.models import User, AnalysisTask, Report, ApiKey
        
        logger.info("Creating database tables...")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created or already exist")