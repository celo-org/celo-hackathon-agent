"""
Database session management for the API server.
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base

from app.config import settings

# Replace postgresql:// with postgresql+asyncpg:// for async SQLAlchemy
DATABASE_URL = str(settings.DATABASE_URL).replace("postgresql://", "postgresql+asyncpg://")

logger = logging.getLogger(__name__)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Disable SQL logging to reduce noise
    future=True,
)

# Create async session factory
async_session_factory = async_sessionmaker(
    engine,
    expire_on_commit=False,
    autoflush=True,  # Enable autoflush to ensure changes are flushed to DB
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

        await conn.run_sync(Base.metadata.create_all)
