# GitHub Repository Analyzer API

This API server allows users to analyze GitHub repositories, generate detailed reports, and store them on IPFS.

## Features

- User authentication and registration
- Repository analysis using LLMs
- Report generation and storage
- IPFS integration for decentralized report storage
- RESTful API with OpenAPI documentation

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Google Gemini API key

### Environment Setup

Create a `.env` file in the project root with the following variables:

```
GOOGLE_API_KEY=your_gemini_api_key
JWT_SECRET=your_jwt_secret_key
```

### Running the API Server

1. Start the services using Docker Compose:

```bash
cd api
docker-compose up -d
```

2. Access the API documentation at http://localhost:8000/api/docs

## API Endpoints

### Authentication

- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Authenticate and get an access token
- `GET /api/auth/me` - Get current user information

### Analysis

- `POST /api/analysis/submit` - Submit GitHub repository for analysis
- `GET /api/analysis/tasks` - Get all user's analysis tasks
- `GET /api/analysis/tasks/{task_id}` - Get status of a specific analysis task
- `DELETE /api/analysis/tasks/{task_id}` - Cancel an analysis task

### Reports

- `GET /api/reports` - Get all user's reports
- `GET /api/reports/{report_id}` - Get a specific report
- `GET /api/reports/{report_id}/download` - Download report as Markdown or JSON
- `POST /api/reports/{report_id}/publish` - Publish report to IPFS

### Health

- `GET /api/health` - Get service health status
- `GET /api/health/dependencies` - Get status of all dependencies

## Development

### Project Structure

```
api/
├── app/
│   ├── db/
│   │   ├── models.py       - Database models
│   │   ├── repositories/   - Data access layer
│   │   └── session.py      - Database connection
│   ├── routers/
│   │   ├── auth.py         - Authentication endpoints
│   │   ├── analysis.py     - Analysis endpoints
│   │   ├── reports.py      - Report endpoints
│   │   └── health.py       - Health check endpoints
│   ├── schemas/
│   │   ├── user.py         - User schemas
│   │   ├── analysis.py     - Analysis schemas
│   │   └── report.py       - Report schemas
│   ├── services/
│   │   ├── auth.py         - Authentication logic
│   │   ├── analysis.py     - Analysis logic
│   │   └── ipfs.py         - IPFS integration
│   ├── config.py           - Application configuration
│   └── main.py             - FastAPI application
├── tests/                  - Test suite
├── Dockerfile              - Container definition
├── docker-compose.yml      - Service orchestration
└── requirements.txt        - Python dependencies
```

## Implementation Phases

This API is being developed in phases:

1. **Phase 1 (Current)**: Basic API structure, authentication, and database models
2. **Phase 2**: Background tasks, repository analysis, and report generation
3. **Phase 3**: IPFS integration
4. **Phase 4**: Testing, optimization, and deployment