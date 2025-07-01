"""
API server startup script for the GitHub Repository Analyzer.

This script initializes and runs the FastAPI application,
setting up the required logging and configuration.
"""

import logging
import os
import sys
from pathlib import Path

import uvicorn
from dotenv import load_dotenv

# Add the API app to the path
api_dir = Path(__file__).parent.parent
sys.path.insert(0, str(api_dir))

# Load environment variables from root .env file
project_root = Path(__file__).parent.parent.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)

# Add project root to path to import core modules
sys.path.insert(0, str(project_root))

# Import centralized logging setup
try:
    # Try Docker/installed package path first
    from core.src.config import setup_logging
except ImportError:
    # Fallback to development path
    from packages.core.src.config import setup_logging

# Configure logging using centralized setup
log_level_name = os.getenv("LOG_LEVEL", "INFO")
setup_logging(log_level_name)
logger = logging.getLogger(__name__)


def start_api():
    """Start the FastAPI server."""
    logger.debug("Starting API server...")

    # Get configuration from environment variables
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("DEBUG", "False").lower() == "true"

    logger.debug(f"Server will run on {host}:{port} (reload={reload})")

    # Start the server with suppressed Uvicorn INFO logs
    uvicorn_log_level = "warning" if log_level_name.upper() != "DEBUG" else "debug"
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=uvicorn_log_level,
    )


if __name__ == "__main__":
    start_api()
