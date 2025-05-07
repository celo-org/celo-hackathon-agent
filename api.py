"""
API server startup script for the GitHub Repository Analyzer.

This script initializes and runs the FastAPI application,
setting up the required logging and configuration.
"""

import logging
import uvicorn
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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

    # Add the API directory to the path so we can import the app
    api_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api")
    if api_dir not in sys.path:
        sys.path.append(api_dir)

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
