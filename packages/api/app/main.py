"""
Main application module for the API server.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.session import create_db_and_tables
from app.routers import analysis, auth, health, reports

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Silence noisy loggers when not in DEBUG mode
if getattr(logging, settings.LOG_LEVEL) > logging.DEBUG:
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.dialects").setLevel(logging.WARNING)
    logging.getLogger("alembic").setLevel(logging.WARNING)

# Always silence these noisy loggers regardless of log level
logging.getLogger("sqlalchemy.engine.Engine").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("watchfiles.main").setLevel(logging.WARNING)
logging.getLogger("app.db.session").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events for the FastAPI application.
    This is executed before the application starts and after it shuts down.
    """
    # Startup: create database tables
    logger.debug("Creating database tables if they don't exist...")
    await create_db_and_tables()

    # Start application
    logger.debug("Application startup complete")
    yield

    # Shutdown
    logger.debug("Application shutdown")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(analysis.router, prefix=f"{settings.API_V1_STR}/analysis", tags=["Analysis"])
app.include_router(reports.router, prefix=f"{settings.API_V1_STR}/reports", tags=["Reports"])
app.include_router(health.router, prefix=f"{settings.API_V1_STR}/health", tags=["Health"])


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint for the API."""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.API_VERSION,
        "docs": "/docs",
    }
