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
    projects_df: pd.DataFrame, config_path: str = "config.json", model_provider: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Analyze projects from DataFrame.

    Args:
        projects_df: DataFrame containing project data
        config_path: Path to configuration file
        model_provider: Optional model provider to use for analysis (anthropic, openai, google)

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

    analyzer = RepositoryAnalyzer(config_path, model_provider)
    results = []

    for index, row in projects_df.iterrows():
        project_name = row["project_name"]
        project_description = row["project_description"]
        raw_github_urls = row["project_github_url"]

        # Update progress bar description - keep it simple
        progress_bar.set_description(f"Analyzing Projects")

        # Get project_owner_github_url (comma-separated GitHub user URLs)
        # This field contains GitHub URLs of the project owners/developers
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
        # Otherwise, leave as empty list
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
                    "error": "No valid GitHub URL provided",
                    "code_quality": 0,
                    "celo_integration": False,
                },
            }

            results.append(project_result)
            progress_bar.update(1)
            continue

        # Log the analysis
        logger.info(
            f"Analyzing project {index+1}/{total_projects}: {project_name} with {len(github_urls)} repo(s)"
        )

        # Initialize combined analysis results
        combined_analysis = {
            "repo_details": [],
            "code_quality": {"overall_score": 0, "repositories_analyzed": 0},
            "celo_integration": {
                "integrated": False,
                "evidence": [],
                "repositories_with_celo": 0,
            },
        }

        # Create a spinner
        spinner = Spinner(
            f"Analyzing {len(github_urls)} GitHub repositories for {project_name}"
        )
        spinner.start()

        # Analyze each GitHub repository
        for url_index, github_url in enumerate(github_urls):
            try:
                # Skip empty URLs
                if not github_url or not github_url.startswith("http"):
                    logger.warning(f"Skipping invalid URL: {github_url}")
                    continue

                # Update spinner with current repo
                spinner.update(
                    f"Analyzing repository {url_index+1}/{len(github_urls)}: {github_url}"
                )

                # Define a callback function to update the spinner
                def progress_callback(message):
                    # The spinner's update method now includes animation
                    updated_message = f"[{url_index+1}/{len(github_urls)}] {message}"
                    spinner.update(updated_message)

                    # Helper for manual animation during long operations
                    if "Analyzing" in message or "Checking" in message:
                        # Manually force a few extra animation frames to show activity
                        for _ in range(3):
                            time.sleep(0.1)
                            spinner.update(updated_message)

                # Analyze repository with progress updates
                repo_analysis = analyzer.analyze_repository(
                    github_url, callback=progress_callback
                )

                # Store repo details
                if "repo_details" in repo_analysis:
                    combined_analysis["repo_details"].append(
                        repo_analysis["repo_details"]
                    )

                # Update combined code quality score
                if "code_quality" in repo_analysis:
                    quality = repo_analysis["code_quality"]
                    if isinstance(quality, dict) and "overall_score" in quality:
                        # Increment count and add to total score
                        combined_analysis["code_quality"]["repositories_analyzed"] += 1
                        combined_analysis["code_quality"]["overall_score"] += quality[
                            "overall_score"
                        ]

                        # Preserve detailed metrics from the first repository
                        # Since this is a single-repo analysis most of the time, this preserves the detailed metrics
                        # For multi-repo, we'll just use the first repo's detailed metrics as a sample
                        if (
                            combined_analysis["code_quality"]["repositories_analyzed"]
                            == 1
                        ):
                            # Copy detailed metrics if they exist
                            for key in [
                                "readability",
                                "standards",
                                "complexity",
                                "testing",
                                "ai_analysis",
                                "metrics",
                            ]:
                                if key in quality:
                                    combined_analysis["code_quality"][key] = quality[
                                        key
                                    ]

                # Update Celo integration status
                if "celo_integration" in repo_analysis:
                    celo_integration = repo_analysis["celo_integration"]
                    if (
                        isinstance(celo_integration, dict)
                        and "integrated" in celo_integration
                    ):
                        if celo_integration["integrated"]:
                            # Mark project as Celo-integrated if any repo is integrated
                            combined_analysis["celo_integration"]["integrated"] = True
                            combined_analysis["celo_integration"][
                                "repositories_with_celo"
                            ] += 1

                            # Append evidence if available
                            if (
                                "evidence" in celo_integration
                                and celo_integration["evidence"]
                            ):
                                # Add repo name to evidence for clarity
                                for evidence in celo_integration["evidence"]:
                                    evidence["repository"] = github_url
                                combined_analysis["celo_integration"][
                                    "evidence"
                                ].extend(celo_integration["evidence"])

            except Exception as e:
                logger.error(f"Error analyzing {github_url}: {str(e)}")
                spinner.update(f"Error analyzing {github_url}: {str(e)}")

        # Calculate the average code quality score if we analyzed any repositories
        if combined_analysis["code_quality"]["repositories_analyzed"] > 0:
            avg_score = (
                combined_analysis["code_quality"]["overall_score"]
                / combined_analysis["code_quality"]["repositories_analyzed"]
            )
            combined_analysis["code_quality"]["overall_score"] = avg_score

        # Clear the line first to avoid overlap issues
        print(f"\r{' ' * 100}", end="", flush=True)

        # Final update when done
        spinner.stop(
            f"Completed analysis of {len(github_urls)} repositories for {project_name}"
        )

        # Combine project info with analysis results
        project_result = {
            "project_name": project_name,
            "project_description": project_description,
            "project_github_url": raw_github_urls,  # Keep the original value
            "github_urls": github_urls,  # Add the list of URLs
            "project_owner_github_url": owner_github_urls,
            "project_url": project_url,
            "analysis": combined_analysis,
        }

        results.append(project_result)

        # Basic success message
        logger.info(f"Successfully analyzed {project_name}")

        # Log code quality score and Celo integration status
        if "code_quality" in combined_analysis:
            score = combined_analysis["code_quality"].get("overall_score", 0)
            repos_analyzed = combined_analysis["code_quality"].get(
                "repositories_analyzed", 0
            )
            logger.info(
                f"Code quality score for {project_name}: {score:.2f}/100 (based on {repos_analyzed} repositories)"
            )

        # Log Celo integration status
        if "celo_integration" in combined_analysis:
            is_integrated = combined_analysis["celo_integration"].get(
                "integrated", False
            )
            repos_with_celo = combined_analysis["celo_integration"].get(
                "repositories_with_celo", 0
            )
            logger.info(
                f"Celo integration for {project_name}: {'Yes' if is_integrated else 'No'} ({repos_with_celo}/{len(github_urls)} repositories)"
            )

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
        results = analyze_projects(projects_df, args.config)

        # Generate reports
        spinner.update(f"Generating reports for {project_count} projects")
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
