# DevRel Agent Makefile
.PHONY: help setup run run-interactive run-excel run-url clean lint test

# Default target
help:
	@echo "DevRel Agent CLI Makefile"
	@echo ""
	@echo "Available commands:"
	@echo "  make setup            - Install required dependencies"
	@echo "  make run              - Run CLI in interactive mode"
	@echo "  make run-excel FILE=sample_projects.xlsx [VERBOSE=1]"
	@echo "                          - Run with Excel file"
	@echo "  make run-url URL=\"https://github.com/user/repo\" [NAME=\"Project Name\"] [VERBOSE=1]"
	@echo "                          - Run with direct GitHub URL"
	@echo "  make clean            - Remove generated reports and cache files"
	@echo "  make lint             - Check code style"
	@echo "  make test             - Run tests"

# Install dependencies
setup:
	@echo "Installing dependencies..."
	pip install -r requirements.txt
	@echo "Setup complete."

# Run in interactive mode
run:
	@echo "Starting DevRel Agent in interactive mode..."
	./devrel-agent.py

# Run with Excel file
run-excel:
	@if [ -z "$(FILE)" ]; then \
		echo "Error: You must specify an Excel file with FILE=path/to/excel.xlsx"; \
		exit 1; \
	fi
	@echo "Starting DevRel Agent with Excel file: $(FILE)"
	@if [ "$(VERBOSE)" = "1" ]; then \
		./devrel-agent.py --non-interactive --excel "$(FILE)" --verbose; \
	else \
		./devrel-agent.py --non-interactive --excel "$(FILE)"; \
	fi

# Run with GitHub URL
run-url:
	@if [ -z "$(URL)" ]; then \
		echo "Error: You must specify a GitHub URL with URL=https://github.com/user/repo"; \
		exit 1; \
	fi
	@echo "Starting DevRel Agent with GitHub URL: $(URL)"
	@if [ -n "$(NAME)" ] && [ "$(VERBOSE)" = "1" ]; then \
		./devrel-agent.py --non-interactive --urls "$(URL)" --project-name "$(NAME)" --verbose; \
	elif [ -n "$(NAME)" ]; then \
		./devrel-agent.py --non-interactive --urls "$(URL)" --project-name "$(NAME)"; \
	elif [ "$(VERBOSE)" = "1" ]; then \
		./devrel-agent.py --non-interactive --urls "$(URL)" --verbose; \
	else \
		./devrel-agent.py --non-interactive --urls "$(URL)"; \
	fi

# Remove generated files
clean:
	@echo "Cleaning up generated files..."
	rm -rf reports/*
	rm -f *.log
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "Cleanup complete."

# Run linting
lint:
	@echo "Running linter..."
	@if command -v flake8 > /dev/null; then \
		flake8 .; \
	else \
		echo "flake8 not installed. Run 'pip install flake8' to install."; \
		exit 1; \
	fi

# Run tests
test:
	@echo "Running tests..."
	@if [ -d "tests" ]; then \
		python -m pytest tests; \
	else \
		echo "No tests directory found."; \
	fi