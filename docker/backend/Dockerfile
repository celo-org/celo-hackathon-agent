# ===============================
# AI Project Analyzer - Backend Services
# Unified Docker Image for API and Worker
# ===============================

# Use official Python runtime as base image
FROM python:3.11-slim-bullseye AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    postgresql-client \
    redis-tools &&
    rm -rf /var/lib/apt/lists/*

# Install uv for fast Python package management
RUN pip install uv

# Set working directory
WORKDIR /app

# ===============================
# Build stage
# ===============================
FROM base AS builder

# Copy package files first (for better caching)
COPY packages/core/pyproject.toml packages/core/
COPY packages/api/pyproject.toml packages/api/
COPY packages/cli/pyproject.toml packages/cli/

# Copy source code
COPY packages/core/src/ packages/core/src/
COPY packages/api/app/ packages/api/app/
COPY packages/api/src/ packages/api/src/
COPY packages/api/alembic/ packages/api/alembic/
COPY packages/api/alembic.ini packages/api/
COPY packages/cli/src/ packages/cli/src/

# Copy shared configuration
COPY config/ config/

# Install Python dependencies
RUN cd packages/core && uv pip install --system -e .
RUN cd packages/cli && uv pip install --system -e .
RUN cd packages/api && uv pip install --system -e .

# ===============================
# Development stage
# ===============================
FROM base AS development

# Copy everything for development (includes hot reload)
COPY . /app/

# Install all packages in development mode
RUN cd packages/core && uv pip install --system -e .
RUN cd packages/cli && uv pip install --system -e .
RUN cd packages/api && uv pip install --system -e .

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose ports
EXPOSE 8000

# Health check for API service
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Default command (will be overridden in docker-compose)
CMD ["python", "packages/api/src/api.py"]

# ===============================
# Production stage
# ===============================
FROM base AS production

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy installed packages and code from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY --from=builder /app/ /app/

# Create necessary directories
RUN mkdir -p /app/logs /app/data && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check for API service
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Default command (will be overridden in docker-compose)
CMD ["python", "packages/api/src/api.py"]
