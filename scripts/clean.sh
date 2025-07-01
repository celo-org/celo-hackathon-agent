#!/bin/bash
# Cleanup script for AI Project Analyzer

set -e

echo "🧹 Cleaning AI Project Analyzer Development Artifacts"
echo "===================================================="

# Function to display usage
show_usage() {
  echo "Usage: $0 [options]"
  echo "Options:"
  echo "  --all           Clean everything (build artifacts, caches, dependencies)"
  echo "  --build         Clean build artifacts only"
  echo "  --cache         Clean caches only"
  echo "  --deps          Clean installed dependencies"
  echo "  --logs          Clean log files"
  echo "  --help          Show this help message"
}

# Parse arguments
CLEAN_ALL=false
CLEAN_BUILD=false
CLEAN_CACHE=false
CLEAN_DEPS=false
CLEAN_LOGS=false

# If no arguments, clean common artifacts
if [ $# -eq 0 ]; then
  CLEAN_BUILD=true
  CLEAN_CACHE=true
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
  --all)
    CLEAN_ALL=true
    shift
    ;;
  --build)
    CLEAN_BUILD=true
    shift
    ;;
  --cache)
    CLEAN_CACHE=true
    shift
    ;;
  --deps)
    CLEAN_DEPS=true
    shift
    ;;
  --logs)
    CLEAN_LOGS=true
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

# Set all flags if --all is specified
if [ "$CLEAN_ALL" = true ]; then
  CLEAN_BUILD=true
  CLEAN_CACHE=true
  CLEAN_DEPS=true
  CLEAN_LOGS=true
fi

# Clean build artifacts
if [ "$CLEAN_BUILD" = true ]; then
  echo "🏗️  Cleaning build artifacts..."

  # Python build artifacts
  find packages/ -name "dist" -type d -exec rm -rf {} + 2>/dev/null || true
  find packages/ -name "build" -type d -exec rm -rf {} + 2>/dev/null || true
  find packages/ -name "*.egg-info" -type d -exec rm -rf {} + 2>/dev/null || true

  # Frontend build artifacts
  find packages/frontend -name "dist" -type d -exec rm -rf {} + 2>/dev/null || true

  echo "✅ Build artifacts cleaned"
fi

# Clean caches
if [ "$CLEAN_CACHE" = true ]; then
  echo "🗂️  Cleaning caches..."

  # Python caches
  find packages/ -name "__pycache__" -type d -not -path "*/node_modules/*" -exec rm -rf {} + 2>/dev/null || true
  find packages/ -name "*.pyc" -delete 2>/dev/null || true
  find packages/ -name "*.pyo" -delete 2>/dev/null || true

  # Test caches
  find packages/ -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
  find packages/ -name ".coverage" -delete 2>/dev/null || true
  find packages/ -name "htmlcov" -type d -exec rm -rf {} + 2>/dev/null || true

  # Ruff cache
  find packages/ -name ".ruff_cache" -type d -exec rm -rf {} + 2>/dev/null || true

  echo "✅ Caches cleaned"
fi

# Clean dependencies
if [ "$CLEAN_DEPS" = true ]; then
  echo "📦 Cleaning dependencies..."

  # Frontend dependencies
  if [ -d "packages/frontend/node_modules" ]; then
    rm -rf packages/frontend/node_modules
    echo "  ✅ Frontend node_modules removed"
  fi

  # Python virtual environments (if any)
  find packages/ -name "venv" -type d -exec rm -rf {} + 2>/dev/null || true
  find packages/ -name ".venv" -type d -exec rm -rf {} + 2>/dev/null || true

  echo "✅ Dependencies cleaned"
fi

# Clean logs
if [ "$CLEAN_LOGS" = true ]; then
  echo "📋 Cleaning logs..."

  # Application logs
  find . -name "*.log" -not -path "*/node_modules/*" -delete 2>/dev/null || true
  find . -name "logs" -type d -not -path "*/node_modules/*" -exec rm -rf {} + 2>/dev/null || true

  # Database logs (development)
  rm -rf .postgres_data 2>/dev/null || true

  echo "✅ Logs cleaned"
fi

echo ""
echo "✅ Cleanup completed!"
echo ""
echo "💡 To reinstall everything:"
echo "  ./scripts/install.sh     # Install all packages"
echo "  ./scripts/dev-setup.sh   # Set up development environment"
