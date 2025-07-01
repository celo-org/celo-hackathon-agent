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

# Configure logging based on environment variables
log_level_name = os.getenv("LOG_LEVEL", "INFO")
log_level = getattr(logging, log_level_name.upper(), logging.INFO)

logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


def start_api():
    """Start the FastAPI server."""
    logger.info("Starting API server...")

    # Get configuration from environment variables
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("DEBUG", "False").lower() == "true"

    logger.info(f"Server will run on {host}:{port} (reload={reload})")

    # Start the server
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level_name.lower(),
    )


if __name__ == "__main__":
    start_api()
