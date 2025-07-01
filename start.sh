#!/bin/bash
# Start script for the AI Project Analyzer Monorepo

set -e

# Function to display usage information
show_usage() {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  --api-only       Start only the API server"
    echo "  --frontend-only  Start only the frontend"
    echo "  --full-stack     Start API + Frontend (default)"
    echo "  --help           Show this help message"
    echo ""
    echo "Development commands:"
    echo "  --dev            Start all services in development mode"
}

# Parse command line arguments
MODE="full-stack"

while [[ $# -gt 0 ]]; do
    case "$1" in
    --api-only)
        MODE="api-only"
        shift
        ;;
    --frontend-only)
        MODE="frontend-only"
        shift
        ;;
    --full-stack)
        MODE="full-stack"
        shift
        ;;
    --dev)
        MODE="dev"
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

echo "AI Project Analyzer - Monorepo"
echo "================================"

# Function to start services
start_services() {
    case "$MODE" in
    "api-only")
        echo "Starting API services..."
        cd packages/api && ./start.sh
        ;;
    "frontend-only")
        echo "Starting frontend..."
        cd packages/frontend && npm run dev
        ;;
    "full-stack")
        echo "Starting full stack (API + Frontend)..."

        # Start API services in background
        cd packages/api
        ./start.sh &
        API_PID=$!
        cd ../..

        # Wait a bit for API to start
        sleep 3

        # Start frontend
        cd packages/frontend
        npm run dev &
        FRONTEND_PID=$!
        cd ../..

        echo "Services started:"
        echo "- API services (PID: $API_PID)"
        echo "- Frontend (PID: $FRONTEND_PID)"
        echo ""
        echo "Access the application at: http://localhost:5173"
        echo "API documentation at: http://localhost:8000/docs"
        ;;
    "dev")
        echo "Starting all services in development mode..."

        # Start infrastructure
        echo "Starting infrastructure (PostgreSQL + Redis)..."
        docker-compose -f config/docker-compose.yml up -d

        # Wait for services to be ready
        echo "Waiting for services to be ready..."
        sleep 5

        # Start API
        cd packages/api
        ./start.sh &
        API_PID=$!
        cd ../..

        # Start frontend
        cd packages/frontend
        npm run dev &
        FRONTEND_PID=$!
        cd ../..

        echo ""
        echo "Development environment started:"
        echo "- PostgreSQL: localhost:5432"
        echo "- Redis: localhost:6379"
        echo "- API: http://localhost:8000"
        echo "- Frontend: http://localhost:5173"
        echo "- API Docs: http://localhost:8000/docs"
        ;;
    esac
}

# Check dependencies
check_dependencies() {
    if [ "$MODE" != "frontend-only" ]; then
        if ! command -v uv &>/dev/null; then
            echo "Error: uv is required but not installed."
            echo "Install from: https://github.com/astral-sh/uv"
            exit 1
        fi
    fi

    if [ "$MODE" != "api-only" ]; then
        if ! command -v npm &>/dev/null; then
            echo "Error: npm is required but not installed."
            exit 1
        fi
    fi

    if [ "$MODE" = "dev" ]; then
        if ! command -v docker-compose &>/dev/null && ! command -v docker &>/dev/null; then
            echo "Error: Docker is required for development mode."
            exit 1
        fi
    fi
}

# Main execution
check_dependencies
start_services

echo ""
echo "Press Ctrl+C to stop all services"

# Wait for user interrupt
wait
