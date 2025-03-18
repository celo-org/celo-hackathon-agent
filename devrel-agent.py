#!/usr/bin/env python3
"""
DevRel Agent CLI tool for analyzing GitHub repositories.

This interactive CLI tool helps analyze GitHub repositories for code quality 
and Celo blockchain integration.
"""

import os
import sys
import json
import argparse
import inquirer
import pandas as pd
from typing import Dict, List, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

from src.analyzer.repo_analyzer import RepositoryAnalyzer
from src.reporting.report_generator import generate_report
from src.main import load_projects, analyze_projects
from src.utils.logger import logger, configure_logger

# Load environment variables from .env file
load_dotenv()

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
    # Ask for model provider first
    model_question = [
        inquirer.List('model_provider',
                      message="Choose AI model provider:",
                      choices=[
                          ('Anthropic Claude', 'anthropic'),
                          ('OpenAI GPT-4', 'openai'),
                          ('Google Gemini', 'google'),
                      ],
                    ),
    ]
    model_answer = inquirer.prompt(model_question)
    model_provider = model_answer['model_provider']
    
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
    input_data = {'model_provider': model_provider}
    
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
        # Get model provider
        model_provider = user_input.get('model_provider', 'anthropic')
        
        # Check if API key is available for selected provider
        api_key_env_var = {
            'anthropic': 'ANTHROPIC_API_KEY',
            'openai': 'OPENAI_API_KEY', 
            'google': 'GOOGLE_API_KEY'
        }.get(model_provider)
        
        if api_key_env_var and not os.environ.get(api_key_env_var):
            print(f"\n❌ Error: No API key found for {model_provider.capitalize()} in environment variables.")
            print(f"Please set the {api_key_env_var} environment variable in your .env file.")
            return 1
        
        # Display configuration
        print(f"\n{COLORS['bold']}Configuration:{COLORS['reset']}")
        print(f"  {COLORS['cyan']}🤖 Model Provider:{COLORS['reset']} {model_provider.capitalize()}")
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
        
        # Configure logger with verbose setting
        configure_logger(user_input['verbose'])
        
        # Start overall analysis timer
        logger.info("Starting analysis process", step="Analysis")
        
        # Get project data
        if user_input['source'] == 'excel':
            logger.info("Loading project data from Excel", step="Load Projects")
            projects_df = load_projects(user_input['excel_path'])
            logger.step_complete("Load Projects")
        else:
            logger.info("Preparing data from direct URLs", step="Prepare Data")
            projects_df = create_dataframe_from_urls(
                user_input['github_urls'],
                user_input['project_name'],
                user_input['project_description']
            )
            logger.step_complete("Prepare Data")
        
        # Get project count
        project_count = len(projects_df)
        logger.info(f"Found {project_count} projects to analyze")
        
        # Run analysis with verbose flag if enabled
        logger.info(f"Analyzing {project_count} projects", step="Project Analysis")
        results = analyze_projects(
            projects_df, 
            user_input['config_path'], 
            model_provider, 
            verbose=user_input['verbose']
        )
        logger.step_complete("Project Analysis")
        
        # Generate reports
        logger.info(f"Generating reports for {project_count} projects", step="Report Generation")
        generate_report(results, user_input['output_dir'])
        logger.step_complete("Report Generation")
        
        # Complete overall analysis
        logger.step_complete("Analysis")
        
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
        print(f"  {COLORS['cyan']}🤖 Model Provider:{COLORS['reset']} {model_provider.capitalize()}")
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
    parser.add_argument('--model', choices=['anthropic', 'openai', 'google'],
                       default=None, help='AI model provider (anthropic, openai, google)')
    
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
        
        # Load config to get default model if not specified
        try:
            with open(args.config, 'r') as f:
                config_data = json.load(f)
                default_model = config_data.get('default_model', 'anthropic')
        except Exception:
            default_model = 'anthropic'
            
        # Set model provider
        model_provider = args.model or default_model
        user_input['model_provider'] = model_provider
        
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