"""
Reporter module for the AI Project Analyzer.

This module handles saving analysis reports to files in various formats.
"""

import logging
import os
from typing import Dict, Any, Union
from datetime import datetime
import re

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
            "analysis": analysis,
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


def extract_scores_from_markdown(markdown_content: str) -> Dict[str, float]:
    """
    Extract scores from markdown analysis content.

    Args:
        markdown_content: Markdown-formatted analysis text

    Returns:
        Dict[str, float]: Dictionary of extracted scores (0-10 scale with decimals)
    """
    scores = {}

    # For debugging
    logger.debug(f"Extracting scores from markdown content of length: {len(markdown_content)}")

    # Check for the special case where content is wrapped in ```markdown blocks
    if markdown_content.startswith("```markdown") or markdown_content.startswith("```"):
        logger.debug(
            "Content appears to be wrapped in markdown code blocks, extracting inner content"
        )
        lines = markdown_content.splitlines()
        # Find the first and last code block markers
        start_idx = next((i for i, line in enumerate(lines) if line.startswith("```")), 0)
        end_idx = (
            len(lines) - 1 - next((i for i, line in enumerate(reversed(lines)) if line == "```"), 0)
        )

        # Extract the content between the markers (if they exist)
        if start_idx < end_idx:
            # Skip the first line with ```markdown
            inner_content = "\n".join(lines[start_idx + 1 : end_idx])
            if inner_content:
                logger.debug(f"Extracted inner markdown content of length: {len(inner_content)}")
                markdown_content = inner_content

    # First try to extract from the score table (preferred method)
    # Pattern looks for a number that can be an integer or decimal followed by /10 (e.g., 8/10 or 8.5/10)
    table_pattern = r"\|\s*([^|]+)\s*\|\s*(\d+(?:\.\d+)?)(?:/10)?\s*\|"
    table_matches = re.findall(table_pattern, markdown_content)
    logger.debug(f"Found {len(table_matches)} potential score matches in table format")

    if table_matches:
        for criterion, score_str in table_matches:
            criterion = criterion.strip().lower()
            try:
                # Remove "/10" if present in the score string
                score_str = score_str.strip().replace("/10", "").strip()
                score = float(score_str)

                # Log what we found
                logger.debug(f"Found score: {score} for criterion: {criterion}")

                # If the score is on a 0-100 scale, convert to 0-10
                if score > 10:
                    score = round(score / 10, 1)
                    logger.debug(f"Converted to 0-10 scale: {score}")

                # Map various criteria names to standardized keys
                if "security" in criterion:
                    scores["security"] = score
                    logger.debug(f"Mapped to security: {score}")
                elif any(term in criterion for term in ["function", "correct"]):
                    scores["functionality"] = score
                    logger.debug(f"Mapped to functionality: {score}")
                elif any(term in criterion for term in ["read", "understand"]):
                    scores["readability"] = score
                    logger.debug(f"Mapped to readability: {score}")
                elif any(term in criterion for term in ["depend", "setup"]):
                    scores["dependencies"] = score
                    logger.debug(f"Mapped to dependencies: {score}")
                elif any(term in criterion for term in ["evidence", "technical", "usage", "celo"]):
                    scores["evidence"] = score
                    logger.debug(f"Mapped to evidence: {score}")
                elif "overall" in criterion:
                    scores["overall"] = score
                    logger.debug(f"Mapped to overall: {score}")
                else:
                    logger.debug(f"Could not map criterion: {criterion}")
            except ValueError as e:
                logger.warning(f"Error parsing score '{score_str}': {e}")
                continue

    # If we couldn't find scores in a table, try individual patterns as fallback
    if not scores or len(scores) < 5:
        logger.debug(f"Falling back to individual patterns (current scores: {scores})")
        # Define patterns to look for (allowing for decimal scores with optional /10)
        patterns = {
            "security": r"Security:?\s+(?:score)?\s*[:-]?\s*(\d+(?:\.\d+)?)(?:/10)?",
            "functionality": r"Functionality\s*(?:&|and)\s*Correctness:?\s+(?:score)?\s*[:-]?\s*(\d+(?:\.\d+)?)(?:/10)?",
            "readability": r"Readability:?\s+(?:score)?\s*[:-]?\s*(\d+(?:\.\d+)?)(?:/10)?|Readability\s*(?:&|and)\s*Understandability:?\s+(?:score)?\s*[:-]?\s*(\d+(?:\.\d+)?)(?:/10)?",
            "dependencies": r"Dependencies\s*(?:&|and)\s*Setup:?\s+(?:score)?\s*[:-]?\s*(\d+(?:\.\d+)?)(?:/10)?",
            "evidence": r"Evidence\s+of\s+(?:Technical|Celo)\s+Usage:?\s+(?:score)?\s*[:-]?\s*(\d+(?:\.\d+)?)(?:/10)?",
            "overall": r"Overall\s*(?:Score)?:?\s+(?:score)?\s*[:-]?\s*(\d+(?:\.\d+)?)(?:/10)?",
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
                        # Remove "/10" if present in the score string
                        score_str = score_str.strip().replace("/10", "").strip()
                        score = float(score_str)
                        logger.debug(f"Found {score_name} score: {score} using pattern")

                        # If the score is on a 0-100 scale, convert to 0-10
                        if score > 10:
                            score = round(score / 10, 1)
                            logger.debug(f"Converted to 0-10 scale: {score}")

                        scores[score_name] = score
                except (ValueError, IndexError) as e:
                    logger.warning(f"Could not extract {score_name} score: {e}")

    # If we still don't have an overall score but have other scores, calculate it
    if "overall" not in scores and len(scores) >= 3:
        other_scores = [s for k, s in scores.items() if k != "overall"]
        if other_scores:
            scores["overall"] = round(sum(other_scores) / len(other_scores), 1)
            logger.debug(
                f"Calculated overall score: {scores['overall']} from {len(other_scores)} scores"
            )

    logger.debug(f"Final extracted scores: {scores}")
    return scores


def update_summary_report(
    analyses: Dict[str, Union[str, Dict[str, Any]]],
    output_dir: str,
    total_repos: int,
    repos_completed: int,
) -> str:
    """
    Create or update a summary report of analyzed repositories, showing progress.

    Args:
        analyses: Dictionary mapping repository names to their analysis results
        output_dir: Directory to save the summary report
        total_repos: Total number of repositories to be analyzed
        repos_completed: Number of repositories that have been completed

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

    # Show progress information with visual progress bar
    progress_percentage = (repos_completed / total_repos) * 100 if total_repos > 0 else 0
    bar_length = 30
    filled_length = int(bar_length * repos_completed // total_repos)
    progress_bar = "█" * filled_length + "░" * (bar_length - filled_length)

    summary_content += f"## Progress: {repos_completed}/{total_repos} Repositories Analyzed ({progress_percentage:.1f}%)\n"
    summary_content += f"```\n[{progress_bar}]\n```\n\n"

    # Add status with timestamps
    summary_content += f"- Analysis started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    if repos_completed == total_repos:
        summary_content += f"- Analysis completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    else:
        summary_content += (
            f"- Analysis in progress: {repos_completed} of {total_repos} repositories analyzed\n"
        )
    summary_content += "\n"

    # Add score table
    summary_content += "## Score Summary\n\n"
    summary_content += "| Repository | Security | Functionality | Readability | Dependencies | Evidence | Overall |\n"
    summary_content += "|------------|----------|--------------|-------------|--------------|----------|----------|\n"

    for repo_name, scores in all_scores.items():
        # Format scores to show on 0-10 scale with one decimal place
        security = (
            f"{scores.get('security', 'N/A')}/10" if scores.get("security") != "N/A" else "N/A"
        )
        functionality = (
            f"{scores.get('functionality', 'N/A')}/10"
            if scores.get("functionality") != "N/A"
            else "N/A"
        )
        readability = (
            f"{scores.get('readability', 'N/A')}/10"
            if scores.get("readability") != "N/A"
            else "N/A"
        )
        dependencies = (
            f"{scores.get('dependencies', 'N/A')}/10"
            if scores.get("dependencies") != "N/A"
            else "N/A"
        )
        evidence = (
            f"{scores.get('evidence', 'N/A')}/10" if scores.get("evidence") != "N/A" else "N/A"
        )
        overall = f"{scores.get('overall', 'N/A')}/10" if scores.get("overall") != "N/A" else "N/A"

        summary_content += f"| {repo_name} | {security} | {functionality} | {readability} | {dependencies} | {evidence} | {overall} |\n"

    # Add average scores if we have data
    if all_scores:
        summary_content += "\n## Average Scores\n\n"
        categories = [
            "security",
            "functionality",
            "readability",
            "dependencies",
            "evidence",
            "overall",
        ]

        for category in categories:
            scores = [
                repo_scores.get(category, 0)
                for repo_scores in all_scores.values()
                if isinstance(repo_scores.get(category, 0), (int, float))
            ]

            if scores:
                avg_score = sum(scores) / len(scores)
                summary_content += f"- **{category.title()}**: {avg_score:.1f}/10\n"

    # List completed reports
    summary_content += "\n## Individual Reports\n\n"
    for repo_name in analyses.keys():
        safe_name = repo_name.replace("/", "-")
        report_name = f"{safe_name}-analysis.md"
        summary_content += f"- [{repo_name}](./{report_name})\n"

    # Add pending repositories if not all are completed
    if repos_completed < total_repos:
        summary_content += "\n## Pending Repositories\n\n"
        summary_content += (
            f"There are {total_repos - repos_completed} repositories pending analysis.\n"
        )

    # Save summary
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary_content)

    logger.info(f"Updated summary report at {summary_path}")
    return summary_path


def create_summary_report(analyses: Dict[str, Union[str, Dict[str, Any]]], output_dir: str) -> str:
    """
    Create a summary report of all analyzed repositories.

    Args:
        analyses: Dictionary mapping repository names to their analysis results
        output_dir: Directory to save the summary report

    Returns:
        str: Path to the summary report file
    """
    # Call the updated function with completed = total
    return update_summary_report(analyses, output_dir, len(analyses), len(analyses))


def save_single_report(
    repo_name: str,
    analysis: Union[str, Dict[str, Any]],
    report_dir: str,
    total_repos: int,
    completed_repos: int,
    current_analyses: Dict[str, Union[str, Dict[str, Any]]] = None,
) -> Dict[str, str]:
    """
    Save a single repository analysis report and update the summary.

    Args:
        repo_name: Name of the repository
        analysis: Analysis result for the repository
        report_dir: Directory to save the report
        total_repos: Total number of repositories to be analyzed
        completed_repos: Number of repositories completed including this one
        current_analyses: Current collection of analyses to include in summary

    Returns:
        Dict[str, str]: Dictionary mapping repository names to their report file paths
    """
    results = {}

    # Save the individual report
    try:
        report_path = save_report(repo_name, analysis, report_dir)
        results[repo_name] = report_path

        # Update the analyses dict for the summary
        if current_analyses is None:
            current_analyses = {}
        current_analyses[repo_name] = analysis

        # Update the summary report
        try:
            summary_path = update_summary_report(
                current_analyses, report_dir, total_repos, completed_repos
            )
            results["__summary__"] = summary_path
        except Exception as e:
            logger.error(f"Error updating summary report: {str(e)}")

    except Exception as e:
        logger.error(f"Error saving report for {repo_name}: {str(e)}")

    return results


def save_reports(
    analyses: Dict[str, Union[str, Dict[str, Any]]], base_output_dir: str
) -> Dict[str, str]:
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
