"""
Main application for Hackathon Analyzer.
"""

import os
import json
import time
import sys
import argparse
import pandas as pd
from typing import Dict, List, Any, Optional
from pathlib import Path
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from src.analyzer.repo_analyzer import RepositoryAnalyzer
from src.reporting.report_generator import generate_reports
from src.utils.logger import logger, configure_logger

# Load environment variables from .env file
load_dotenv()


def load_projects(excel_path: str) -> pd.DataFrame:
    """
    Load projects from Excel file.

    Args:
        excel_path: Path to Excel file

    Returns:
        DataFrame containing project data
    """
    logger.info("Loading project data", step="Load Projects")

    try:
        df = pd.read_excel(excel_path)

        # Handle new format with "Name", "Github URL", "Description"
        if all(col in df.columns for col in ["Name", "Github URL", "Description"]):
            logger.debug("Detected new Excel format, converting to internal format")
            # Create a new DataFrame with the required column names
            new_df = pd.DataFrame(
                {
                    "project_name": df["Name"],
                    "project_description": df["Description"],
                    "project_github_url": df["Github URL"],
                    # Set empty values for missing columns
                    "project_owner_github_url": "",
                    "project_url": "",
                }
            )
            df = new_df

        # Handle legacy format
        else:
            required_columns = [
                "project_name",
                "project_description",
                "project_github_url",
                "project_owner_github_url",
                "project_url",
            ]

            # Check if required columns exist
            for col in required_columns:
                if col not in df.columns:
                    logger.error(f"Missing required column: {col}")
                    raise ValueError(f"Missing required column: {col}")

        project_count = len(df)
        logger.step_complete("Load Projects")
        logger.info(f"Found {project_count} projects to analyze")
        return df
    except Exception as e:
        error_msg = f"Error loading project data: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)


def analyze_projects(
    projects_df: pd.DataFrame,
    config_path: str = "config.json",
    model_provider: Optional[str] = None,
    verbose: bool = False,
) -> List[Dict[str, Any]]:
    """
    Analyze projects from DataFrame.

    Args:
        projects_df: DataFrame containing project data
        config_path: Path to configuration file
        model_provider: Optional model provider to use for analysis (anthropic, openai, google)
        verbose: Whether to enable verbose output

    Returns:
        List of dictionaries containing analysis results
    """
    total_projects = len(projects_df)
    logger.info(
        f"Starting analysis of {total_projects} projects", step="Project Analysis"
    )

    # Initialize repository analyzer with the specified model provider
    analyzer = RepositoryAnalyzer(config_path, model_provider, verbose=verbose)
    results = []

    for index, row in projects_df.iterrows():
        project_name = row["project_name"]
        project_description = row["project_description"]
        raw_github_urls = row["project_github_url"]

        # Get project_owner_github_url (comma-separated GitHub user URLs)
        raw_owner_urls = row["project_owner_github_url"]

        # Process owner GitHub URLs (handle comma-separated URLs)
        owner_github_urls = []
        if isinstance(raw_owner_urls, str):
            # Split by comma and strip whitespace
            owner_github_urls = [
                url.strip() for url in raw_owner_urls.split(",") if url.strip()
            ]
        elif pd.notna(raw_owner_urls):  # Check if it's not NaN
            # If it's not a string (might be a single URL without commas)
            owner_github_urls = [str(raw_owner_urls)]

        # Get project URL
        project_url = row["project_url"]

        # Process the GitHub URLs (handle comma-separated URLs)
        github_urls = []
        if isinstance(raw_github_urls, str):
            # Split by comma and strip whitespace
            github_urls = [
                url.strip() for url in raw_github_urls.split(",") if url.strip()
            ]
        else:
            # If it's not a string (might be a single URL without commas or NaN)
            if pd.notna(raw_github_urls):
                github_urls = [str(raw_github_urls)]

        # If no valid GitHub URLs, create a default result and continue
        if not github_urls:
            logger.warn(f"No valid GitHub URLs found for project {project_name}")

            # Create a default result with error
            project_result = {
                "project_name": project_name,
                "project_description": project_description,
                "project_github_url": "No valid GitHub URL provided",
                "project_owner_github_url": owner_github_urls,
                "project_url": project_url,
                "analysis": {"error": "No valid GitHub URL provided"},
            }

            results.append(project_result)
            continue

        # Log the analysis
        logger.info(
            f"Analyzing project {index+1}/{total_projects}: {project_name}",
            step=f"Project {index+1}/{total_projects}",
        )

        # Analyze each GitHub repository
        for url_index, github_url in enumerate(github_urls):
            try:
                # Skip empty URLs
                if not github_url or not github_url.startswith("http"):
                    logger.warn(f"Skipping invalid URL: {github_url}")
                    continue

                # Log repository analysis start
                repo_name = f"Repository {url_index+1}/{len(github_urls)}"
                logger.info(f"Analyzing {github_url}", step=repo_name)

                # Define a callback function for progress updates
                def progress_callback(message):
                    logger.progress_callback(repo_name)(message)

                # Analyze repository with progress updates
                repo_analysis = analyzer.analyze_repository(
                    github_url, callback=progress_callback
                )

                # Create a project result with repository analysis
                project_result = {
                    "project_name": project_name,
                    "project_description": project_description,
                    "project_github_url": raw_github_urls,
                    "github_urls": github_urls,
                    "project_owner_github_url": owner_github_urls,
                    "project_url": project_url,
                    "analysis": repo_analysis,
                }

                # Add to results
                results.append(project_result)

                # Log completion
                logger.step_complete(repo_name)

            except Exception as e:
                logger.error(f"Error analyzing {github_url}: {str(e)}")

                # Create a project result with error
                project_result = {
                    "project_name": project_name,
                    "project_description": project_description,
                    "project_github_url": raw_github_urls,
                    "github_urls": github_urls,
                    "project_owner_github_url": owner_github_urls,
                    "project_url": project_url,
                    "analysis": {"error": str(e)},
                }

                results.append(project_result)

        # Log completion of this project
        logger.step_complete(f"Project {index+1}/{total_projects}")

    # Log completion of all projects
    logger.step_complete("Project Analysis")

    return results


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
    }

    # Show a smaller, cleaner banner
    banner = f"""
    {colors['cyan']}╔═════════════════════════════════════════════════════╗
    ║ {colors['yellow']}HACKATHON PROJECT ANALYZER{colors['cyan']}                         ║
    ╚═════════════════════════════════════════════════════╝{colors['reset']}
    
    {colors['bold']}A tool to analyze GitHub repositories for code quality 
    and blockchain integration.{colors['reset']}
    """
    print(banner)

    # Setup argument parser
    parser = argparse.ArgumentParser(
        description="Analyze GitHub projects for hackathon"
    )
    parser.add_argument(
        "--excel", required=True, help="Path to Excel file containing project data"
    )
    parser.add_argument(
        "--config", default="config.json", help="Path to configuration file"
    )
    parser.add_argument("--output", default="reports", help="Directory to save reports")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument(
        "--model", default=None, help="Model provider (anthropic, openai, google)"
    )
    args = parser.parse_args()

    # Configure logger with verbosity
    configure_logger(args.verbose)

    if args.verbose:
        logger.debug("Verbose logging enabled")

    # Print startup information in a cleaner format
    print(f"{colors['bold']}Configuration:{colors['reset']}")
    print(f"  {colors['cyan']}📊 Input:{colors['reset']} {args.excel}")
    print(f"  {colors['cyan']}⚙️  Config:{colors['reset']} {args.config}")
    print(f"  {colors['cyan']}📁 Output:{colors['reset']} {args.output}")
    if args.model:
        print(f"  {colors['cyan']}🤖 Model:{colors['reset']} {args.model}")

    print(f"\n{colors['yellow']}Starting analysis...{colors['reset']}\n")

    logger.info("Starting analysis process", step="Analysis")

    try:
        # Load projects from Excel
        projects_df = load_projects(args.excel)

        # Get project count
        project_count = len(projects_df)

        # Analyze projects
        results = analyze_projects(projects_df, args.config, args.model, args.verbose)

        # Generate reports
        logger.info(
            f"Generating reports for {len(results)} projects", step="Report Generation"
        )
        generate_reports(results, args.output)
        logger.step_complete("Report Generation")

        # Complete overall analysis
        logger.step_complete("Analysis")

        # Calculate elapsed time
        elapsed_time = logger.stop_timer("Analysis")
        minutes, seconds = divmod(elapsed_time, 60)

        # Show a more stylish completion message
        print(
            f"\n{colors['green']}╔═════════════════════════════════════════════════════╗{colors['reset']}"
        )
        print(
            f"{colors['green']}║ {colors['bold']}✅ ANALYSIS COMPLETED SUCCESSFULLY{colors['reset']}{colors['green']}                  ║{colors['reset']}"
        )
        print(
            f"{colors['green']}╚═════════════════════════════════════════════════════╝{colors['reset']}"
        )
        print(f"\n{colors['bold']}Summary:{colors['reset']}")
        print(
            f"  {colors['cyan']}⏱️  Time:{colors['reset']} {int(minutes)}m {int(seconds)}s"
        )
        print(f"  {colors['cyan']}📊 Projects:{colors['reset']} {project_count}")
        print(f"  {colors['cyan']}📁 Reports:{colors['reset']} {args.output}/")
        print(
            f"\n{colors['yellow']}Thank you for using the Hackathon Analysis Tool!{colors['reset']}"
        )

        return 0

    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}", exc_info=True)
        print(f"\n❌ Error: {str(e)}")
        print("Please check the logs for more details.")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
