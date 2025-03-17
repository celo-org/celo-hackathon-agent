#!/usr/bin/env python3
"""
DevRel Agent CLI tool for analyzing GitHub repositories.

This interactive CLI tool helps analyze GitHub repositories for code quality 
and Celo blockchain integration.
"""

import os
import sys
import argparse
import inquirer
import pandas as pd
from typing import Dict, List, Any, Optional
from pathlib import Path

from src.analyzer.repo_analyzer import RepositoryAnalyzer
from src.reporting.report_generator import generate_report
from src.main import load_projects, analyze_projects
from src.utils.spinner import Spinner

# Define colors for styling
COLORS = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "green": "\033[92m",
    "blue": "\033[94m",
    "cyan": "\033[96m",
    "yellow": "\033[93m",
    "magenta": "\033[95m",
}

def display_banner():
    """Display the DevRel Agent banner."""
    banner = f"""
    {COLORS['cyan']}╔═════════════════════════════════════════════════════╗
    ║ {COLORS['yellow']}DEVREL AGENT - PROJECT ANALYZER{COLORS['cyan']}                    ║
    ╚═════════════════════════════════════════════════════╝{COLORS['reset']}
    
    {COLORS['bold']}A tool to analyze GitHub repositories for code quality 
    and Celo blockchain integration.{COLORS['reset']}
    """
    print(banner)

def extract_repo_name_from_url(github_url: str) -> str:
    """
    Extract repository name from GitHub URL.
    
    Args:
        github_url: GitHub repository URL
        
    Returns:
        Repository name
    """
    # Handle empty URL
    if not github_url:
        return "Unknown Repository"
        
    # Remove trailing slashes and .git extension
    github_url = github_url.rstrip('/')
    if github_url.endswith('.git'):
        github_url = github_url[:-4]
    
    # Split the URL and get the last part as the repo name
    parts = github_url.split('/')
    if len(parts) >= 1:
        return parts[-1]
    else:
        return "Unknown Repository"

def get_user_input() -> Dict[str, Any]:
    """
    Get user input through interactive prompts.

    Returns:
        Dict containing user input values.
    """
    # Ask for analysis source
    source_question = [
        inquirer.List('source',
                      message="Choose your input source:",
                      choices=[
                          ('Excel file with GitHub URLs', 'excel'),
                          ('Direct GitHub URLs', 'direct'),
                      ],
                    ),
    ]
    source_answer = inquirer.prompt(source_question)
    
    # Based on source, ask for specific input
    input_data = {}
    
    if source_answer['source'] == 'excel':
        excel_questions = [
            inquirer.Text('excel_path',
                         message="Enter path to Excel file:",
                         default="sample_projects.xlsx"),
        ]
        excel_answer = inquirer.prompt(excel_questions)
        input_data['source'] = 'excel'
        input_data['excel_path'] = excel_answer['excel_path']
    else:
        # First get GitHub URLs
        github_url_question = [
            inquirer.Text('github_urls',
                         message="Enter GitHub URLs (comma-separated):"),
        ]
        github_url_answer = inquirer.prompt(github_url_question)
        github_urls = github_url_answer['github_urls']
        
        # Extract repo name from the first URL for default project name
        default_project_name = "Direct GitHub Analysis"
        if github_urls:
            first_url = github_urls.split(',')[0].strip()
            if first_url:
                default_project_name = extract_repo_name_from_url(first_url)
        
        # Now ask for project name and description
        project_info_questions = [
            inquirer.Text('project_name',
                         message="Enter project name:",
                         default=default_project_name),
            inquirer.Text('project_description',
                         message="Enter project description (optional):",
                         default=""),
        ]
        project_info_answer = inquirer.prompt(project_info_questions)
        
        input_data['source'] = 'direct'
        input_data['github_urls'] = github_urls
        input_data['project_name'] = project_info_answer['project_name']
        input_data['project_description'] = project_info_answer['project_description']
    
    # Common questions
    common_questions = [
        inquirer.Confirm('verbose',
                       message="Enable verbose output?",
                       default=False),
        inquirer.Text('output_dir',
                    message="Enter output directory for reports:",
                    default="reports"),
        inquirer.Text('config_path',
                    message="Enter config file path:",
                    default="config.json"),
    ]
    common_answers = inquirer.prompt(common_questions)
    
    # Merge all answers
    input_data.update(common_answers)
    
    return input_data

def create_dataframe_from_urls(github_urls: str, project_name: str, project_description: str) -> pd.DataFrame:
    """
    Create a DataFrame from direct GitHub URLs.

    Args:
        github_urls: Comma-separated GitHub URLs
        project_name: Name of the project
        project_description: Description of the project

    Returns:
        DataFrame formatted for analysis
    """
    # Split URLs by comma and strip whitespace
    urls = [url.strip() for url in github_urls.split(',') if url.strip()]
    
    # Create DataFrame with required columns
    df = pd.DataFrame({
        "project_name": [project_name],
        "project_description": [project_description],
        "project_github_url": [github_urls],
        "project_owner_github_url": [""],
        "project_url": [""]
    })
    
    return df

def run_analysis(user_input: Dict[str, Any]) -> int:
    """
    Run the analysis based on user input.

    Args:
        user_input: Dictionary of user inputs
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        # Display configuration
        print(f"\n{COLORS['bold']}Configuration:{COLORS['reset']}")
        print(f"  {COLORS['cyan']}📊 Input Source:{COLORS['reset']} {user_input['source']}")
        if user_input['source'] == 'excel':
            print(f"  {COLORS['cyan']}📄 Excel Path:{COLORS['reset']} {user_input['excel_path']}")
        else:
            print(f"  {COLORS['cyan']}🔗 GitHub URLs:{COLORS['reset']} {user_input['github_urls']}")
            print(f"  {COLORS['cyan']}📝 Project Name:{COLORS['reset']} {user_input['project_name']}")
        print(f"  {COLORS['cyan']}⚙️  Config:{COLORS['reset']} {user_input['config_path']}")
        print(f"  {COLORS['cyan']}📁 Output:{COLORS['reset']} {user_input['output_dir']}")
        print(f"  {COLORS['cyan']}🔊 Verbose:{COLORS['reset']} {'Yes' if user_input['verbose'] else 'No'}")

        print(f"\n{COLORS['yellow']}Starting analysis...{COLORS['reset']}\n")
        
        spinner = Spinner("Initializing analysis")
        spinner.start()
        
        # Get project data
        if user_input['source'] == 'excel':
            spinner.update("Loading project data from Excel")
            projects_df = load_projects(user_input['excel_path'])
        else:
            spinner.update("Preparing data from direct URLs")
            projects_df = create_dataframe_from_urls(
                user_input['github_urls'],
                user_input['project_name'],
                user_input['project_description']
            )
        
        # Update spinner with project count
        project_count = len(projects_df)
        spinner.update(f"Analyzing {project_count} projects")
        
        # Run analysis
        results = analyze_projects(projects_df, user_input['config_path'])
        
        # Generate reports
        spinner.update(f"Generating reports for {project_count} projects")
        generate_report(results, user_input['output_dir'])
        
        spinner.stop("Analysis completed")
        
        # Show completion message
        print(
            f"\n{COLORS['green']}╔═════════════════════════════════════════════════════╗{COLORS['reset']}"
        )
        print(
            f"{COLORS['green']}║ {COLORS['bold']}✅ ANALYSIS COMPLETED SUCCESSFULLY{COLORS['reset']}{COLORS['green']}                  ║{COLORS['reset']}"
        )
        print(
            f"{COLORS['green']}╚═════════════════════════════════════════════════════╝{COLORS['reset']}"
        )
        print(f"\n{COLORS['bold']}Summary:{COLORS['reset']}")
        print(f"  {COLORS['cyan']}📊 Projects Analyzed:{COLORS['reset']} {project_count}")
        print(f"  {COLORS['cyan']}📁 Reports:{COLORS['reset']} {user_input['output_dir']}/")
        print(
            f"\n{COLORS['yellow']}Thank you for using DevRel Agent!{COLORS['reset']}"
        )
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("Please check the logs for more details.")
        return 1

def main():
    """Main entry point for the DevRel Agent CLI."""
    parser = argparse.ArgumentParser(description="DevRel Agent CLI")
    parser.add_argument('--non-interactive', action='store_true', 
                        help='Run in non-interactive mode with command-line args')
    parser.add_argument('--excel', help='Path to Excel file with GitHub URLs')
    parser.add_argument('--urls', help='Comma-separated GitHub URLs for direct analysis')
    parser.add_argument('--project-name', 
                        help='Project name for direct URL analysis (defaults to repo name)')
    parser.add_argument('--project-desc', default='', 
                        help='Project description for direct URL analysis')
    parser.add_argument('--output', default='reports', help='Output directory for reports')
    parser.add_argument('--config', default='config.json', help='Path to config file')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Display banner
    display_banner()
    
    # Check if running in non-interactive mode
    if args.non_interactive:
        user_input = {
            'verbose': args.verbose,
            'output_dir': args.output,
            'config_path': args.config
        }
        
        if args.excel:
            user_input['source'] = 'excel'
            user_input['excel_path'] = args.excel
        elif args.urls:
            user_input['source'] = 'direct'
            user_input['github_urls'] = args.urls
            
            # Determine project name - use provided name or extract from URL
            if args.project_name:
                user_input['project_name'] = args.project_name
            else:
                # Extract from the first URL
                first_url = args.urls.split(',')[0].strip()
                user_input['project_name'] = extract_repo_name_from_url(first_url)
                
            user_input['project_description'] = args.project_desc
        else:
            print("Error: In non-interactive mode, you must provide either --excel or --urls")
            return 1
    else:
        # Get user input through interactive prompts
        user_input = get_user_input()
    
    # Run analysis with the provided input
    return run_analysis(user_input)

if __name__ == "__main__":
    sys.exit(main())