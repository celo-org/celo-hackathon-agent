#!/bin/bash
# Installation script for AI Project Analyzer Monorepo

set -e

echo "🚀 Installing AI Project Analyzer Monorepo"
echo "=========================================="

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command_exists python3; then
  echo "❌ Python 3 is required but not installed."
  exit 1
fi

if ! command_exists uv; then
  echo "❌ uv is required but not installed."
  echo "Install from: https://github.com/astral-sh/uv"
  exit 1
fi

if ! command_exists npm; then
  echo "❌ npm is required but not installed."
  exit 1
fi

echo "✅ Prerequisites satisfied"

# Install packages in dependency order
echo ""
echo "📦 Installing packages..."

# 1. Install core package (has no local dependencies)
echo "Installing core package..."
cd packages/core
uv pip install -e .
cd ../..

# 2. Install CLI package (depends on core)
echo "Installing CLI package..."
cd packages/cli
uv pip install -e ../core # Install core as editable
uv pip install -e .
cd ../..

# 3. Install API package (depends on core)
echo "Installing API package..."
cd packages/api
uv pip install -e ../core # Install core as editable
uv pip install -e .
cd ../..

# 4. Install frontend dependencies
echo "Installing frontend dependencies..."
cd packages/frontend
npm install
cd ../..

echo ""
echo "✅ All packages installed successfully!"
echo ""
echo "🎯 Next steps:"
echo "1. Copy .env.template to .env and configure your API keys"
echo "2. Start infrastructure: docker-compose -f config/docker-compose.yml up -d"
echo "3. Run migrations: cd packages/api && alembic upgrade head"
echo "4. Start services: ./start.sh --dev"
