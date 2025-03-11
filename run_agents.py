#!/usr/bin/env python3
"""
Celo Hackathon Analyzer with Tool-Calling Agents and Parallel Execution

This script uses multiple specialized LangChain agents with parallel execution
to analyze GitHub repositories for code quality and Celo blockchain integration.
"""

import os
import json
import time
import logging
import sys
import argparse
import multiprocessing
import traceback
from pathlib import Path
from dotenv import load_dotenv

from src.agents.orchestrator import AnalysisOrchestrator
from src.utils.spinner import Spinner
from src.models.config import Config

# Set up logging
file_handler = logging.FileHandler("agents_analysis.log")
file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
)
file_handler.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter("%(message)s"))
console_handler.setLevel(logging.ERROR)  # Only show errors in console by default

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

# Configure our own logger
logger = logging.getLogger("celo-agents")
logger.setLevel(logging.INFO)

# Suppress logging from other libraries
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("anthropic").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("langchain").setLevel(logging.WARNING)

# Load environment variables from .env file
load_dotenv()


def main():
    """Main function to run the analysis."""
    # Colors for styling
    colors = {
        "reset": "\033[0m",
        "bold": "\033[1m",
        "green": "\033[92m",
        "blue": "\033[94m",
        "cyan": "\033[96m",
        "yellow": "\033[93m",
        "magenta": "\033[95m",
        "red": "\033[91m",
    }

    # Show a banner
    banner = f"""
{colors['cyan']}╔══════════════════════════════════════════════════════════════════════════╗
║ {colors['yellow']}CELO HACKATHON PROJECT ANALYZER - AI AGENTS WITH PARALLEL EXECUTION{colors['cyan']}     ║
╚══════════════════════════════════════════════════════════════════════════╝{colors['reset']}

{colors['bold']}This tool uses specialized AI agents to analyze GitHub repositories for
code quality and Celo blockchain integration, with parallel execution support.{colors['reset']}
"""
    print(banner)

    # Setup argument parser
    parser = argparse.ArgumentParser(
        description="Analyze GitHub projects using LangChain agents with parallel execution"
    )
    parser.add_argument(
        "--excel",
        help="Path to Excel file containing project data",
        default="sample_projects.xlsx",
    )
    parser.add_argument(
        "--config", default="config.json", help="Path to configuration file"
    )
    parser.add_argument("--output", default="reports", help="Directory to save reports")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument(
        "--single", help="Analyze a single repository URL", default=None
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=0,
        help="Maximum number of parallel workers (default: CPU count)",
    )
    args = parser.parse_args()

    # Set logging level based on verbosity
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        console_handler.setLevel(logging.INFO)
        logger.debug("Verbose logging enabled")

    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(f"{colors['red']}⚠️ Error: No Anthropic API key found.{colors['reset']}")
        print(
            "Please set ANTHROPIC_API_KEY environment variable or add it to .env file."
        )
        return 1

    # Determine optimal number of workers
    if args.workers <= 0:
        # Use CPU count, but cap at a reasonable maximum
        workers = min(multiprocessing.cpu_count(), 4)
    else:
        workers = args.workers

    # Print startup information
    print(f"{colors['bold']}Configuration:{colors['reset']}")
    print(f"  {colors['cyan']}📊 Input:{colors['reset']} {args.excel}")
    print(f"  {colors['cyan']}⚙️  Config:{colors['reset']} {args.config}")
    print(f"  {colors['cyan']}📁 Output:{colors['reset']} {args.output}")

    if args.single:
        print(
            f"  {colors['cyan']}🔍 Mode:{colors['reset']} Single repository: {args.single}"
        )
    else:
        print(
            f"  {colors['cyan']}🔍 Mode:{colors['reset']} Multiple repositories from Excel"
        )

    print(
        f"  {colors['cyan']}⚡ Workers:{colors['reset']} {workers} parallel analysis threads"
    )

    # Verify the excel file exists if using that mode
    if not args.single and not os.path.exists(args.excel):
        print(
            f"{colors['red']}⚠️ Error: Excel file not found: {args.excel}{colors['reset']}"
        )
        print(f"Please provide a valid Excel file path or use --single option.")
        return 1

    logger.info(f"Starting analysis with {workers} workers")
    print(f"\n{colors['yellow']}Starting analysis...{colors['reset']}\n")

    start_time = time.time()

    try:
        # Create a global spinner for overall progress
        spinner = Spinner("Initializing AI agents for analysis")
        spinner.start()

        # Create analysis orchestrator
        orchestrator = AnalysisOrchestrator(
            config_path=args.config,
            output_dir=args.output,
            max_workers=workers,
            verbose=args.verbose,
        )

        # Run analysis
        if args.single:
            # Analyze single repository
            spinner.update(f"Analyzing single repository: {args.single}")
            result = orchestrator.analyze_single_repository(args.single, spinner)

            # Generate a report for this repository
            from src.agents.reporting_agent import generate_reports

            report_result = generate_reports([result], args.output, args.verbose)

            # Add report info to result
            result["report_path"] = os.path.join(
                args.output,
                result["project_name"].replace("/", "_").replace(" ", "_").lower()
                + ".md",
            )

            project_count = 1
            report_summary = report_result.get("summary", "")
        else:
            # Analyze multiple repositories from Excel
            spinner.update(f"Analyzing projects from {args.excel}")
            result = orchestrator.run(args.excel, spinner)
            project_count = result.get("projects_analyzed", 0)
            report_summary = result.get("report_summary", "")

        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        minutes, seconds = divmod(elapsed_time, 60)

        # Final spinner update
        spinner.stop(
            f"Analysis completed successfully in {int(minutes)}m {int(seconds)}s"
        )

        # Show a more stylish completion message
        print(
            f"\n{colors['green']}╔══════════════════════════════════════════════════════════╗{colors['reset']}"
        )
        print(
            f"{colors['green']}║ {colors['bold']}✅ AI AGENTS ANALYSIS COMPLETED SUCCESSFULLY{colors['reset']}{colors['green']} ║{colors['reset']}"
        )
        print(
            f"{colors['green']}╚══════════════════════════════════════════════════════════╝{colors['reset']}"
        )
        print(f"\n{colors['bold']}Summary:{colors['reset']}")
        print(
            f"  {colors['cyan']}⏱️  Time:{colors['reset']} {int(minutes)}m {int(seconds)}s"
        )
        print(f"  {colors['cyan']}📊 Projects:{colors['reset']} {project_count}")
        print(f"  {colors['cyan']}📁 Reports:{colors['reset']} {args.output}/")

        # Display timing information if available
        if args.single and "timing" in result:
            timing = result["timing"]
            print(f"\n{colors['bold']}Timing Breakdown:{colors['reset']}")
            print(
                f"  Repository Analysis:     {timing.get('repository_analysis', 0):.1f}s"
            )
            print(
                f"  Code Quality Analysis:   {timing.get('code_quality_analysis', 0):.1f}s"
            )
            print(
                f"  Celo Integration Check:  {timing.get('celo_integration_analysis', 0):.1f}s"
            )
            print(f"  Total Processing Time:   {timing.get('total', 0):.1f}s")

        # Display key insights if available
        if report_summary:
            print(f"\n{colors['bold']}Key Insights:{colors['reset']}")
            print(f"  {report_summary}")

        print(
            f"\n{colors['yellow']}Thank you for using the Celo Hackathon AI Agents Analysis Tool!{colors['reset']}"
        )

        if args.single:
            print(
                f"\n{colors['bold']}📋 Report:{colors['reset']} {result.get('report_path', '')}"
            )
        else:
            print(
                f"\n{colors['bold']}📋 Summary Report:{colors['reset']} {args.output}/summary.md"
            )

        # Log completion
        logger.info(f"Analysis completed successfully in {elapsed_time:.2f} seconds")

        return 0

    except KeyboardInterrupt:
        print(f"\n\n{colors['yellow']}⚠️ Analysis interrupted by user{colors['reset']}")
        logger.warning("Analysis interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}", exc_info=True)
        print(f"\n{colors['red']}❌ Error: {str(e)}{colors['reset']}")

        # In verbose mode, show traceback
        if args.verbose:
            print("\nTraceback:")
            traceback.print_exc()
        else:
            print("Run with --verbose for more details or check the logs.")

        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
