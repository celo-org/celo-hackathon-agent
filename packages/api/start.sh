#!/bin/bash
# Start script for the GitHub Repository Analyzer API

# Prevent issues with fork() on macOS
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES

# Change to the project root directory
cd "$(dirname "$0")/../.."

# Load environment variables
if [ -f .env ]; then
    source .env
fi

# Function to display usage information
show_usage() {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  --api-only     Start only the API server"
    echo "  --worker-only  Start only the worker process"
    echo "  --help         Show this help message"
    echo ""
    echo "By default, both API server and worker will be started."
}

# Parse command line arguments
API_ONLY=false
WORKER_ONLY=false

while [[ $# -gt 0 ]]; do
    case "$1" in
    --api-only)
        API_ONLY=true
        shift
        ;;
    --worker-only)
        WORKER_ONLY=true
        shift
        ;;
    --help)
        show_usage
        exit 0
        ;;
    *)
        echo "Unknown option: $1"
        show_usage
        exit 1
        ;;
    esac
done

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a process is running
is_process_running() {
    pgrep -f "$1" >/dev/null
}

# Check Redis status
check_redis() {
    if ! command_exists redis-cli; then
        echo "Redis CLI not found. Cannot check Redis status."
        return 1
    fi

    if redis-cli ping >/dev/null 2>&1; then
        echo "✅ Redis is running"
        return 0
    else
        echo "❌ Redis is not running"
        echo "  Please start Redis with: docker run -d -p 6379:6379 --name redis-server redis"
        return 1
    fi
}

# Start the API server
start_api() {
    echo "Starting API server..."
    cd packages/api
    uv run src/api.py &
    API_PID=$!
    echo "API server started with PID: $API_PID"
    cd ../..
}

# Start the worker process
start_worker() {
    echo "Starting worker process..."
    cd packages/api
    uv run src/worker.py &
    WORKER_PID=$!
    echo "Worker process started with PID: $WORKER_PID"
    cd ../..
}

# Main execution
echo "GitHub Repository Analyzer API"
echo "==============================="

# Always check Redis
check_redis
REDIS_STATUS=$?

if [ "$REDIS_STATUS" -ne 0 ] && [ "$WORKER_ONLY" = true ]; then
    echo "Cannot start worker without Redis. Exiting."
    exit 1
fi

# Start the requested components
if [ "$API_ONLY" = true ]; then
    start_api
elif [ "$WORKER_ONLY" = true ]; then
    if [ "$REDIS_STATUS" -eq 0 ]; then
        start_worker
    fi
else
    # Start both API and worker
    start_api
    if [ "$REDIS_STATUS" -eq 0 ]; then
        start_worker
    fi
fi

# Display startup message
echo ""
echo "Services started:"
if [ "$API_ONLY" = false ]; then
    if [ "$REDIS_STATUS" -eq 0 ]; then
        echo "- Worker process (PID: $WORKER_PID)"
    fi
fi
if [ "$WORKER_ONLY" = false ]; then
    echo "- API server (PID: $API_PID)"
    echo ""
    echo "API is available at: http://localhost:${API_PORT:-8000}"
    echo "API documentation at: http://localhost:${API_PORT:-8000}/docs"
fi

echo ""
echo "Press Ctrl+C to stop all services"

# Wait for user interrupt
wait
