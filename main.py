#!/usr/bin/env python3
"""
AI Project Analyzer - Analyze GitHub projects using LLMs
"""
import sys
import argparse
import logging
from typing import List, Optional

from src.config import setup_logging, get_default_model, get_default_temperature, get_default_log_level
from src.fetcher import fetch_repositories
from src.analyzer import analyze_repositories, AVAILABLE_MODELS
from src.reporter import save_reports


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Analyze GitHub repositories using LLMs")
    
    parser.add_argument(
        "--github-urls", 
        type=str, 
        required=True,
        help="Comma-separated list of GitHub repository URLs"
    )
    
    parser.add_argument(
        "--prompt", 
        type=str, 
        default="prompts/default.txt",
        help="Path to the prompt file (default: prompts/default.txt)"
    )
    
    parser.add_argument(
        "--output", 
        type=str, 
        default="reports",
        help="Directory to save reports (default: reports)"
    )
    
    parser.add_argument(
        "--log-level", 
        type=str, 
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=get_default_log_level(),
        help=f"Set the logging level (default: {get_default_log_level()})"
    )
    
    # Add model selection
    parser.add_argument(
        "--model", 
        type=str, 
        choices=list(AVAILABLE_MODELS.keys()),
        default=get_default_model(),
        help=f"Gemini model to use for analysis (default: {get_default_model()})"
    )
    
    # Add temperature control
    parser.add_argument(
        "--temperature", 
        type=float, 
        default=get_default_temperature(),
        help=f"Temperature for generation (0.0-1.0, lower is more deterministic, default: {get_default_temperature()})"
    )
    
    # Add JSON output option
    parser.add_argument(
        "--json", 
        action="store_true",
        help="Output analysis in JSON format instead of Markdown"
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the application."""
    args = parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Parse GitHub URLs
    github_urls = [url.strip() for url in args.github_urls.split(",")]
    
    # Log start of analysis with selected model
    logging.info(f"Starting analysis with model: {args.model}, temperature: {args.temperature}")
    if args.json:
        logging.info("Using JSON output format")
    
    # Fetch repository digests
    logging.info(f"Fetching {len(github_urls)} repositories...")
    repo_digests = fetch_repositories(github_urls)
    
    if not repo_digests:
        logging.error("No repositories were successfully fetched. Exiting.")
        return 1
    
    # Analyze repositories
    logging.info("Analyzing repositories...")
    analyses = analyze_repositories(
        repo_digests, 
        args.prompt,
        model_name=args.model,
        temperature=args.temperature,
        output_json=args.json
    )
    
    # Save reports
    logging.info("Saving reports...")
    report_paths = save_reports(analyses, args.output)
    
    # Print report paths
    print("\nAnalysis reports saved to:")
    for repo_name, path in report_paths.items():
        print(f"- {repo_name}: {path}")
    
    logging.info("Analysis complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())