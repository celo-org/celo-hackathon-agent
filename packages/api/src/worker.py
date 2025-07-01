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

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

# Import analyze_repository function directly

# Configure logging
log_level_name = os.getenv("LOG_LEVEL", "INFO")
log_level = getattr(logging, log_level_name.upper(), logging.INFO)

logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Silence noisy loggers when not in DEBUG mode
if log_level > logging.DEBUG:
    logging.getLogger("rq.worker").setLevel(logging.WARNING)
    logging.getLogger("rq.queue").setLevel(logging.WARNING)

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
