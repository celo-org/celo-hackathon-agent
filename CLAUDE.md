# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

- Install: `uv pip install -e .`
- Run: `uv run main.py --github-urls [REPO_URL]`
- Lint: `ruff check .`
- Format: `ruff format .`

## Code Style Guidelines

- Line length: 100 characters max
- Target Python version: 3.11+
- Use type hints consistently throughout the codebase
- Prefer absolute imports
- Error handling: Use try/except blocks with specific exception types
- Logging: Use the standard logging module with appropriate levels
- Function/variable naming: Use snake_case for functions and variables
- Class naming: Use PascalCase for classes
- Constants: Use UPPER_CASE for constants
- Docstrings: Use Google style docstrings with Args and Returns sections
- Package dependencies: Defined in pyproject.toml
- Timestamp format: ISO format for machine processing, human-readable for display