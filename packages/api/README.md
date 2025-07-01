# AI Project Analyzer - API Package

REST API server for analyzing GitHub repositories with user management and background processing.

## Features

- RESTful API endpoints
- User authentication and authorization
- Background task processing
- PostgreSQL database storage
- Redis-based job queue
- IPFS integration for report storage

## Installation

```bash
cd packages/api
pip install -e .
```

## Development Setup

1. Start required services:

```bash
# Start PostgreSQL and Redis
docker-compose -f ../../config/docker-compose.yml up -d
```

2. Run database migrations:

```bash
cd packages/api
alembic upgrade head
```

3. Start the API server:

```bash
python src/api.py
```

4. Start the worker process:

```bash
python src/worker.py
```

## API Endpoints

### Authentication

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout

### Analysis

- `POST /api/analysis/submit` - Submit repository for analysis
- `GET /api/analysis/tasks` - Get user's analysis tasks
- `GET /api/analysis/tasks/{task_id}` - Get specific task status
- `DELETE /api/analysis/tasks/{task_id}/cancel` - Cancel analysis task

### Reports

- `GET /api/reports` - Get user's reports
- `GET /api/reports/{report_id}` - Get specific report
- `DELETE /api/reports/{report_id}` - Delete report

## Configuration

Environment variables:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `JWT_SECRET`: JWT signing secret
- `GOOGLE_API_KEY`: Google Gemini API key
- `GITHUB_TOKEN`: GitHub API token
