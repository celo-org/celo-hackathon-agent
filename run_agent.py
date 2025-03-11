#!/usr/bin/env python3
"""
Celo Hackathon Analyzer using LangChain agent-based architecture.

This script launches the analysis of GitHub repositories using specialized tool-calling agents
that evaluate code quality and check for Celo blockchain integration.
"""

import os
import json
import time
import logging
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

from src.agents.coordinator import AnalysisPipeline
from src.utils.spinner import Spinner
from src.models.config import Config

# Set up logging
# File handler for detailed logging
file_handler = logging.FileHandler("agent_analysis.log")
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

def main():
    """Main function to run the analysis."""
    # Colors for styling
    colors = {
        'reset': '\033[0m',
        'bold': '\033[1m',
        'green': '\033[92m',
        'blue': '\033[94m',
        'cyan': '\033[96m',
        'yellow': '\033[93m',
        'magenta': '\033[95m'
    }
    
    # Show a banner
    banner = f"""
    {colors['cyan']}╔══════════════════════════════════════════════════════════╗
    ║ {colors['yellow']}CELO HACKATHON PROJECT ANALYZER - AGENT-BASED VERSION{colors['cyan']} ║
    ╚══════════════════════════════════════════════════════════╝{colors['reset']}
    
    {colors['bold']}An intelligent tool that analyzes GitHub repositories 
    using specialized AI agents and tool-calling architecture.{colors['reset']}
    """
    print(banner)
    
    # Setup argument parser
    parser = argparse.ArgumentParser(
        description="Analyze GitHub projects using LangChain agents"
    )
    parser.add_argument(
        "--excel", required=True, help="Path to Excel file containing project data"
    )
    parser.add_argument(
        "--config", default="config.json", help="Path to configuration file"
    )
    parser.add_argument("--output", default="reports", help="Directory to save reports")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--single", help="Analyze a single repository URL (optional)")
    args = parser.parse_args()
    
    # Set logging level based on verbosity
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        console_handler.setLevel(logging.INFO)
        logger.debug("Verbose logging enabled")
    
    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(f"{colors['yellow']}⚠️ Error: No Anthropic API key found.{colors['reset']}")
        print("Please set ANTHROPIC_API_KEY environment variable or add it to .env file.")
        return 1
    
    # Print startup information
    print(f"{colors['bold']}Configuration:{colors['reset']}")
    print(f"  {colors['cyan']}📊 Input:{colors['reset']} {args.excel}")
    print(f"  {colors['cyan']}⚙️  Config:{colors['reset']} {args.config}")
    print(f"  {colors['cyan']}📁 Output:{colors['reset']} {args.output}")
    print(f"  {colors['cyan']}🔍 Mode:{colors['reset']} {'Single repository: ' + args.single if args.single else 'Multiple repositories from Excel'}")
    
    print(f"\n{colors['yellow']}Starting analysis...{colors['reset']}\n")
    
    start_time = time.time()
    
    try:
        # Create a global spinner for overall progress
        spinner = Spinner("Initializing agent-based analysis")
        spinner.start()
        
        # Load configuration
        config = Config.from_file(args.config)
        
        # Create analysis pipeline
        pipeline = AnalysisPipeline(
            config_path=args.config,
            output_dir=args.output,
            verbose=args.verbose
        )
        
        # Run analysis
        if args.single:
            # Analyze single repository
            spinner.update(f"Analyzing single repository: {args.single}")
            result = pipeline.analyze_single_repository(args.single)
            
            # Generate a report for this repository
            from src.agents.reporting_agent import generate_reports
            generate_reports([result], args.output, args.verbose)
            
            project_count = 1
        else:
            # Analyze multiple repositories from Excel
            spinner.update(f"Analyzing projects from {args.excel}")
            result = pipeline.run(args.excel)
            project_count = result.get("projects_analyzed", 0)
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        minutes, seconds = divmod(elapsed_time, 60)
        
        # Final spinner update
        spinner.stop(f"Analysis completed successfully in {int(minutes)}m {int(seconds)}s")
        
        # Show a more stylish completion message
        print(
            f"\n{colors['green']}╔══════════════════════════════════════════════════════════╗{colors['reset']}"
        )
        print(
            f"{colors['green']}║ {colors['bold']}✅ AGENT-BASED ANALYSIS COMPLETED SUCCESSFULLY{colors['reset']}{colors['green']} ║{colors['reset']}"
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
        
        # Display key insights if available
        if isinstance(result, dict) and "report_summary" in result:
            print(f"\n{colors['bold']}Key Insights:{colors['reset']}")
            report_summary = result["report_summary"]
            print(f"  {report_summary}\n")
        
        print(
            f"\n{colors['yellow']}Thank you for using the Celo Hackathon Agent-Based Analysis Tool!{colors['reset']}"
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