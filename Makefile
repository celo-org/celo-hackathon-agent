# AI Project Analyzer - Simple Makefile
.PHONY: help install test clean dev build docker-up docker-down

# Default target
help:
	@echo "AI Project Analyzer - Available Commands:"
	@echo ""
	@echo "  install     Install all packages"
	@echo "  test        Run tests"
	@echo "  clean       Clean build artifacts"
	@echo "  dev         Start development environment"
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

# Start development environment
dev:
	@echo "🚀 Starting development environment..."
	@echo "Starting backend services..."
	@docker-compose up -d
	@echo "Starting frontend..."
	@cd packages/frontend && npm run dev &
	@echo ""
	@echo "✅ Development environment started:"
	@echo "  API: http://localhost:8000"
	@echo "  Frontend: http://localhost:5173"
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
	@echo "✅ Development environment stopped"
