"""
Reporter module for the AI Project Analyzer.

This module handles saving analysis reports to files in various formats.
"""
import logging
import os
import json
from typing import Dict, List, Any, Union, Optional
from datetime import datetime
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# Supported report formats
REPORT_FORMATS = ["md", "json", "html", "csv"]


def ensure_directory_exists(directory: str) -> None:
    """
    Ensure that the directory exists, create it if it doesn't.
    
    Args:
        directory: Directory path to check/create
    """
    os.makedirs(directory, exist_ok=True)
    logger.debug(f"Ensured directory exists: {directory}")


def generate_report_directory(base_output_dir: str) -> str:
    """
    Generate a timestamped directory for reports.
    
    Args:
        base_output_dir: Base directory for reports
        
    Returns:
        str: Path to the timestamped directory
    """
    # Create timestamp-based directory
    timestamp = datetime.now().strftime("%m-%d-%Y-%H%M")
    report_dir = os.path.join(base_output_dir, timestamp)
    
    # Ensure the directory exists
    ensure_directory_exists(report_dir)
    
    return report_dir


def generate_filename(repo_name: str) -> str:
    """
    Generate a filename for the report.
    
    Args:
        repo_name: Name of the repository
        
    Returns:
        str: Generated filename
    """
    # Replace slashes with hyphens for file safety
    safe_name = repo_name.replace("/", "-")
    
    return f"{safe_name}-analysis.md"


def save_report(repo_name: str, analysis, output_dir: str) -> str:
    """
    Save an individual analysis report to a file.
    
    Args:
        repo_name: Name of the repository
        analysis: Analysis report content (string or dictionary)
        output_dir: Directory to save the report
        
    Returns:
        str: Path to the saved report file
    """
    # Ensure the output directory exists
    ensure_directory_exists(output_dir)
    
    # Determine if we're dealing with JSON or Markdown
    is_json = isinstance(analysis, dict)
    
    # Generate filename with appropriate extension
    file_ext = "json" if is_json else "md"
    base_filename = generate_filename(repo_name)
    filename = f"{os.path.splitext(base_filename)[0]}.{file_ext}"
    
    # Full path to the report file
    report_path = os.path.join(output_dir, filename)
    
    # Save the report based on its type
    if is_json:
        # Add metadata to JSON
        analysis_with_metadata = {
            "repository": repo_name,
            "generated_at": datetime.now().isoformat(),
            "analysis": analysis
        }
        
        # Save as JSON
        with open(report_path, "w", encoding="utf-8") as f:
            import json
            json.dump(analysis_with_metadata, f, indent=2)
    else:
        # For markdown, add header with repository name and timestamp
        header = f"# Analysis Report: {repo_name}\n\n"
        header += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Handle error messages specially
        if isinstance(analysis, str) and analysis.startswith("Error:"):
            header += f"\n## Error\n\n{analysis}\n"
            content = header
        else:
            content = header + analysis
        
        # Save as Markdown
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(content)
    
    logger.info(f"Saved report to {report_path}")
    return report_path


def extract_scores_from_markdown(markdown_content: str) -> Dict[str, int]:
    """
    Extract scores from markdown analysis content.
    
    Args:
        markdown_content: Markdown-formatted analysis text
        
    Returns:
        Dict[str, int]: Dictionary of extracted scores
    """
    scores = {}
    
    # First try to extract from the score table (preferred method)
    table_pattern = r"\|\s*([^|]+)\s*\|\s*(\d+)\s*\|"
    table_matches = re.findall(table_pattern, markdown_content)
    
    if table_matches:
        for criterion, score_str in table_matches:
            criterion = criterion.strip().lower()
            try:
                score = int(score_str.strip())
                
                # Map various criteria names to standardized keys
                if "security" in criterion:
                    scores["security"] = score
                elif any(term in criterion for term in ["function", "correct"]):
                    scores["functionality"] = score
                elif any(term in criterion for term in ["read", "understand"]):
                    scores["readability"] = score
                elif any(term in criterion for term in ["depend", "setup"]):
                    scores["dependencies"] = score
                elif any(term in criterion for term in ["evidence", "technical", "usage", "celo"]):
                    scores["evidence"] = score
                elif "overall" in criterion:
                    scores["overall"] = score
            except ValueError:
                continue
    
    # If we couldn't find scores in a table, try individual patterns as fallback
    if not scores or len(scores) < 5:
        # Define patterns to look for
        patterns = {
            "security": r"Security:?\s+(?:score)?\s*[:-]?\s*(\d+)",
            "functionality": r"Functionality\s*(?:&|and)\s*Correctness:?\s+(?:score)?\s*[:-]?\s*(\d+)",
            "readability": r"Readability:?\s+(?:score)?\s*[:-]?\s*(\d+)|Readability\s*(?:&|and)\s*Understandability:?\s+(?:score)?\s*[:-]?\s*(\d+)",
            "dependencies": r"Dependencies\s*(?:&|and)\s*Setup:?\s+(?:score)?\s*[:-]?\s*(\d+)",
            "evidence": r"Evidence\s+of\s+(?:Technical|Celo)\s+Usage:?\s+(?:score)?\s*[:-]?\s*(\d+)",
            "overall": r"Overall\s*(?:Score)?:?\s+(?:score)?\s*[:-]?\s*(\d+)"
        }
        
        # Extract scores using regex
        for score_name, pattern in patterns.items():
            match = re.search(pattern, markdown_content, re.IGNORECASE)
            if match:
                try:
                    # If there are multiple capture groups, find the first non-None one
                    capture_groups = match.groups()
                    score_str = next((g for g in capture_groups if g is not None), None)
                    if score_str:
                        scores[score_name] = int(score_str)
                except (ValueError, IndexError):
                    logger.warning(f"Could not extract {score_name} score")
    
    # If we still don't have an overall score but have other scores, calculate it
    if "overall" not in scores and len(scores) >= 3:
        other_scores = [s for k, s in scores.items() if k != "overall"]
        if other_scores:
            scores["overall"] = round(sum(other_scores) / len(other_scores))
    
    return scores




def create_summary_report(analyses: Dict[str, Union[str, Dict[str, Any]]], output_dir: str) -> str:
    """
    Create a summary report of all analyzed repositories.
    
    Args:
        analyses: Dictionary mapping repository names to their analysis results
        output_dir: Directory to save the summary report
        
    Returns:
        str: Path to the summary report file
    """
    # Ensure the output directory exists
    ensure_directory_exists(output_dir)
    
    # Create filename
    summary_path = os.path.join(output_dir, "summary-report.md")
    
    # Extract scores from each analysis
    all_scores = {}
    
    for repo_name, analysis in analyses.items():
        if isinstance(analysis, dict):
            # Handle JSON format
            if "analysis" in analysis and isinstance(analysis["analysis"], dict):
                scores = {}
                # Extract scores from structured data
                for category in ["readability", "standards", "complexity", "testing", "overall"]:
                    if category in analysis["analysis"]:
                        score_data = analysis["analysis"][category]
                        if isinstance(score_data, dict) and "score" in score_data:
                            scores[category] = score_data["score"]
                all_scores[repo_name] = scores
        elif isinstance(analysis, str):
            # Handle markdown format
            scores = extract_scores_from_markdown(analysis)
            if scores:
                all_scores[repo_name] = scores
    
    # Generate markdown summary
    summary_content = "# Analysis Summary Report\n\n"
    summary_content += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    summary_content += f"## Repositories Analyzed: {len(analyses)}\n\n"
    
    # Add score table
    summary_content += "## Score Summary\n\n"
    summary_content += "| Repository | Security | Functionality | Readability | Dependencies | Evidence | Overall |\n"
    summary_content += "|------------|----------|--------------|-------------|--------------|----------|----------|\n"
    
    for repo_name, scores in all_scores.items():
        security = scores.get("security", "N/A")
        functionality = scores.get("functionality", "N/A")
        readability = scores.get("readability", "N/A")
        dependencies = scores.get("dependencies", "N/A")
        evidence = scores.get("evidence", "N/A")
        overall = scores.get("overall", "N/A")
        
        summary_content += f"| {repo_name} | {security} | {functionality} | {readability} | {dependencies} | {evidence} | {overall} |\n"
    
    # Add average scores if we have data
    if all_scores:
        summary_content += "\n## Average Scores\n\n"
        categories = ["security", "functionality", "readability", "dependencies", "evidence", "overall"]
        
        for category in categories:
            scores = [repo_scores.get(category, 0) for repo_scores in all_scores.values() 
                      if isinstance(repo_scores.get(category, 0), int)]
            
            if scores:
                avg_score = sum(scores) / len(scores)
                summary_content += f"- **{category.title()}**: {avg_score:.1f}\n"
    
    # List all reports
    summary_content += "\n## Individual Reports\n\n"
    for repo_name in analyses.keys():
        summary_content += f"- [{repo_name}](./)\n"
    
    # Save summary
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary_content)
    
    logger.info(f"Saved summary report to {summary_path}")
    return summary_path


def save_reports(analyses: Dict[str, Union[str, Dict[str, Any]]], base_output_dir: str) -> Dict[str, str]:
    """
    Save multiple analysis reports to files and generate summary.
    
    Args:
        analyses: Dictionary mapping repository names to their analysis results
        base_output_dir: Base directory for saving reports
        
    Returns:
        Dict[str, str]: Dictionary mapping repository names to their report file paths
    """
    results = {}
    
    # Create timestamped directory for this batch of reports
    report_dir = generate_report_directory(base_output_dir)
    logger.info(f"Saving reports to directory: {report_dir}")
    
    # Save individual reports
    for repo_name, analysis in analyses.items():
        try:
            report_path = save_report(repo_name, analysis, report_dir)
            results[repo_name] = report_path
        except Exception as e:
            logger.error(f"Error saving report for {repo_name}: {str(e)}")
    
    # Generate summary report if we have more than one analysis
    if len(analyses) > 1:
        try:
            summary_path = create_summary_report(analyses, report_dir)
            results["__summary__"] = summary_path
        except Exception as e:
            logger.error(f"Error creating summary report: {str(e)}")
    
    return results