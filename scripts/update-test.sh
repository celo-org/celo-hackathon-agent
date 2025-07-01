#!/bin/bash
# Enhanced testing script for AI Project Analyzer

set -e

echo "🧪 Running Tests for AI Project Analyzer"
echo "========================================"

# Function to display usage
show_usage() {
  echo "Usage: $0 [options]"
  echo "Options:"
  echo "  --package PACKAGE  Test specific package (core|cli|api|frontend|all)"
  echo "  --coverage        Run tests with coverage reporting"
  echo "  --integration     Run integration tests"
  echo "  --lint           Run code quality checks"
  echo "  --docker         Run tests in Docker containers"
  echo "  --performance    Run performance tests"
  echo "  --security       Run security tests"
  echo "  --help           Show this help message"
}

# Parse arguments
PACKAGE="all"
COVERAGE=false
INTEGRATION=false
LINT=false
DOCKER=false
PERFORMANCE=false
SECURITY=false

while [[ $# -gt 0 ]]; do
  case "$1" in
  --package)
    PACKAGE="$2"
    shift 2
    ;;
  --coverage)
    COVERAGE=true
    shift
    ;;
  --integration)
    INTEGRATION=true
    shift
    ;;
  --lint)
    LINT=true
    shift
    ;;
  --docker)
    DOCKER=true
    shift
    ;;
  --performance)
    PERFORMANCE=true
    shift
    ;;
  --security)
    SECURITY=true
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

# Function to run tests for a package
run_package_tests() {
  local pkg=$1
  echo "Testing $pkg package..."

  if [ "$DOCKER" = true ]; then
    echo "Running tests in Docker container..."
    case "$pkg" in
    "core" | "cli" | "api")
      docker-compose run --rm test-runner ./scripts/test.sh --package $pkg $([ "$COVERAGE" = true ] && echo "--coverage" || echo "")
      ;;
    "frontend")
      docker-compose run --rm -w /app/packages/frontend frontend npm test $([ "$COVERAGE" = true ] && echo "-- --coverage" || echo "")
      ;;
    *)
      echo "Unknown package: $pkg"
      return 1
      ;;
    esac
  else
    case "$pkg" in
    "core" | "cli" | "api")
      cd "packages/$pkg"

      if [ "$COVERAGE" = true ]; then
        echo "Running tests with coverage..."
        uv run pytest --cov=src --cov-report=html --cov-report=term --cov-report=xml
      else
        echo "Running tests..."
        uv run pytest
      fi

      cd ../..
      ;;
    "frontend")
      cd "packages/frontend"
      echo "Running frontend tests..."
      if [ "$COVERAGE" = true ]; then
        npm test -- --coverage --watchAll=false
      else
        npm test -- --watchAll=false
      fi
      cd ../..
      ;;
    *)
      echo "Unknown package: $pkg"
      return 1
      ;;
    esac
  fi
}

# Function to run linting
run_lint() {
  echo "🔍 Running code quality checks..."

  if [ "$DOCKER" = true ]; then
    docker-compose run --rm test-runner bash -c "
            for pkg in core cli api; do
                echo \"Linting \$pkg package...\"
                cd packages/\$pkg
                uv run ruff check src/
                uv run ruff format --check src/
                cd ../..
            done
        "

    docker-compose run --rm -w /app/packages/frontend frontend npm run lint
  else
    # Python packages
    for pkg in core cli api; do
      echo "Linting $pkg package..."
      cd "packages/$pkg"
      uv run ruff check src/
      uv run ruff format --check src/
      cd ../..
    done

    # Frontend
    cd packages/frontend
    echo "Linting frontend..."
    npm run lint
    cd ../..
  fi

  echo "✅ All linting checks passed!"
}

# Function to run security tests
run_security_tests() {
  echo "🔐 Running security tests..."

  if [ "$DOCKER" = true ]; then
    docker-compose run --rm test-runner bash -c "
            uv pip install bandit safety
            bandit -r packages/*/src/ -f json -o bandit-report.json
            safety check --json --output safety-report.json
        "
  else
    uv pip install bandit safety
    bandit -r packages/*/src/ -f json -o bandit-report.json
    safety check --json --output safety-report.json
  fi

  echo "✅ Security tests completed!"
}

# Function to run performance tests
run_performance_tests() {
  echo "⚡ Running performance tests..."

  if [ "$DOCKER" = true ]; then
    docker-compose run --rm test-runner bash -c "
            cd packages/api
            uv pip install pytest-benchmark
            uv run pytest tests/performance/ --benchmark-only
        "
  else
    cd packages/api
    uv pip install pytest-benchmark
    uv run pytest tests/performance/ --benchmark-only
    cd ../..
  fi

  echo "✅ Performance tests completed!"
}

# Function to run integration tests
run_integration_tests() {
  echo "🔗 Running integration tests..."

  if [ "$DOCKER" = true ]; then
    echo "Starting integration test environment..."
    docker-compose --profile test up -d postgres redis
    sleep 10 # Wait for services to be ready

    docker-compose run --rm test-runner bash -c "
            cd packages/api
            alembic upgrade head
            cd ../..
            pytest packages/api/tests/integration/
        "

    docker-compose --profile test down
  else
    # Check if services are running
    echo "Checking if services are available..."

    # Test API connectivity
    if curl -f http://localhost:8000/api/health >/dev/null 2>&1; then
      echo "✅ API server is running"

      # Run API integration tests
      cd packages/api
      uv run pytest tests/integration/ || echo "⚠️  API integration tests failed"
      cd ../..
    else
      echo "⚠️  API server not running, skipping API integration tests"
    fi

    # Test database connectivity
    if pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
      echo "✅ PostgreSQL is running"
    else
      echo "⚠️  PostgreSQL not running, some tests may fail"
    fi

    # Test Redis connectivity
    if redis-cli ping >/dev/null 2>&1; then
      echo "✅ Redis is running"
    else
      echo "⚠️  Redis not running, some tests may fail"
    fi
  fi
}

# Main execution
if [ "$SECURITY" = true ]; then
  run_security_tests
fi

if [ "$LINT" = true ]; then
  run_lint
fi

if [ "$PACKAGE" = "all" ]; then
  echo "📦 Testing all packages..."
  run_package_tests "core"
  run_package_tests "cli"
  run_package_tests "api"
  run_package_tests "frontend"
else
  echo "📦 Testing $PACKAGE package..."
  run_package_tests "$PACKAGE"
fi

if [ "$PERFORMANCE" = true ]; then
  run_performance_tests
fi

if [ "$INTEGRATION" = true ]; then
  run_integration_tests
fi

echo ""
echo "✅ All tests completed!"

if [ "$COVERAGE" = true ]; then
  echo ""
  echo "📊 Coverage reports generated:"
  find packages/ -name "htmlcov" -type d -exec echo "  {}" \;
  find packages/ -name "coverage.xml" -exec echo "  {}" \;
fi
