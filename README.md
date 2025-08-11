# 🤖 AI Project Analyzer

> **Enterprise-grade monorepo for analyzing GitHub repositories using Large Language Models**

A comprehensive AI-powered analysis platform that evaluates GitHub repositories across multiple dimensions including code quality, architecture, security, and project health using Google Gemini and other LLMs.

## 🏗️ **Monorepo Architecture**

This project is organized as a modern monorepo with four main packages:

```
ai-project-analyzer/
├── packages/
│   ├── core/           # 🧠 Business logic & AI analysis
│   ├── cli/            # 💻 Command-line interface
│   ├── api/            # 🌐 REST API server
│   └── frontend/       # ⚛️  React web application
├── config/             # ⚙️  Shared configuration
├── docker/             # 🐳 Container configurations
├── scripts/            # 🔧 Build & development scripts
└── docs/               # 📚 Documentation
```

### 📦 **Package Overview**

| Package      | Description                                     | Technology                      | Port/Usage        |
| ------------ | ----------------------------------------------- | ------------------------------- | ----------------- |
| **Core**     | AI analysis engine, GitHub integration, metrics | Python 3.11+, LangChain, Gemini | Library           |
| **CLI**      | Command-line tool for repository analysis       | Python, Typer, Rich             | `analyze` command |
| **API**      | REST API with authentication, job queues        | FastAPI, PostgreSQL, Redis      | Port 8000         |
| **Frontend** | Web interface with reports dashboard            | React, TypeScript, Tailwind     | Port 3000         |

## 🚀 **Quick Start**

### **Prerequisites**

- **Python 3.11+** (recommend using [uv](https://github.com/astral-sh/uv))
- **Node.js 18+** (for frontend)
- **Docker & Docker Compose** (for full stack)

### **1. Clone & Setup**

```bash
git clone <repository-url>
cd ai-project-analyzer

# Install Python dependencies (workspace-level)
uv sync --dev

# Install frontend dependencies
cd packages/frontend && npm install
```

### **2. Environment Configuration**

```bash
# Copy environment template
cp config/env.template .env

# Edit .env with your configuration:
# GOOGLE_API_KEY=your_gemini_api_key_here
# DATABASE_URL=postgresql://localhost/ai_analyzer
# REDIS_URL=redis://localhost:6379/0
```

### **3. Quick Analysis (CLI)**

```bash
# Analyze a single repository
uv run python packages/cli/src/main.py analyze https://github.com/user/repo

# Analyze multiple repositories
uv run python packages/cli/src/main.py batch-analyze repos.txt

# Use different models
uv run python packages/cli/src/main.py analyze --model gemini-2.5-pro-preview-03-25 <repo-url>
```

### **4. Full Stack Development**

```bash
# Start all services with Docker
docker-compose up -d

# Or run services individually:

# 1. Start API server (Terminal 1)
cd packages/api && uvicorn app.main:app --reload

# 2. Start frontend (Terminal 2)
cd packages/frontend && npm run dev

# 3. Start background workers (Terminal 3)
cd packages/api && python -m app.worker
```

## 💻 **Development Setup**

### **VS Code Integration**

This monorepo includes complete VS Code configuration:

- **IntelliSense** for all packages
- **Debug configurations** for CLI, API, and tests
- **Task runners** for linting, testing, building
- **Recommended extensions** for Python, React, Docker

Just open the workspace in VS Code and install recommended extensions!

### **Development Commands**

```bash
# Install all dependencies
uv sync --dev

# Run tests across all packages
pytest packages/ -v

# Lint and format Python code
ruff check packages/
ruff format packages/

# Build frontend
cd packages/frontend && npm run build

# Run with Docker (recommended for API development)
docker-compose up -d postgres redis  # Start dependencies
cd packages/api && uvicorn app.main:app --reload
```

## 📊 **Usage Examples**

### **CLI Analysis**

```bash
# Basic analysis
uv run python packages/cli/src/main.py analyze https://github.com/microsoft/vscode

# Celo-specific analysis
uv run python packages/cli/src/main.py analyze --prompt celo https://github.com/celo-org/celo-monorepo

# Batch analysis with custom output
uv run python packages/cli/src/main.py batch-analyze \
  --input repos.txt \
  --output ./reports \
  --model gemini-2.5-flash
```

### **API Usage**

```bash
# Start analysis job
curl -X POST "http://localhost:8000/api/v1/analysis" \
  -H "Content-Type: application/json" \
  -d '{"github_url": "https://github.com/user/repo", "analysis_type": "deep"}'

# Get report
curl "http://localhost:8000/api/v1/reports/{report_id}"

# List user reports
curl "http://localhost:8000/api/v1/reports" \
  -H "Authorization: Bearer <your_token>"
```

### **Programmatic Usage**

```python
from core.src.analyzer import analyze_single_repository
from core.src.fetcher import fetch_single_repository

# Fetch repository content
repo_name, digest = fetch_single_repository("https://github.com/user/repo")

# Analyze with AI
analysis = analyze_single_repository(
    repo_name=repo_name,
    code_digest=digest,
    prompt_path="config/prompts/default.txt",
    model_name="gemini-2.5-flash"
)

print(analysis)
```

## 🛠️ **Configuration**

### **Environment Variables**

| Variable         | Description           | Default                              | Required |
| ---------------- | --------------------- | ------------------------------------ | -------- |
| `GOOGLE_API_KEY` | Gemini API key        | -                                    | ✅       |
| `DATABASE_URL`   | PostgreSQL connection | `postgresql://localhost/ai_analyzer` | API only |
| `REDIS_URL`      | Redis connection      | `redis://localhost:6379/0`           | API only |
| `LOG_LEVEL`      | Logging level         | `INFO`                               | ❌       |

### **Analysis Prompts**

- `config/prompts/default.txt` - General repository analysis
- `config/prompts/celo.txt` - Celo blockchain project analysis
- `config/prompts/report-template.txt` - Report formatting template

### **Model Configuration**

| Model                          | Best For         | Speed   | Quality    |
| ------------------------------ | ---------------- | ------- | ---------- |
| `gemini-2.5-flash`             | General analysis | ⚡ Fast | ⭐⭐⭐     |
| `gemini-2.5-pro-preview-03-25` | Deep analysis    | 🐌 Slow | ⭐⭐⭐⭐⭐ |

## 🧪 **Testing**

```bash
# Run all tests
pytest packages/ -v

# Test specific package
pytest packages/core/ -v

# Test with coverage
pytest packages/ --cov=packages --cov-report=html

# Integration tests (requires Docker)
docker-compose up -d postgres redis
pytest packages/api/tests/integration/ -v
```

## 📈 **Monitoring & Observability**

The production setup includes comprehensive monitoring:

- **Prometheus** metrics collection
- **Grafana** dashboards and alerting
- **Loki** log aggregation with Promtail
- **Health checks** for all services

```bash
# Start monitoring stack
docker-compose -f docker-compose.prod.yml up -d

# Access dashboards
open http://localhost:3000  # Grafana (admin/admin)
open http://localhost:9090  # Prometheus
```

## 🚢 **Deployment**

### **Production Deployment**

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy with monitoring
docker-compose -f docker-compose.prod.yml up -d

# Check deployment health
curl http://localhost/health
```

### **Cloud Deployment**

See `docs/DEPLOYMENT.md` for detailed cloud deployment guides:

- AWS ECS/EKS deployment
- Google Cloud Run deployment
- Azure Container Instances

## 📚 **Documentation**

- **[Contributing Guide](docs/CONTRIBUTING.md)** - Development workflow, coding standards
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment instructions
- **[API Documentation](http://localhost:8000/docs)** - Interactive OpenAPI docs (when API is running)
- **[CHANGELOG](CHANGELOG.md)** - Version history and changes

## 🤝 **Contributing**

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Make** your changes with tests
4. **Run** quality checks: `ruff check packages/ && pytest packages/`
5. **Commit** using conventional commits (`git commit -m 'feat: add amazing feature'`)
6. **Push** and create a **Pull Request**

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for detailed guidelines.

## 📄 **License**

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

## 🌟 **Acknowledgments**

- **Google Gemini** for advanced language model capabilities
- **LangChain** for LLM integration framework
- **FastAPI** for high-performance API development
- **React & shadcn/ui** for modern frontend experience

---

**Built with ❤️ for the developer community**
