#!/bin/bash
# Docker development convenience script

set -e

echo "🐳 AI Project Analyzer - Docker Development Helper"
echo "================================================="

# Function to display usage
show_usage() {
  echo "Usage: $0 [command] [options]"
  echo ""
  echo "Commands:"
  echo "  up              Start all development services"
  echo "  down            Stop all services"
  echo "  restart         Restart all services"
  echo "  rebuild         Rebuild and restart services"
  echo "  logs [service]  Show logs for all services or specific service"
  echo "  shell [service] Open shell in service container"
  echo "  test            Run tests in container"
  echo "  admin           Start admin services (pgAdmin, Redis Commander)"
  echo "  clean           Clean up all containers, volumes, and images"
  echo "  status          Show status of all services"
  echo ""
  echo "Options:"
  echo "  --no-deps       Don't start dependent services"
  echo "  --build         Force rebuild before starting"
  echo "  --detach        Run in background (default)"
  echo "  --help          Show this help message"
}

# Parse arguments
COMMAND=""
SERVICE=""
BUILD_FLAG=""
DETACH_FLAG="-d"
NO_DEPS=""

while [[ $# -gt 0 ]]; do
  case "$1" in
  up | down | restart | rebuild | logs | shell | test | admin | clean | status)
    COMMAND="$1"
    shift
    ;;
  --no-deps)
    NO_DEPS="--no-deps"
    shift
    ;;
  --build)
    BUILD_FLAG="--build"
    shift
    ;;
  --detach)
    DETACH_FLAG="-d"
    shift
    ;;
  --no-detach)
    DETACH_FLAG=""
    shift
    ;;
  --help)
    show_usage
    exit 0
    ;;
  *)
    if [ -z "$SERVICE" ]; then
      SERVICE="$1"
    fi
    shift
    ;;
  esac
done

# Set default command
if [ -z "$COMMAND" ]; then
  COMMAND="up"
fi

# Load environment variables
if [ -f .env ]; then
  export $(cat .env | grep -v '^#' | xargs)
else
  echo "⚠️  .env file not found. Creating from template..."
  cp config/env.development .env
  echo "✅ Please edit .env and add your API keys, then run this script again."
  exit 1
fi

# Execute commands
case "$COMMAND" in
"up")
  echo "🚀 Starting development services..."
  docker-compose up $BUILD_FLAG $DETACH_FLAG $NO_DEPS

  if [ "$DETACH_FLAG" = "-d" ]; then
    echo ""
    echo "✅ Services started in background!"
    echo ""
    echo "🌐 Access URLs:"
    echo "  Frontend:    http://localhost:5173"
    echo "  API:         http://localhost:8000"
    echo "  API Docs:    http://localhost:8000/docs"
    echo ""
    echo "💡 Useful commands:"
    echo "  ./scripts/docker-dev.sh logs     # View logs"
    echo "  ./scripts/docker-dev.sh admin    # Start admin tools"
    echo "  ./scripts/docker-dev.sh status   # Check service status"
  fi
  ;;

"down")
  echo "🛑 Stopping services..."
  docker-compose down
  echo "✅ Services stopped"
  ;;

"restart")
  echo "🔄 Restarting services..."
  docker-compose restart $SERVICE
  echo "✅ Services restarted"
  ;;

"rebuild")
  echo "🔨 Rebuilding and restarting services..."
  docker-compose down
  docker-compose build --no-cache
  docker-compose up $DETACH_FLAG
  echo "✅ Services rebuilt and restarted"
  ;;

"logs")
  if [ -n "$SERVICE" ]; then
    echo "📋 Showing logs for $SERVICE..."
    docker-compose logs -f $SERVICE
  else
    echo "📋 Showing logs for all services..."
    docker-compose logs -f
  fi
  ;;

"shell")
  if [ -z "$SERVICE" ]; then
    SERVICE="api"
  fi
  echo "🐚 Opening shell in $SERVICE container..."
  docker-compose exec $SERVICE /bin/bash
  ;;

"test")
  echo "🧪 Running tests in container..."
  docker-compose --profile test run --rm test-runner
  ;;

"admin")
  echo "🔧 Starting admin services..."
  docker-compose --profile admin up -d postgres-admin redis-commander
  echo ""
  echo "✅ Admin services started!"
  echo ""
  echo "🔧 Admin URLs:"
  echo "  pgAdmin:         http://localhost:5050"
  echo "  Redis Commander: http://localhost:8081"
  echo ""
  echo "🔐 Admin Credentials:"
  echo "  pgAdmin: admin@analyzer.com / admin"
  ;;

"clean")
  echo "🧹 Cleaning up Docker resources..."
  read -p "This will remove all containers, volumes, and images. Are you sure? (y/N): " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker-compose down -v --remove-orphans
    docker system prune -f
    docker volume prune -f
    echo "✅ Cleanup completed"
  else
    echo "❌ Cleanup cancelled"
  fi
  ;;

"status")
  echo "📊 Service Status:"
  echo "=================="
  docker-compose ps
  echo ""
  echo "💾 Volume Usage:"
  echo "==============="
  docker volume ls | grep analyzer
  echo ""
  echo "🌐 Network Info:"
  echo "==============="
  docker network ls | grep analyzer
  ;;

*)
  echo "❌ Unknown command: $COMMAND"
  show_usage
  exit 1
  ;;
esac
