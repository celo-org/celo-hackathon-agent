#!/usr/bin/env python3
"""
AI Project Analyzer - Analyze GitHub projects using LLMs
"""

import argparse
import logging
import sys
import time
from pathlib import Path

# Add packages to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.src.analyzer import AVAILABLE_MODELS, analyze_single_repository
from core.src.config import (
    get_default_log_level,
    get_default_model,
    get_default_temperature,
    setup_logging,
)
from core.src.fetcher import fetch_single_repository
from core.src.file_parser import parse_input_file
from core.src.reporter import generate_report_directory, save_single_report


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
        default="config/prompts/default.txt",
        help="Path to the prompt file (default: config/prompts/default.txt)",
    )

    parser.add_argument(
        "--output",
        type=str,
        default="reports",
        help="Directory to save reports (default: reports)",
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
        "--json",
        action="store_true",
        help="Output analysis in JSON format instead of Markdown",
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

    # Print startup information
    print("🚀 AI Project Analyzer Starting")
    print("=" * 50)
    logging.info(f"Log level: {args.log_level}")
    logging.info(f"Model: {args.model}")
    logging.info(f"Temperature: {args.temperature}")
    logging.info(f"Output directory: {args.output}")
    logging.info(f"Metrics collection: {'enabled' if not args.no_metrics else 'disabled'}")

    # Parse GitHub URLs from args or input file
    github_urls = []

    if args.github_urls:
        # Parse comma-separated list
        github_urls = [url.strip() for url in args.github_urls.split(",")]
        logging.info(f"Using GitHub URLs from command line: {len(github_urls)} repositories")
    elif args.input_file:
        # Parse from file
        print(f"📂 Parsing input file: {args.input_file}")
        logging.info(f"Parsing input file: {args.input_file}")
        try:
            github_urls = parse_input_file(args.input_file)
            print(f"✅ Found {len(github_urls)} repositories in file")
            logging.info(f"Successfully parsed {len(github_urls)} repositories from file")
            for i, url in enumerate(github_urls, 1):
                logging.debug(f"  {i}. {url}")
        except Exception as e:
            print(f"❌ Failed to parse input file: {str(e)}")
            logging.error(f"Failed to parse input file: {str(e)}")
            return 1

    if not github_urls:
        print("❌ No repositories found to analyze")
        logging.error("No repositories found to analyze")
        return 1

    # Configure metrics collection
    include_metrics = not args.no_metrics

    # Create timestamped directory for reports
    print(f"📁 Creating reports directory: {args.output}")
    report_dir = generate_report_directory(args.output)
    print(f"📁 Reports will be saved to: {report_dir}")
    logging.info(f"Reports directory created: {report_dir}")

    # Track total GitHub URLs and completed repositories
    total_repos = len(github_urls)
    completed_repos = 0
    all_analyses = {}
    all_report_paths = {}
    start_time = time.time()

    print(f"\n🔍 Starting analysis of {total_repos} repositories...")
    print("=" * 50)

    # Process each repository individually
    for index, url in enumerate(github_urls, 1):
        print(f"\n📋 [{index}/{total_repos}] Processing: {url}")
        logging.info(f"Starting analysis {index}/{total_repos}: {url}")

        # Step 1: Fetch repository content and metrics
        print("⬇️  Fetching repository content...")
        logging.info(f"Fetching repository: {url}")
        repo_name, repo_data = fetch_single_repository(
            url, include_metrics=include_metrics, github_token=args.github_token
        )

        # Skip if fetch failed completely
        if not repo_data or not repo_data["content"] or repo_data["content"].startswith("Error:"):
            print(f"❌ Failed to fetch repository: {url}")
            logging.error(f"Failed to fetch repository: {url}")
            continue

        print(f"✅ Repository fetched: {repo_name}")
        logging.info(f"Successfully fetched repository: {repo_name}")

        content_size = len(repo_data["content"])
        logging.debug(f"Repository content size: {content_size:,} characters")

        if repo_data.get("metrics"):
            logging.debug(f"GitHub metrics collected for {repo_name}")
        else:
            logging.debug(f"No GitHub metrics available for {repo_name}")

        # Step 2: Analyze repository
        print(f"🤖 Analyzing with {args.model}...")
        logging.info(f"Starting AI analysis of {repo_name}")
        code_digest = repo_data["content"]
        metrics = repo_data.get("metrics", {})

        analysis = analyze_single_repository(
            repo_name,
            code_digest,
            args.prompt,
            model_name=args.model,
            temperature=args.temperature,
            output_json=args.json,
            metrics_data=metrics,
        )

        print(f"✅ Analysis completed for: {repo_name}")
        logging.info(f"Analysis completed for: {repo_name}")

        # Step 3: Save report and update summary
        print("💾 Saving report...")
        logging.info(f"Saving report for {repo_name}")
        completed_repos += 1
        all_analyses[repo_name] = analysis

        # Save report and update summary
        report_paths = save_single_report(
            repo_name, analysis, report_dir, total_repos, completed_repos, all_analyses
        )

        # Update all report paths
        all_report_paths.update(report_paths)

        # Print progress indicator and current repository report path
        progress_percentage = (completed_repos / total_repos) * 100
        bar_length = 40
        filled_length = int(bar_length * completed_repos // total_repos)
        progress_bar = "█" * filled_length + "░" * (bar_length - filled_length)

        print(f"\n[{progress_bar}] {completed_repos}/{total_repos} ({progress_percentage:.1f}%)")
        print(f"✅ Completed analysis of: {repo_name}")
        logging.info(f"Repository {completed_repos}/{total_repos} completed: {repo_name}")

        if repo_name in report_paths:
            print(f"📄 Report: {report_paths[repo_name]}")
            logging.debug(f"Report saved: {report_paths[repo_name]}")

        # Print summary report path on first repo and on updates
        if "__summary__" in report_paths and (
            completed_repos == 1 or completed_repos == total_repos
        ):
            print(f"📊 Summary report: {report_paths['__summary__']}")
            logging.debug(f"Summary report updated: {report_paths['__summary__']}")

        # Estimate time remaining
        if completed_repos < total_repos:
            elapsed_time = time.time() - start_time
            avg_time_per_repo = elapsed_time / completed_repos
            estimated_remaining = avg_time_per_repo * (total_repos - completed_repos)
            remaining_repos = total_repos - completed_repos

            # Format the time nicely
            mins, secs = divmod(estimated_remaining, 60)
            time_str = f"{int(mins)}m {int(secs)}s"
            print(f"⏱️  Estimated time remaining: {time_str} ({remaining_repos} repos left)")
            logging.info(
                f"Progress: {completed_repos}/{total_repos} completed, {time_str} estimated remaining"
            )

    # Final stats
    print("\n🎉 Analysis Complete!")
    print("=" * 50)

    if completed_repos == 0:
        print("❌ No repositories were successfully analyzed")
        logging.error("No repositories were successfully analyzed. Exiting.")
        return 1

    print(f"✅ Successfully analyzed {completed_repos}/{total_repos} repositories")
    logging.info(f"Analysis complete: {completed_repos}/{total_repos} repositories processed")

    # Print final report paths summary
    print("\n📄 Analysis reports saved to:")
    for repo_name, path in all_report_paths.items():
        if repo_name != "__summary__":
            print(f"- {repo_name}: {path}")
            logging.debug(f"Final report: {repo_name} -> {path}")

    if "__summary__" in all_report_paths:
        print(f"\n📊 Summary report: {all_report_paths['__summary__']}")
        logging.info(f"Summary report saved: {all_report_paths['__summary__']}")

    # Print execution time
    total_time = time.time() - start_time
    mins, secs = divmod(total_time, 60)
    hours, mins = divmod(mins, 60)

    if hours > 0:
        time_str = f"{int(hours)}h {int(mins)}m {int(secs)}s"
    else:
        time_str = f"{int(mins)}m {int(secs)}s"

    print(f"\n⏱️  Total execution time: {time_str}")
    avg_time = total_time / completed_repos if completed_repos > 0 else 0
    print(f"📊 Average time per repository: {avg_time:.1f} seconds")

    logging.info(f"Execution complete. Total time: {time_str}, Average per repo: {avg_time:.1f}s")

    return 0


if __name__ == "__main__":
    sys.exit(main())
