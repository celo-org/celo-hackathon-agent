#!/bin/bash
# Build script for AI Project Analyzer

set -e

echo "🏗️  Building AI Project Analyzer for Production"
echo "=============================================="

# Function to display usage
show_usage() {
  echo "Usage: $0 [options]"
  echo "Options:"
  echo "  --package PACKAGE  Build specific package (core|cli|api|frontend|all)"
  echo "  --clean           Clean build artifacts first"
  echo "  --help            Show this help message"
}

# Parse arguments
PACKAGE="all"
CLEAN=false

while [[ $# -gt 0 ]]; do
  case "$1" in
  --package)
    PACKAGE="$2"
    shift 2
    ;;
  --clean)
    CLEAN=true
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

# Clean build artifacts if requested
if [ "$CLEAN" = true ]; then
  echo "🧹 Cleaning build artifacts..."
  find packages/ -name "dist" -type d -exec rm -rf {} + 2>/dev/null || true
  find packages/ -name "build" -type d -exec rm -rf {} + 2>/dev/null || true
  find packages/ -name "*.egg-info" -type d -exec rm -rf {} + 2>/dev/null || true
  find packages/ -name "__pycache__" -type d -not -path "*/node_modules/*" -exec rm -rf {} + 2>/dev/null || true
  echo "✅ Build artifacts cleaned"
fi

# Build packages
build_package() {
  local pkg=$1
  echo "Building $pkg package..."

  case "$pkg" in
  "core" | "cli" | "api")
    cd "packages/$pkg"
    uv build
    cd ../..
    ;;
  "frontend")
    cd "packages/frontend"
    npm run build
    cd ../..
    ;;
  *)
    echo "Unknown package: $pkg"
    return 1
    ;;
  esac
}

if [ "$PACKAGE" = "all" ]; then
  echo "📦 Building all packages..."
  build_package "core"
  build_package "cli"
  build_package "api"
  build_package "frontend"
else
  echo "📦 Building $PACKAGE package..."
  build_package "$PACKAGE"
fi

echo ""
echo "✅ Build completed successfully!"
echo ""
echo "📁 Build artifacts:"
find packages/ -name "dist" -type d -exec echo "  {}" \;
find packages/frontend -name "dist" -type d -exec echo "  {}" \; 2>/dev/null || true
