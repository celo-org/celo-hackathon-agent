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
	@echo "Building and starting all backend services..."
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
	@echo "To stop: make stop"

# Start frontend development only
dev-frontend:
	@echo "🚀 Starting frontend development..."
	@cd packages/frontend && pnpm dev &
	@echo ""
	@echo "✅ Frontend development started:"
	@echo "  Frontend: http://localhost:5173 (with hot reload)"
	@echo ""
	@echo "To stop: make stop"

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

# Stop development environment
stop:
	@echo "🛑 Stopping development environment..."
	@docker-compose down
	@pkill -f "vite" 2>/dev/null || true
	@pkill -f "pnpm dev" 2>/dev/null || true
	@echo "✅ Development environment stopped"
