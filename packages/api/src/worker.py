#!/usr/bin/env python3
"""
Worker process for background tasks.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

from redis import Redis
from rq import Queue, Worker

# Prevent issues with fork() on macOS
os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Add packages/api to path so app.* imports work
api_package_path = project_root / "packages" / "api"
sys.path.insert(0, str(api_package_path))

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

# Import centralized logging setup
from config import setup_logging

# Configure logging using centralized setup
log_level_name = os.getenv("LOG_LEVEL", "INFO")
setup_logging(log_level_name)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Worker process for background tasks")

    parser.add_argument(
        "--listen",
        type=str,
        default="analysis",
        help="Queue names to listen on (comma-separated)",
    )

    parser.add_argument(
        "--burst",
        action="store_true",
        help="Run in burst mode (quit after all work is done)",
    )

    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()

    # Get Redis connection
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_conn = Redis.from_url(redis_url)

    # Parse queue names
    queue_names = [q.strip() for q in args.listen.split(",")]
    logger.debug(f"Starting worker listening on queues: {', '.join(queue_names)}")

    # Start worker
    queues = [Queue(name=name, connection=redis_conn) for name in queue_names]
    worker = Worker(queues, connection=redis_conn)

    worker.work(burst=args.burst)


if __name__ == "__main__":
    main()
