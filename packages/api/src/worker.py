#!/usr/bin/env python3
"""
Worker process for background tasks.
"""

import argparse
import logging
import os

from redis import Redis
from rq import Queue, Worker

# Prevent issues with fork() on macOS
os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"

# PYTHONPATH is set via Docker environment variables
# No manual sys.path manipulation needed

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
    logger.debug(f"Connecting to Redis at: {redis_url}")

    try:
        redis_conn = Redis.from_url(redis_url)
        redis_conn.ping()  # Test connection
        logger.debug("Redis connection successful")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        return

    # Parse queue names
    queue_names = [q.strip() for q in args.listen.split(",")]
    logger.debug(f"Starting worker listening on queues: {', '.join(queue_names)}")

    # Start worker
    try:
        queues = [Queue(name=name, connection=redis_conn) for name in queue_names]
        logger.debug(f"Created {len(queues)} queues")

        worker = Worker(queues, connection=redis_conn)
        logger.debug(f"Created worker: {worker}")

        logger.debug(f"Starting worker with burst={args.burst}")

        # Add a periodic callback to verify the worker is alive
        import threading
        import time

        def heartbeat():
            count = 0
            while True:
                time.sleep(30)
                count += 1
                logger.debug(f"[WORKER HEARTBEAT #{count}] Worker is alive and running")

        # Start heartbeat in background thread
        if not args.burst:
            heartbeat_thread = threading.Thread(target=heartbeat, daemon=True)
            heartbeat_thread.start()
            logger.debug("Started worker heartbeat thread")

        worker.work(burst=args.burst)
        logger.debug("Worker.work() returned - this should only happen in burst mode or on exit")

    except Exception as e:
        logger.error(f"Error in worker execution: {e}")
        import traceback

        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
