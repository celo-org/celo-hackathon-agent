# AI Project Analyzer

A tool for analyzing GitHub repositories using LLMs.

## Features

- Analyze multiple GitHub repositories at once
- Use custom prompts for different types of analyses
- Generate detailed project analysis reports in Markdown or JSON
- Configurable model selection and parameters
- Interactive progress tracking
- Automatic retries for API failures
- Built with LangChain and Google Gemini

## Components

### CLI Tool

The original command-line interface for analyzing repositories.

### API Server (New!)

The new RESTful API server with user accounts, background processing, and IPFS integration:

- User authentication and management
- Repository analysis via API endpoints
- Report storage in PostgreSQL and IPFS
- Async processing with background workers

[Learn more about the API Server](api/README.md)

## CLI Installation

```bash
# Clone the repository
git clone <repository-url>
cd ai-project-analyzer

# Install dependencies (using uv)
uv pip install -e .
```

## API Installation

```bash
# Install dependencies
uv pip install -e .

# Start the Redis server (required for background processing)
docker run -d -p 6379:6379 --name redis-server redis

# Start PostgreSQL (required for database)
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres -e POSTGRES_USER=postgres -e POSTGRES_DB=analyzer_db --name postgres-server postgres

# Start the API server and worker
./start.sh

# API will be available at http://localhost:8000
# API documentation at http://localhost:8000/docs
```

### API Components

The API server consists of these components:

1. **API Server**: Handles HTTP requests and responses using FastAPI
2. **Worker Process**: Processes repository analysis tasks in the background
3. **Redis Server**: Used for the background job queue
4. **PostgreSQL Database**: Stores users, analysis tasks, and reports

You can start these components individually:

```bash
# Start only the API server
./start.sh --api-only

# Start only the worker process
./start.sh --worker-only
```

## Configuration

Copy the `.env.template` file to `.env` and fill in your API key:

```bash
cp .env.template .env
# Edit .env with your preferred text editor
```

Required configuration:

```
# LLM settings
GOOGLE_API_KEY=your_gemini_api_key_here

# For API server
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/analyzer_db
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=your_secret_key_here
```

Optional configuration:

```
# API server settings
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False

# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO

# Default model to use
DEFAULT_MODEL=gemini-2.5-pro-preview-03-25

# Temperature setting (0.0-1.0)
TEMPERATURE=0.2

# GitHub settings
GITHUB_TOKEN=your_github_token_here
```

These environment variables can also be set directly in your shell environment.

## CLI Usage

```bash
# Basic usage
uv run main.py --github-urls github.com/celo-org/celo-composer

# Analyze multiple repositories
uv run main.py --github-urls github.com/celo-org/celo-composer,github.com/celo-org/celo-monorepo

# Use a custom prompt
uv run main.py --github-urls github.com/celo-org/celo-composer --prompt prompts/celo.txt

# Select a different model
uv run main.py --github-urls github.com/celo-org/celo-composer --model gemini-1.5-pro

# Adjust generation temperature (0.0-1.0)
uv run main.py --github-urls github.com/celo-org/celo-composer --temperature 0.7

# Output in JSON format
uv run main.py --github-urls github.com/celo-org/celo-composer --json

# Set logging level
uv run main.py --github-urls github.com/celo-org/celo-composer --log-level DEBUG

# Specify output directory
uv run main.py --github-urls github.com/celo-org/celo-composer --output ./my-reports
```

## Available Models

- `gemini-2.5-pro-preview-03-25`: Advanced model with enhanced capabilities and performance

## Custom Prompts and Scoring

You can create custom prompts in the `prompts/` directory. See the existing files for examples.

### Included Prompts and Templates

The tool comes with:

- `prompts/default.txt`: General project analysis prompt
- `prompts/celo.txt`: Specialized prompt for Celo ecosystem projects
- `prompts/report-template.txt`: Template for structuring analysis reports

### Standardized Scoring Criteria

All analyses include scores for these standard criteria:

1. **Security** (0-100)

   - Authentication & authorization
   - Data validation
   - Vulnerability prevention

2. **Functionality & Correctness** (0-100)

   - Core functionality implementation
   - Error handling
   - Edge case management

3. **Readability & Understandability** (0-100)

   - Code style consistency
   - Documentation quality
   - Naming conventions

4. **Dependencies & Setup** (0-100)

   - Dependencies management
   - Installation process
   - Configuration approach

5. **Evidence of Technical Usage** (0-100)
   - Technology-specific implementation
   - Adherence to best practices
   - Integration quality

### Creating Custom Prompts

To create your own custom prompt:

1. Create a new text file in the `prompts/` directory
2. Include scoring criteria following the standard template
3. Add specific sections relevant to your technology
4. Run the tool with `--prompt prompts/your-prompt.txt`

For technology-specific prompts, be sure to include a detailed "Evidence of Usage" section that explains what indicators the LLM should look for to verify the technology is being used correctly.

## Output Formats

- **Markdown** (default): Human-readable reports with structured sections
- **JSON**: Machine-readable structured data (use the `--json` flag)
- **Summary Report**: Automatically generated when analyzing multiple repositories

### Report Organization

Reports are organized in a timestamp-based directory structure:

```
reports/
└── MM-DD-YYYY-HHMM/
    ├── celo-org-celo-composer-analysis.md
    ├── celo-org-celo-monorepo-analysis.md
    └── summary-report.md
```

### Summary Reports

When analyzing multiple repositories, a summary report is automatically generated with:

- Comparison table of all repository scores
- Average scores across all analyzed repositories
- Links to individual reports

## License

MIT