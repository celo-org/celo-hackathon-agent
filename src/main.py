"""
Main application for Celo Hackathon Analyzer.
"""

import os
import json
import time
import logging
import sys
import argparse
import pandas as pd
from typing import Dict, List, Any, Optional
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv

from src.analyzer.repo_analyzer import RepositoryAnalyzer
from src.utils.spinner import Spinner
from src.reporting.report_generator import generate_report

# Set up logging
# File handler for detailed logging
file_handler = logging.FileHandler("analysis.log")
file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
file_handler.setLevel(logging.DEBUG)

# Console handler for minimal logging (only errors by default)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter("%(message)s"))
console_handler.setLevel(logging.ERROR)  # Only show errors in console by default

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Suppress logging from other libraries
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("anthropic").setLevel(logging.WARNING)

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
    spinner = Spinner(f"Loading projects from {excel_path}")
    spinner.start()

    try:
        logger.info(f"Loading project data from Excel file: {excel_path}")
        df = pd.read_excel(excel_path)
        
        # Handle new format with "Name", "Github URL", "Description"
        if all(col in df.columns for col in ["Name", "Github URL", "Description"]):
            logger.info("Detected new Excel format, converting to internal format")
            # Create a new DataFrame with the required column names
            new_df = pd.DataFrame({
                "project_name": df["Name"],
                "project_description": df["Description"],
                "project_github_url": df["Github URL"],
                # Set empty values for missing columns
                "project_owner_github_url": "",
                "project_url": ""
            })
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
                    spinner.stop(f"Error: Missing column {col}")
                    raise ValueError(f"Missing required column: {col}")

        project_count = len(df)
        spinner.stop(f"Successfully loaded {project_count} projects from {excel_path}")
        logger.info(f"Successfully loaded {project_count} projects")
        return df
    except Exception as e:
        error_msg = f"Error loading project data: {str(e)}"
        spinner.stop(f"Failed to load projects: {str(e)}")
        logger.error(error_msg)
        raise Exception(error_msg)


def analyze_projects(
    projects_df: pd.DataFrame, config_path: str = "config.json", 
    model_provider: Optional[str] = None, verbose: bool = False
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
    logger.info(f"Starting analysis of {total_projects} projects")

    # Initialize progress bar with custom colors and format
    progress_bar = tqdm(
        total=total_projects,
        desc="Analyzing Projects",
        bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]",
        ncols=80,
        colour="green",
    )

    # Initialize repository analyzer with the specified model provider
    analyzer = RepositoryAnalyzer(config_path, model_provider, verbose=verbose)
    results = []

    for index, row in projects_df.iterrows():
        project_name = row["project_name"]
        project_description = row["project_description"]
        raw_github_urls = row["project_github_url"]

        # Update progress bar description - keep it simple
        progress_bar.set_description(f"Analyzing Projects")

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
            logger.warning(f"No valid GitHub URLs found for project {project_name}")

            # Create a default result with error
            project_result = {
                "project_name": project_name,
                "project_description": project_description,
                "project_github_url": "No valid GitHub URL provided",
                "project_owner_github_url": owner_github_urls,
                "project_url": project_url,
                "analysis": {
                    "error": "No valid GitHub URL provided"
                },
            }

            results.append(project_result)
            progress_bar.update(1)
            continue

        # Log the analysis
        logger.info(
            f"Analyzing project {index+1}/{total_projects}: {project_name} with {len(github_urls)} repo(s)"
        )

        # Analyze each GitHub repository
        for url_index, github_url in enumerate(github_urls):
            try:
                # Skip empty URLs
                if not github_url or not github_url.startswith("http"):
                    logger.warning(f"Skipping invalid URL: {github_url}")
                    continue

                # Create a spinner for this repository analysis
                spinner = Spinner(
                    f"Analyzing repository {url_index+1}/{len(github_urls)}: {github_url}"
                )
                spinner.start()

                # Define a callback function to update the spinner
                def progress_callback(message):
                    # Update with repository context
                    updated_message = f"[{url_index+1}/{len(github_urls)}] {message}"
                    spinner.update(updated_message)

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
                    "analysis": repo_analysis
                }

                # Add to results
                results.append(project_result)

                # Stop spinner
                spinner.stop(
                    f"Completed analysis of {github_url}"
                )

            except Exception as e:
                logger.error(f"Error analyzing {github_url}: {str(e)}")
                spinner.stop(f"Error analyzing {github_url}: {str(e)}")

                # Create a project result with error
                project_result = {
                    "project_name": project_name,
                    "project_description": project_description,
                    "project_github_url": raw_github_urls,
                    "github_urls": github_urls,
                    "project_owner_github_url": owner_github_urls,
                    "project_url": project_url,
                    "analysis": {"error": str(e)}
                }

                results.append(project_result)

        # Update progress bar
        progress_bar.update(1)

    # Close progress bar
    progress_bar.close()
    # Add space after progress bar
    print("")
    logger.info(f"Completed analysis of all {total_projects} projects")

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
    ║ {colors['yellow']}CELO HACKATHON PROJECT ANALYZER{colors['cyan']}                     ║
    ╚═════════════════════════════════════════════════════╝{colors['reset']}
    
    {colors['bold']}A tool to analyze GitHub repositories for code quality 
    and Celo blockchain integration.{colors['reset']}
    """
    print(banner)

    # Setup argument parser
    parser = argparse.ArgumentParser(
        description="Analyze GitHub projects for Celo hackathon"
    )
    parser.add_argument(
        "--excel", required=True, help="Path to Excel file containing project data"
    )
    parser.add_argument(
        "--config", default="config.json", help="Path to configuration file"
    )
    parser.add_argument("--output", default="reports", help="Directory to save reports")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--model", default=None, help="Model provider (anthropic, openai, google)")
    args = parser.parse_args()

    # Set logging level based on verbosity
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    # Print startup information in a cleaner format
    print(f"{colors['bold']}Configuration:{colors['reset']}")
    print(f"  {colors['cyan']}📊 Input:{colors['reset']} {args.excel}")
    print(f"  {colors['cyan']}⚙️  Config:{colors['reset']} {args.config}")
    print(f"  {colors['cyan']}📁 Output:{colors['reset']} {args.output}")
    if args.model:
        print(f"  {colors['cyan']}🤖 Model:{colors['reset']} {args.model}")

    print(f"\n{colors['yellow']}Starting analysis...{colors['reset']}\n")

    start_time = time.time()

    try:
        # Create a global spinner for overall progress
        spinner = Spinner("Initializing analysis")
        spinner.start()

        # Load projects from Excel
        spinner.update("Loading project data from Excel")
        projects_df = load_projects(args.excel)

        # Update spinner with project count
        project_count = len(projects_df)
        spinner.update(f"Analyzing {project_count} projects")

        # Analyze projects
        results = analyze_projects(projects_df, args.config, args.model, args.verbose)

        # Generate reports
        spinner.update(f"Generating reports for {len(results)} projects")
        generate_report(results, args.output)

        # Calculate elapsed time
        elapsed_time = time.time() - start_time
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
            f"\n{colors['yellow']}Thank you for using the Celo Hackathon Analysis Tool!{colors['reset']}"
        )

        # Log completion
        logger.info(f"Analysis completed successfully in {elapsed_time:.2f} seconds")

        return 0

    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}", exc_info=True)
        print(f"\n❌ Error: {str(e)}")
        print("Please check the logs for more details.")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())