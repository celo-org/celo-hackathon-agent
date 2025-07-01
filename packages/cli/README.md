# AI Project Analyzer - CLI Package

Command-line interface for analyzing GitHub repositories using LLMs.

## Installation

```bash
cd packages/cli
pip install -e .
```

## Usage

### Basic Analysis

```bash
# Analyze a single repository
python -m src.main --github-urls https://github.com/owner/repo

# Analyze multiple repositories
python -m src.main --github-urls https://github.com/owner/repo1,https://github.com/owner/repo2

# Use custom prompt
python -m src.main --github-urls https://github.com/owner/repo --prompt ../../config/prompts/celo.txt
```

### Advanced Options

```bash
# Select model
python -m src.main --github-urls https://github.com/owner/repo --model gemini-2.5-pro-preview-03-25

# Adjust temperature
python -m src.main --github-urls https://github.com/owner/repo --temperature 0.7

# JSON output
python -m src.main --github-urls https://github.com/owner/repo --json

# Custom output directory
python -m src.main --github-urls https://github.com/owner/repo --output ./my-reports
```

## Features

- Batch repository analysis
- Progress tracking with rich progress bars
- Configurable output formats (Markdown/JSON)
- Custom prompt support
- Detailed logging and error handling
