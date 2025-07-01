#!/bin/bash
# Development setup script for AI Project Analyzer

set -e

echo "🛠️  Setting up AI Project Analyzer for Development"
echo "================================================="

# Run installation first
echo "Running installation..."
./scripts/install.sh

echo ""
echo "🔧 Setting up development environment..."

# Install development dependencies
echo "Installing development dependencies..."

cd packages/core
uv pip install -e ".[dev]"
cd ../..

cd packages/cli
uv pip install -e ".[dev]"
cd ../..

cd packages/api
uv pip install -e ".[dev]"
cd ../..

# Set up environment file if it doesn't exist
if [ ! -f .env ]; then
  echo "Creating .env file from template..."
  if [ -f config/env.development ]; then
    cp config/env.development .env
    echo "⚠️  Please edit .env and add your API keys!"
  elif [ -f config/env.template ]; then
    cp config/env.template .env
    echo "⚠️  Please edit .env and add your API keys!"
  else
    echo "Creating basic .env file..."
    cat >.env <<'EOF'
# AI Project Analyzer Environment Configuration

# Required: Google Gemini API key
GOOGLE_API_KEY=your_gemini_api_key_here

# Optional: GitHub token for enhanced metrics
GITHUB_TOKEN=your_github_token_here

# API Configuration
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/analyzer_db
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=your_secret_key_here

# API Server Settings
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
LOG_LEVEL=INFO

# LLM Settings
DEFAULT_MODEL=gemini-2.5-flash-preview-04-17
TEMPERATURE=0.2
EOF
    echo "✅ Created .env file. Please edit it and add your API keys!"
  fi
fi

# Set up pre-commit hooks (optional)
echo ""
echo "🔍 Setting up code quality tools..."

# Create a simple pre-commit script
mkdir -p .git/hooks
cat >.git/hooks/pre-commit <<'EOF'
#!/bin/bash
# Simple pre-commit hook for code quality

echo "Running code quality checks..."

# Run ruff on Python files
echo "Checking Python code style..."
uv run ruff check packages/*/src/ --fix || exit 1
uv run ruff format packages/*/src/ || exit 1

echo "Code quality checks passed!"
EOF

chmod +x .git/hooks/pre-commit

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "🎯 Quick start commands:"
echo "  ./start.sh --dev          # Start full development environment"
echo "  ./start.sh --api-only     # Start API services only"
echo "  ./start.sh --frontend-only # Start frontend only"
echo ""
echo "📚 Package-specific commands:"
echo "  cd packages/cli && python -m src.main --help"
echo "  cd packages/api && python src/api.py"
echo "  cd packages/frontend && npm run dev"
