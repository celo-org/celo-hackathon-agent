# AI Project Analyzer - Simple Makefile
.PHONY: help install test clean dev dev-frontend build docker-up docker-down

# Default target
help:
	@echo "AI Project Analyzer - Available Commands:"
	@echo ""
	@echo "  install     Install all packages"
	@echo "  test        Run tests"
	@echo "  clean       Clean build artifacts"
	@echo "  dev         Start backend development (API + Worker in Docker)"
	@echo "  dev-frontend Start frontend development only"
	@echo "  logs        View API and worker logs"
	@echo "  logs-api    View API logs only"
	@echo "  logs-worker View worker logs only"
	@echo "  logs-all    View all service logs"
	@echo "  build       Build all packages"
	@echo "  docker-up   Start Docker services"
	@echo "  docker-down Stop Docker services"
	@echo "  stop        Stop development environment"

# Install all packages
install:
	@echo "📦 Installing packages..."
	@cd packages/core && uv pip install -e .
	@cd packages/cli && uv pip install -e .
	@cd packages/api && uv pip install -e .
	@cd packages/frontend && npm install
	@echo "✅ Installation complete"

# Run tests
test:
	@echo "🧪 Running tests..."
	@cd packages/core && python -m pytest
	@cd packages/cli && python -m pytest  
	@cd packages/api && python -m pytest
	@echo "✅ Tests complete"

# Clean build artifacts
clean:
	@echo "🧹 Cleaning build artifacts..."
	@find packages/ -name "dist" -type d -exec rm -rf {} + 2>/dev/null || true
	@find packages/ -name "build" -type d -exec rm -rf {} + 2>/dev/null || true
	@find packages/ -name "*.egg-info" -type d -exec rm -rf {} + 2>/dev/null || true
	@find packages/ -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Clean complete"

# Start backend development (API + Worker in Docker with hot reload)
dev:
	@echo "🚀 Starting backend development environment..."
	@echo "Building and starting all backend services in detached mode..."
	@docker-compose up postgres redis api worker -d
	@echo "Waiting for services to be ready..."
	@sleep 8
	@echo ""
	@echo "✅ Backend development environment started:"
	@echo "  API: http://localhost:8000 (Docker with hot reload)"
	@echo "  API Docs: http://localhost:8000/docs"
	@echo "  Worker: Background worker (Docker with hot reload)"
	@echo "  Database: PostgreSQL (Docker)"
	@echo "  Redis: Redis (Docker)"
	@echo ""
	@echo "📋 Useful commands:"
	@echo "  make logs      - View API and worker logs"
	@echo "  make logs-api  - View API logs only"
	@echo "  make logs-worker - View worker logs only"
	@echo "  make stop      - Stop all services"

# Start frontend development only
dev-frontend:
	@echo "🚀 Starting frontend development..."
	@echo "  Frontend will start at: http://localhost:5173"
	@echo "  Press Ctrl+C to stop"
	@echo ""
	@cd packages/frontend && pnpm dev

# Build packages
build:
	@echo "🏗️ Building packages..."
	@cd packages/core && uv build
	@cd packages/cli && uv build
	@cd packages/api && uv build
	@cd packages/frontend && npm run build
	@echo "✅ Build complete"

# Docker commands
docker-up:
	@docker-compose up -d

docker-down:
	@docker-compose down

# View logs from API and worker services
logs:
	@echo "📋 Showing logs for API and Worker services..."
	@docker-compose logs -f api worker

# View API logs only
logs-api:
	@echo "📋 Showing API logs..."
	@docker-compose logs -f api

# View worker logs only
logs-worker:
	@echo "📋 Showing worker logs..."
	@docker-compose logs -f worker

# View all service logs
logs-all:
	@echo "📋 Showing logs for all services..."
	@docker-compose logs -f

# Stop development environment
stop:
	@echo "🛑 Stopping development environment..."
	@docker-compose down
	@pkill -f "vite" 2>/dev/null || true
	@pkill -f "pnpm dev" 2>/dev/null || true
	@echo "✅ Development environment stopped"
