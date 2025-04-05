#!/usr/bin/env python3
"""
AI Project Analyzer - Analyze GitHub projects using LLMs
"""

import sys
import argparse
import logging
import os

from src.config import (
    setup_logging,
    get_default_model,
    get_default_temperature,
    get_default_log_level,
)
from src.fetcher import fetch_repositories
from src.analyzer import analyze_repositories, AVAILABLE_MODELS
from src.reporter import save_reports
from src.file_parser import parse_input_file


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Analyze GitHub repositories using LLMs")

    # Create a group for input sources to handle mutual exclusivity
    input_group = parser.add_mutually_exclusive_group(required=True)

    input_group.add_argument(
        "--github-urls",
        type=str,
        help="Comma-separated list of GitHub repository URLs",
    )

    input_group.add_argument(
        "--input-file",
        type=str,
        help="Path to Excel (.xlsx) or CSV file containing GitHub repository URLs",
    )

    parser.add_argument(
        "--prompt",
        type=str,
        default="prompts/default.txt",
        help="Path to the prompt file (default: prompts/default.txt)",
    )

    parser.add_argument(
        "--output", type=str, default="reports", help="Directory to save reports (default: reports)"
    )

    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=get_default_log_level(),
        help=f"Set the logging level (default: {get_default_log_level()})",
    )

    # Add model selection
    parser.add_argument(
        "--model",
        type=str,
        choices=list(AVAILABLE_MODELS.keys()),
        default=get_default_model(),
        help=f"Gemini model to use for analysis (default: {get_default_model()})",
    )

    # Add temperature control
    parser.add_argument(
        "--temperature",
        type=float,
        default=get_default_temperature(),
        help=f"Temperature for generation (0.0-1.0, lower is more deterministic, default: {get_default_temperature()})",
    )

    # Add JSON output option
    parser.add_argument(
        "--json", action="store_true", help="Output analysis in JSON format instead of Markdown"
    )

    # Add GitHub token option
    parser.add_argument(
        "--github-token",
        type=str,
        help="GitHub personal access token for API requests (can also be set with GITHUB_TOKEN env var)",
    )

    # Add option to disable metrics
    parser.add_argument(
        "--no-metrics", action="store_true", help="Disable GitHub metrics collection"
    )

    return parser.parse_args()


def main():
    """Main entry point for the application."""
    args = parse_args()

    # Setup logging
    setup_logging(args.log_level)

    # Parse GitHub URLs from args or input file
    github_urls = []

    if args.github_urls:
        # Parse comma-separated list
        github_urls = [url.strip() for url in args.github_urls.split(",")]
        logging.info(f"Found {len(github_urls)} GitHub URLs from command line arguments")
    elif args.input_file:
        # Parse from file
        logging.info(f"Parsing GitHub URLs from file: {args.input_file}")
        try:
            github_urls = parse_input_file(args.input_file)
            logging.info(f"Found {len(github_urls)} GitHub URLs from input file")
        except Exception as e:
            logging.error(f"Failed to parse input file: {str(e)}")
            return 1

    # Log start of analysis with selected model
    logging.info(f"Starting analysis with model: {args.model}, temperature: {args.temperature}")
    if args.json:
        logging.info("Using JSON output format")

    # Fetch repository data
    logging.info(f"Fetching {len(github_urls)} repositories...")
    include_metrics = not args.no_metrics

    if include_metrics:
        logging.info("GitHub metrics collection is enabled")
    else:
        logging.info("GitHub metrics collection is disabled")

    repo_data = fetch_repositories(
        github_urls, include_metrics=include_metrics, github_token=args.github_token
    )

    if not repo_data:
        logging.error("No repositories were successfully fetched. Exiting.")
        return 1

    # Extract content from repo data
    repo_contents = {}
    repo_metrics = {}

    for repo_name, data in repo_data.items():
        repo_contents[repo_name] = data["content"]
        if "metrics" in data and data["metrics"]:
            repo_metrics[repo_name] = data["metrics"]

    # Analyze repositories
    logging.info("Analyzing repositories...")
    analyses = analyze_repositories(
        repo_contents,
        args.prompt,
        model_name=args.model,
        temperature=args.temperature,
        output_json=args.json,
        metrics_data=repo_metrics,  # Pass metrics to analyzer
    )

    # Save reports
    logging.info("Saving reports...")
    report_paths = save_reports(analyses, args.output)

    # Print report paths
    print("\nAnalysis reports saved to:")
    for repo_name, path in report_paths.items():
        if repo_name != "__summary__":
            print(f"- {repo_name}: {path}")

    if "__summary__" in report_paths:
        print(f"\nSummary report: {report_paths['__summary__']}")

    logging.info("Analysis complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
