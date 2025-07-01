# AI Project Analyzer - Core Package

This package contains the core business logic for analyzing GitHub repositories using LLMs.

## Components

- **analyzer.py**: Main analysis engine using LangChain and Google Gemini
- **fetcher.py**: Repository content fetching using gitingest
- **metrics.py**: GitHub metrics collection and analysis
- **reporter.py**: Report generation and formatting
- **config.py**: Configuration management
- **file_parser.py**: File parsing and validation utilities

## Features

- Repository analysis using multiple LLM models
- GitHub metrics integration
- Standardized scoring system
- Configurable prompt templates
- Report generation in multiple formats

## Usage

This package is designed to be used by other packages in the monorepo:

```python
from core.src.analyzer import analyze_single_repository
from core.src.fetcher import fetch_single_repository
```

## Configuration

The core package uses environment variables for configuration:

- `GOOGLE_API_KEY`: Google Gemini API key
- `GITHUB_TOKEN`: GitHub API token (optional)
- `DEFAULT_MODEL`: Default LLM model to use
- `TEMPERATURE`: Generation temperature (0.0-1.0)
