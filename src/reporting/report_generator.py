"""
Report generation module for the Celo Hackathon Analyzer.
"""

import os
import json
import logging
import pandas as pd
from typing import Dict, List, Any
from tqdm import tqdm

from src.utils.spinner import Spinner

# Configure logger
logger = logging.getLogger(__name__)


def clean_urls(urls: List[str]) -> List[str]:
    """
    Clean up URL strings that might have artifacts from data processing.
    
    Args:
        urls: List of URLs that might contain formatting artifacts
        
    Returns:
        List of cleaned URLs
    """
    clean_urls = []
    for url in urls:
        # Check if it's a string that might contain list formatting like "['url']"
        if isinstance(url, str) and url.startswith("['") and url.endswith("']"):
            # Extract the actual URL from inside the quotes and brackets
            clean_url = url.strip("[]'")
            clean_urls.append(clean_url)
        else:
            clean_urls.append(url)
    return clean_urls


def generate_summary_report(results: List[Dict[str, Any]], output_path: str):
    """
    Generate a summary report with all projects.
    
    Args:
        results: List of project analysis results
        output_path: Path to write the summary report
    """
    with open(output_path, "w") as f:
        f.write("# Celo Hackathon Project Analysis Summary\n\n")
        f.write("| Project | Score | Celo Integration | GitHub URL |\n")
        f.write("|---------|-------|------------------|------------|\n")

        for result in results:
            # Get project name with fallback
            project_name = result.get("project_name", "Unknown Project")
            
            # Handle GitHub URLs with fallbacks for missing fields
            github_url_display = "Not available"
            
            # Try to get from github_urls list first
            if "github_urls" in result and result["github_urls"]:
                github_urls = result["github_urls"]
                if len(github_urls) > 1:
                    github_url_display = f"[{github_urls[0]}]({github_urls[0]}) +{len(github_urls)-1} more"
                else:
                    github_url_display = f"[{github_urls[0]}]({github_urls[0]})"
            # Fallback to project_github_url if available
            elif "project_github_url" in result and result["project_github_url"]:
                github_url = result["project_github_url"]
                # Check if it's a string (might be a list or other structure)
                if isinstance(github_url, str):
                    github_url_display = f"[{github_url}]({github_url})"

            # Get code quality score with fallbacks
            score_display = "0.00"
            
            # Check if code_quality_score is directly in the result (for test data)
            if "code_quality_score" in result and isinstance(result["code_quality_score"], (int, float)):
                score = result["code_quality_score"]
                score_display = f"{score:.2f}"
            # Otherwise try to find it in the analysis structure
            elif "analysis" in result and "code_quality" in result["analysis"]:
                code_quality = result["analysis"]["code_quality"]
                if isinstance(code_quality, dict) and "overall_score" in code_quality:
                    score = code_quality["overall_score"]
                    repos_analyzed = code_quality.get("repositories_analyzed", 1)
                    # Add repository count if multiple repositories
                    score_display = f"{score:.2f}" if repos_analyzed <= 1 else f"{score:.2f} ({repos_analyzed} repos)"
                elif isinstance(code_quality, (int, float)):
                    score = code_quality
                    score_display = f"{score:.2f}"

            # Get Celo integration status with fallbacks
            celo_status = "❌"
            
            # Check if celo_integration_score is directly in the result (for test data)
            if "celo_integration_score" in result and isinstance(result["celo_integration_score"], (int, float)):
                celo_score = result["celo_integration_score"]
                celo_status = "✅" if celo_score > 50 else "❌"
            # Otherwise try to find it in the analysis structure
            elif "analysis" in result and "celo_integration" in result["analysis"]:
                celo_integration = result["analysis"]["celo_integration"]
                if isinstance(celo_integration, dict) and "integrated" in celo_integration:
                    celo_integrated = celo_integration["integrated"]
                    repos_with_celo = celo_integration.get("repositories_with_celo", 0)
                elif isinstance(celo_integration, bool):
                    celo_integrated = celo_integration
                    repos_with_celo = 1 if celo_integrated else 0
                else:
                    celo_integrated = False
                    repos_with_celo = 0
                
                # Show Celo integration status with repository count if multiple repositories
                if "github_urls" in result and len(result["github_urls"]) > 1:
                    celo_status = f"{'✅' if celo_integrated else '❌'} ({repos_with_celo}/{len(result['github_urls'])})"
                else:
                    celo_status = "✅" if celo_integrated else "❌"

            f.write(
                f"| {project_name} | {score_display} | {celo_status} | {github_url_display} |\n"
            )


def generate_project_report(result: Dict[str, Any], output_path: str):
    """
    Generate a detailed report for a single project.
    
    Args:
        result: Project analysis results
        output_path: Path to write the project report
    """
    with open(output_path, "w") as f:
        # Get project name with fallback for missing field
        project_name = result.get('project_name', 'Unknown Project')
        f.write(f"# Project Analysis: {project_name}\n\n")

        # Project Overview
        f.write("## Project Overview\n\n")
        f.write(f"**Project Name:** {project_name}\n\n")
        
        # Project description with fallback for missing field
        project_description = result.get('project_description', 'No description available')
        f.write(f"**Project Description:** {project_description}\n\n")
        
        # Handle None/NaN project_url or missing field
        if 'project_url' in result:
            project_url = result['project_url']
            if project_url is None or isinstance(project_url, float) and pd.isna(project_url):
                f.write(f"**Project URL:** Not available\n\n")
            else:
                f.write(f"**Project URL:** [{project_url}]({project_url})\n\n")
        else:
            f.write(f"**Project URL:** Not available\n\n")
        
        # Add GitHub profiles of project owners/developers
        if "project_owner_github_url" in result and result["project_owner_github_url"]:
            owner_urls = clean_urls(result["project_owner_github_url"])
            
            if len(owner_urls) == 1:
                f.write(f"**Project Developer:** [{owner_urls[0]}]({owner_urls[0]})\n\n")
            elif len(owner_urls) > 1:
                f.write(f"**Project Developers:**\n\n")
                for i, url in enumerate(owner_urls):
                    f.write(f"{i+1}. [{url}]({url})\n")
                f.write("\n")
        
        # Handle multiple GitHub URLs
        if "github_urls" in result and result["github_urls"]:
            # List all GitHub URLs
            github_urls = result["github_urls"]
            if len(github_urls) == 1:
                f.write(f"**GitHub URL:** [{github_urls[0]}]({github_urls[0]})\n\n")
            else:
                f.write(f"**GitHub URLs:** ({len(github_urls)} repositories)\n\n")
                for i, url in enumerate(github_urls):
                    f.write(f"{i+1}. [{url}]({url})\n")
                f.write("\n")
        elif "project_github_url" in result:
            # Fallback to original format
            github_url = result['project_github_url']
            f.write(f"**GitHub URL:** [{github_url}]({github_url})\n\n")
        else:
            # No GitHub URL available
            f.write(f"**GitHub URL:** Not available\n\n")

        # Repository details - handle multiple repositories
        if "analysis" in result and "repo_details" in result["analysis"]:
            repo_details = result["analysis"]["repo_details"]
            
            # Check if we have multiple repositories
            if isinstance(repo_details, list) and len(repo_details) > 0:
                f.write("### Repository Statistics\n\n")
                
                if len(repo_details) == 1:
                    # Single repository - show simple stats
                    repo = repo_details[0]
                    f.write(f"- **Repository:** {repo.get('name', 'N/A')}\n")
                    f.write(f"- **Stars:** {repo.get('stars', 'N/A')}\n")
                    f.write(f"- **Forks:** {repo.get('forks', 'N/A')}\n")
                    f.write(f"- **Open Issues:** {repo.get('open_issues', 'N/A')}\n")
                    f.write(f"- **Primary Language:** {repo.get('language', 'N/A')}\n")
                    f.write(f"- **Last Updated:** {repo.get('last_update', 'N/A')}\n\n")
                else:
                    # Multiple repositories - create a summary table
                    f.write("| Repository | Stars | Forks | Issues | Language | Last Updated |\n")
                    f.write("|------------|-------|-------|--------|----------|-------------|\n")
                    
                    for repo in repo_details:
                        repo_name = repo.get('name', 'N/A')
                        stars = repo.get('stars', 0)
                        forks = repo.get('forks', 0)
                        issues = repo.get('open_issues', 0)
                        language = repo.get('language', 'N/A')
                        last_update = repo.get('last_update', 'N/A')
                        if last_update and len(last_update) > 10:
                            # Simplify date format for table
                            last_update = last_update.split('T')[0]
                        
                        f.write(f"| {repo_name} | {stars} | {forks} | {issues} | {language} | {last_update} |\n")
                    f.write("\n")
            elif isinstance(repo_details, dict):
                # Single repository in old format
                f.write("### Repository Statistics\n\n")
                f.write(f"- **Stars:** {repo_details.get('stars', 'N/A')}\n")
                f.write(f"- **Forks:** {repo_details.get('forks', 'N/A')}\n")
                f.write(f"- **Open Issues:** {repo_details.get('open_issues', 'N/A')}\n")
                f.write(f"- **Primary Language:** {repo_details.get('language', 'N/A')}\n")
                f.write(f"- **Last Updated:** {repo_details.get('last_update', 'N/A')}\n\n")

        # Code Quality
        f.write("## Code Quality Assessment\n\n")

        if "analysis" in result and "code_quality" in result["analysis"]:
            quality = result["analysis"]["code_quality"]

            if isinstance(quality, (int, float)):
                # If code_quality is just a number
                f.write(f"**Overall Score:** {quality:.2f}/100\n\n")
            elif isinstance(quality, dict):
                if "error" in quality:
                    f.write(f"**Error:** {quality['error']}\n\n")
                elif not quality:  # Check if dictionary is empty
                    f.write("Repository analysis was unsuccessful or returned no data.\n\n")
                else:
                    # Check if we have multiple repository info
                    repos_analyzed = quality.get("repositories_analyzed", 0)
                    
                    # Safely get values with proper type checking
                    overall_score = quality.get("overall_score", 0)
                    if isinstance(overall_score, (int, float)):
                        if repos_analyzed > 1:
                            f.write(f"**Overall Score:** {overall_score:.2f}/100 (average of {repos_analyzed} repositories)\n\n")
                        else:
                            f.write(f"**Overall Score:** {overall_score:.2f}/100\n\n")
                    else:
                        f.write(f"**Overall Score:** 0.00/100\n\n")
                    
                    # Add a detailed analysis section
                    f.write("### Detailed Analysis\n\n")
                    
                    # Readability score and analysis
                    readability = quality.get("readability", 0)
                    readability_reasoning = None
                    if "ai_analysis" in quality and "readability_reasoning" in quality.get("ai_analysis", {}):
                        readability_reasoning = quality["ai_analysis"]["readability_reasoning"]
                        
                    if isinstance(readability, (int, float)):
                        f.write(f"**Readability and Documentation:** {readability:.2f}/100\n\n")
                        if readability_reasoning:
                            f.write(f"{readability_reasoning}\n\n")
                    else:
                        f.write(f"**Readability and Documentation:** Not evaluated\n\n")
                    
                    # Standards score and analysis
                    standards = quality.get("standards", 0)
                    standards_reasoning = None
                    if "ai_analysis" in quality and "standards_reasoning" in quality.get("ai_analysis", {}):
                        standards_reasoning = quality["ai_analysis"]["standards_reasoning"]
                        
                    if isinstance(standards, (int, float)):
                        f.write(f"**Coding Standards and Best Practices:** {standards:.2f}/100\n\n")
                        if standards_reasoning:
                            f.write(f"{standards_reasoning}\n\n")
                    else:
                        f.write(f"**Coding Standards and Best Practices:** Not evaluated\n\n")
                    
                    # Complexity score and analysis
                    complexity = quality.get("complexity", 0)
                    complexity_reasoning = None
                    if "ai_analysis" in quality and "complexity_reasoning" in quality.get("ai_analysis", {}):
                        complexity_reasoning = quality["ai_analysis"]["complexity_reasoning"]
                        
                    if isinstance(complexity, (int, float)):
                        f.write(f"**Algorithm Complexity and Efficiency:** {complexity:.2f}/100\n\n")
                        if complexity_reasoning:
                            f.write(f"{complexity_reasoning}\n\n")
                    else:
                        f.write(f"**Algorithm Complexity and Efficiency:** Not evaluated\n\n")
                    
                    # Testing score and analysis
                    testing = quality.get("testing", 0)
                    testing_reasoning = None
                    if "ai_analysis" in quality and "testing_reasoning" in quality.get("ai_analysis", {}):
                        testing_reasoning = quality["ai_analysis"]["testing_reasoning"]
                        
                    if isinstance(testing, (int, float)):
                        f.write(f"**Testing and Coverage:** {testing:.2f}/100\n\n")
                        if testing_reasoning:
                            f.write(f"{testing_reasoning}\n\n")
                    else:
                        f.write(f"**Testing and Coverage:** Not evaluated\n\n")
                    
                    # Overall analysis and suggestions
                    overall_analysis = None
                    suggestions = []
                    if "ai_analysis" in quality:
                        if "overall_analysis" in quality["ai_analysis"]:
                            overall_analysis = quality["ai_analysis"]["overall_analysis"]
                        if "suggestions" in quality["ai_analysis"]:
                            suggestions = quality["ai_analysis"]["suggestions"]
                            
                    if overall_analysis:
                        f.write("### Overall Assessment\n\n")
                        f.write(f"{overall_analysis}\n\n")
                        
                    if suggestions and len(suggestions) > 0:
                        f.write("### Suggestions for Improvement\n\n")
                        for suggestion in suggestions:
                            f.write(f"- {suggestion}\n")
                        f.write("\n")
                    
                    # Metrics
                    if "metrics" in quality:
                        f.write("### Metrics\n\n")
                        metrics = quality["metrics"]
                        f.write(
                            f"- **Total Files:** {metrics.get('file_count', 'N/A')}\n"
                        )
                        f.write(
                            f"- **Test Files:** {metrics.get('test_file_count', 'N/A')}\n"
                        )
                        f.write(
                            f"- **Documentation Files:** {metrics.get('doc_file_count', 'N/A')}\n"
                        )
                        
                        if "code_lines" in metrics:
                            f.write(
                                f"- **Lines of Code:** {metrics.get('code_lines', 'N/A')}\n"
                            )
                        
                        if "comment_lines" in metrics:
                            f.write(
                                f"- **Comment Lines:** {metrics.get('comment_lines', 'N/A')}\n"
                            )
                            
                        if "code_files_analyzed" in metrics:
                            f.write(
                                f"- **Code Files Analyzed:** {metrics.get('code_files_analyzed', 'N/A')}\n"
                            )
                        
                        f.write("\n")
            else:
                f.write(
                    "Could not assess code quality due to an error or inaccessible repository.\n\n"
                )
        else:
            f.write(
                "Could not assess code quality due to an error or inaccessible repository.\n\n"
            )

        # Celo Integration
        f.write("## Celo Blockchain Integration\n\n")

        if "analysis" in result and "celo_integration" in result["analysis"]:
            celo = result["analysis"]["celo_integration"]

            if isinstance(celo, bool):
                # If celo_integration is just a boolean
                integration_status = "Yes" if celo else "No"
                f.write(f"**Integrated with Celo:** {integration_status}\n\n")
            elif isinstance(celo, dict):
                if "error" in celo:
                    f.write(f"**Error:** {celo['error']}\n\n")
                elif not celo:  # Check if dictionary is empty
                    f.write("Repository analysis was unsuccessful or returned no data.\n\n")
                else:
                    # Get integration status safely
                    if "integrated" in celo:
                        integrated = celo["integrated"]
                        # Check if we have multiple repository data
                        repos_with_celo = celo.get("repositories_with_celo", 0)
                        repos_analyzed = 1  # Default for backward compatibility
                        
                        # Check if we can determine total repositories analyzed
                        if "github_urls" in result and result["github_urls"]:
                            repos_analyzed = len(result["github_urls"])
                    else:
                        integrated = False
                        repos_with_celo = 0
                        repos_analyzed = 1
                        
                    # Format integration status with repository counts if multiple repos
                    if repos_analyzed > 1:
                        integration_status = f"{'Yes' if integrated else 'No'} ({repos_with_celo}/{repos_analyzed} repositories)"
                    else:
                        integration_status = "Yes" if integrated else "No"

                    f.write(f"**Integrated with Celo:** {integration_status}\n\n")

                    if integrated and "evidence" in celo and isinstance(celo["evidence"], list):
                        f.write("### Evidence of Integration\n\n")
                        for evidence in celo["evidence"]:
                            if isinstance(evidence, dict) and "keyword" in evidence and "file" in evidence:
                                # Check if evidence includes repository information
                                if "repository" in evidence:
                                    f.write(
                                        f"- Found keyword '{evidence['keyword']}' in file: {evidence['file']} (Repository: {evidence['repository']})\n"
                                    )
                                else:
                                    f.write(
                                        f"- Found keyword '{evidence['keyword']}' in file: {evidence['file']}\n"
                                    )
                        f.write("\n")
                    
                    # Add AI analysis of Celo integration if available
                    if integrated and "analysis" in celo:
                        f.write("### Integration Analysis\n\n")
                        f.write(f"{celo['analysis']}\n\n")
            else:
                # Default case if celo_integration is something unexpected
                f.write(f"**Integrated with Celo:** No\n\n")
        else:
            f.write(
                "Could not assess Celo integration due to an error or inaccessible repository.\n\n"
            )

        # Additional Notes
        f.write("## Additional Notes\n\n")

        if "analysis" in result and "error" in result["analysis"]:
            f.write(f"- {result['analysis']['error']}\n")
        else:
            f.write("No additional notes.\n")


def generate_report(results: List[Dict[str, Any]], output_dir: str = "reports") -> None:
    """
    Generate Markdown reports from analysis results.

    Args:
        results: List of dictionaries containing analysis results
        output_dir: Directory to save reports
    """
    # Create a spinner for report generation
    spinner = Spinner(f"Generating reports in {output_dir} directory")
    spinner.start()
    
    logger.info(f"Starting report generation for {len(results)} projects")
    
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate summary report
        spinner.update(f"Creating summary report")
        logger.info(f"Generating summary report in {output_dir}")
        
        summary_path = os.path.join(output_dir, "summary.md")
        generate_summary_report(results, summary_path)
        
        # Initialize progress bar for individual reports with custom colors and format
        progress_bar = tqdm(
            total=len(results),
            desc="Generating Reports",
            bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]",
            ncols=80,
            colour="blue"
        )

        # Generate individual reports
        for idx, result in enumerate(results):
            project_name = result["project_name"]
            file_name = project_name.replace(" ", "_").lower()
            report_path = os.path.join(output_dir, f"{file_name}.md")
            
            # Keep the progress description simple
            progress_bar.set_description(f"Generating Reports")
            
            # Log progress
            logger.info(f"Creating report for {project_name} ({idx+1}/{len(results)})")

            # Generate the project report
            generate_project_report(result, report_path)
            
            # Update progress bar
            progress_bar.update(1)
        
        # Close progress bar
        progress_bar.close()
        # Add space after progress bar
        print("")
        
        # Save raw results to JSON
        spinner.update(f"Saving raw results to JSON")
        logger.info(f"Saving raw results to {output_dir}/results.json")
        with open(os.path.join(output_dir, "results.json"), "w") as f:
            json.dump(results, f, indent=2)
        
        # Final spinner update
        spinner.stop(f"Successfully generated all reports in {output_dir}")
        logger.info(f"Report generation completed successfully")
        
    except Exception as e:
        error_msg = f"Error generating reports: {str(e)}"
        spinner.stop(f"Error generating reports: {str(e)}")
        logger.error(error_msg)
        raise Exception(error_msg)