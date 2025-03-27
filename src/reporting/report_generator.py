"""
Report generation module for the Hackathon Analyzer.
"""

import os
import json
import pandas as pd
from typing import Dict, List, Any
from pathlib import Path
from datetime import datetime

from src.utils.logger import logger


def format_date(date_string: str) -> str:
    """Format ISO date string to a more readable format."""
    if not date_string or date_string == "N/A":
        return "N/A"
    try:
        date_obj = datetime.fromisoformat(date_string.replace("Z", "+00:00"))
        return date_obj.strftime("%Y-%m-%d")
    except Exception:
        return date_string


def format_size(size_kb: int) -> str:
    """Format size in KB to a more readable format."""
    if size_kb < 1024:
        return f"{size_kb} KB"
    else:
        size_mb = size_kb / 1024
        return f"{size_mb:.1f} MB"


def generate_reports(
    results: List[Dict[str, Any]], output_dir: str = "reports"
) -> None:
    """
    Generate reports from analysis results.

    Args:
        results: List of project analysis results
        output_dir: Directory to save reports
    """
    try:
        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Create reports directory for individual project reports
        project_reports_dir = os.path.join(output_dir, "projects")
        Path(project_reports_dir).mkdir(exist_ok=True)

        # Save raw results to JSON for future reference
        logger.debug(f"Saving raw results to {output_dir}/raw_results.json")
        raw_results_path = os.path.join(output_dir, "raw_results.json")
        with open(raw_results_path, "w") as f:
            json.dump(results, f, indent=2)

        # Generate individual project reports
        logger.debug(f"Generating {len(results)} individual project reports")

        successful_projects = []
        failed_projects = []

        for i, project in enumerate(results):
            project_name = project["project_name"]
            sanitized_name = "".join(c if c.isalnum() else "_" for c in project_name)

            # Check if analysis succeeded or failed due to token limits
            if "analysis" in project and "error" in project["analysis"]:
                error_message = project["analysis"]["error"]
                token_count = project["analysis"].get("token_count", "unknown")
                logger.error(
                    f"Skipping report for failed project {project_name}: {error_message}"
                )
                failed_projects.append(
                    {
                        "name": project_name,
                        "url": project.get("project_github_url", ""),
                        "error": error_message,
                        "token_count": token_count,
                    }
                )
                continue

            # Generate project report markdown
            report_content = generate_project_report(project)

            # Save project report
            report_path = os.path.join(project_reports_dir, f"{sanitized_name}.md")
            with open(report_path, "w") as f:
                f.write(report_content)

            successful_projects.append(project)

            # Log progress if verbose
            logger.debug(f"Generated report {i+1}/{len(results)}: {project_name}")

        # Generate summary report
        logger.debug("Generating summary report")
        summary_report = generate_summary_report(results)
        summary_path = os.path.join(output_dir, "summary.md")
        with open(summary_path, "w") as f:
            f.write(summary_report)

        # Generate error report if there are failed projects
        if failed_projects:
            generate_error_report(failed_projects, output_dir)

        # Generate Excel summary
        generate_excel_summary(successful_projects, failed_projects, output_dir)

        # Generate CSV summary
        logger.debug("Generating CSV summary")
        csv_data = []
        for project in results:
            project_data = {
                "Project Name": project["project_name"],
                "GitHub URL": project["project_github_url"],
                "Project URL": project["project_url"],
            }

            # Add analysis data if available
            if "analysis" in project:
                analysis = project["analysis"]

                # Extract code quality score if available
                if "code_quality" in analysis and isinstance(
                    analysis["code_quality"], dict
                ):
                    project_data["Code Quality Score"] = analysis["code_quality"].get(
                        "overall_score", 0
                    )

                # Extract integration status if available
                if "celo_integration" in analysis and isinstance(
                    analysis["celo_integration"], dict
                ):
                    project_data["Blockchain Integration"] = (
                        "Yes"
                        if analysis["celo_integration"].get("integrated", False)
                        else "No"
                    )

            csv_data.append(project_data)

        # Create CSV summary
        csv_path = os.path.join(output_dir, "summary.csv")
        pd.DataFrame(csv_data).to_csv(csv_path, index=False)

        logger.info(f"Reports generated successfully in {output_dir}")

    except Exception as e:
        error_msg = f"Error generating reports: {str(e)}"
        logger.error(error_msg)
        raise


def generate_summary_report(results: List[Dict[str, Any]]) -> str:
    """
    Generate a summary report of all projects.

    Args:
        results: List of project analysis results

    Returns:
        Summary report markdown
    """
    # Calculate statistics
    total_projects = len(results)
    projects_with_celo = 0
    avg_code_quality = 0
    projects_with_code_quality = 0

    for project in results:
        if "analysis" in project and isinstance(project["analysis"], dict):
            analysis = project["analysis"]

            # Check for Celo integration
            if "celo_integration" in analysis and isinstance(
                analysis["celo_integration"], dict
            ):
                if analysis["celo_integration"].get("integrated", False):
                    projects_with_celo += 1

            # Accumulate code quality scores
            if "code_quality" in analysis and isinstance(
                analysis["code_quality"], dict
            ):
                score = analysis["code_quality"].get("overall_score", 0)
                if score > 0:
                    avg_code_quality += score
                    projects_with_code_quality += 1

    # Calculate average code quality if we have any valid scores
    if projects_with_code_quality > 0:
        avg_code_quality /= projects_with_code_quality

    # Generate report content
    report = f"""# Celo Hackathon Analysis Summary

## Overview
- **Total Projects Analyzed**: {total_projects}
- **Projects with Celo Integration**: {projects_with_celo} ({projects_with_celo/total_projects*100:.1f}%)
- **Average Code Quality Score**: {avg_code_quality:.1f}/100

## Project List

| Project | GitHub URL | Code Quality | Celo Integration |
|---------|------------|--------------|------------------|
"""

    # Add each project to the table
    for project in results:
        project_name = project["project_name"]
        github_url = project["project_github_url"]

        # Default values
        code_quality = "N/A"
        celo_integration = "No"

        # Extract actual values if available
        if "analysis" in project and isinstance(project["analysis"], dict):
            analysis = project["analysis"]

            if "code_quality" in analysis and isinstance(
                analysis["code_quality"], dict
            ):
                score = analysis["code_quality"].get("overall_score", 0)
                if score > 0:
                    code_quality = f"{score:.1f}/100"

            if "celo_integration" in analysis and isinstance(
                analysis["celo_integration"], dict
            ):
                if analysis["celo_integration"].get("integrated", False):
                    celo_integration = "Yes"

        # Add row to table
        report += (
            f"| {project_name} | {github_url} | {code_quality} | {celo_integration} |\n"
        )

    # Add report generation timestamp
    report += (
        f"\n\n*Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
    )

    return report


def generate_project_report(project: Dict[str, Any]) -> str:
    """
    Generate a detailed report for a single project.

    Args:
        project: Project analysis result

    Returns:
        Project report markdown
    """
    project_name = project["project_name"]
    project_description = project.get("project_description", "")
    github_url = project.get("project_github_url", "")
    project_url = project.get("project_url", "")

    # Start report with project info
    report = f"""# Project Analysis: {project_name}

## Project Information
- **Name**: {project_name}
- **Description**: {project_description}
- **GitHub URL**: {github_url}
- **Project URL**: {project_url}

"""

    # Check if we have analysis data
    if "analysis" not in project or not isinstance(project["analysis"], dict):
        report += "## Analysis\n\nNo analysis data available for this project.\n"
        return report

    analysis = project["analysis"]

    # Remove deployment information section - we won't include it in the report

    # Repository details
    if (
        "repo_details" in analysis
        and isinstance(analysis["repo_details"], list)
        and analysis["repo_details"]
    ):
        repo = analysis["repo_details"][0]  # Use first repository for now

        report += "## Repository Overview\n\n"

        # Basic repository stats
        report += f"- **Repository**: {repo.get('name', 'N/A')}\n"
        report += f"- **Description**: {repo.get('description', 'N/A')}\n"
        report += f"- **Stars**: {repo.get('stars', 0)}\n"
        report += f"- **Forks**: {repo.get('forks', 0)}\n"
        report += f"- **Open Issues**: {repo.get('open_issues', 0)}\n"
        report += f"- **Last Update**: {format_date(repo.get('last_update', 'N/A'))}\n"
        report += f"- **Created**: {format_date(repo.get('created_at', 'N/A'))}\n"
        report += f"- **Size**: {format_size(repo.get('size_kb', 0))}\n"
        report += f"- **Repository Type**: {repo.get('repo_type', 'Unknown')}\n\n"

        # Language breakdown
        if "main_languages" in repo and repo["main_languages"]:
            report += "### Languages\n\n"
            for lang, percentage in repo["main_languages"].items():
                report += f"- {lang}: {percentage:.1f}%\n"
            report += "\n"

    # LLM analysis results - direct from the repo_analyzer output with minimal modification
    for key, value in analysis.items():
        # Skip repository details (already processed), metadata, code examples, and deployment
        if key in [
            "repo_details",
            "token_metrics",
            "error",
            "code_examples",
            "deployment",
        ]:
            continue

        # Format section header
        section_title = key.replace("_", " ").title()
        report += f"## {section_title}\n\n"

        # For dictionary values, format as subsections
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                # Skip some technical keys
                if sub_key in ["error", "repositories_analyzed", "raw_analysis"]:
                    continue

                # Format subsection header
                sub_title = sub_key.replace("_", " ").title()
                report += f"### {sub_title}\n\n"

                # Format subsection content based on value type
                if isinstance(sub_value, dict):
                    for item_key, item_value in sub_value.items():
                        # Format as lists or paragraphs based on content
                        if isinstance(item_value, (list, tuple)):
                            report += f"#### {item_key.replace('_', ' ').title()}\n\n"
                            for item in item_value:
                                if isinstance(item, dict):
                                    for k, v in item.items():
                                        report += f"- **{k.title()}**: {v}\n"
                                    report += "\n"
                                else:
                                    report += f"- {item}\n"
                            report += "\n"
                        elif (
                            isinstance(item_value, (int, float))
                            and "score" in item_key.lower()
                        ):
                            report += f"**{item_key.replace('_', ' ').title()}**: {item_value}/100\n\n"
                        elif isinstance(item_value, str):
                            report += f"**{item_key.replace('_', ' ').title()}**: {item_value}\n\n"
                        else:
                            report += f"**{item_key.replace('_', ' ').title()}**: {item_value}\n\n"

                # Format lists
                elif isinstance(sub_value, (list, tuple)):
                    for item in sub_value:
                        if isinstance(item, dict):
                            for k, v in item.items():
                                report += f"- **{k.title()}**: {v}\n"
                            report += "\n"
                        else:
                            report += f"- {item}\n"
                    report += "\n"

                # Format simple values
                elif isinstance(sub_value, (int, float)) and "score" in sub_key.lower():
                    report += f"**Score**: {sub_value}/100\n\n"
                else:
                    report += f"{sub_value}\n\n"

        # Format list values
        elif isinstance(value, (list, tuple)):
            for item in value:
                if isinstance(item, dict):
                    for k, v in item.items():
                        report += f"- **{k.title()}**: {v}\n"
                    report += "\n"
                else:
                    report += f"- {item}\n"
            report += "\n"

        # Format simple values
        else:
            report += f"{value}\n\n"

    # Add token metrics if available in verbose mode
    if "token_metrics" in analysis and isinstance(analysis["token_metrics"], dict):
        tokens = analysis["token_metrics"]
        report += "## Token Usage\n\n"
        report += f"- **Input Tokens**: {tokens.get('input_tokens', 'N/A')}\n"
        report += f"- **Output Tokens**: {tokens.get('output_tokens', 'N/A')}\n"
        report += f"- **Total Tokens**: {tokens.get('total_tokens', 'N/A')}\n\n"

    # Add report generation timestamp
    report += f"\n*Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"

    return report


def generate_error_report(
    failed_projects: List[Dict[str, Any]], output_dir: str
) -> None:
    """
    Generate a report of projects that failed analysis.

    Args:
        failed_projects: List of projects that failed analysis
        output_dir: Output directory for the report
    """
    error_path = os.path.join(output_dir, "errors.md")

    # Format error content
    error_report = "# Analysis Errors\n\n"
    error_report += f"## Failed Projects\n\n"
    error_report += f"- **Total Failed Projects**: {len(failed_projects)}\n\n"

    # Create error table
    error_report += "| Project | Repository | Error | Token Count |\n"
    error_report += "|---------|------------|-------|------------|\n"

    for project in failed_projects:
        project_name = project.get("name", "Unknown")
        repo_url = project.get("url", "N/A")
        repo_link = f"[Link]({repo_url})" if repo_url != "N/A" else "N/A"
        error = project.get("error", "Unknown error")
        token_count = project.get("token_count", "N/A")

        error_report += f"| {project_name} | {repo_link} | {error} | {token_count} |\n"

    # Write error report to file
    with open(error_path, "w", encoding="utf-8") as f:
        f.write(error_report)

    logger.debug(f"Generated error report at {error_path}")


def generate_excel_summary(
    successful_projects: List[Dict[str, Any]],
    failed_projects: List[Dict[str, Any]],
    output_dir: str,
) -> None:
    """
    Generate an Excel spreadsheet with a summary of all projects.

    Args:
        successful_projects: List of projects with successful analysis
        failed_projects: List of projects that failed analysis
        output_dir: Output directory for the report
    """
    excel_path = os.path.join(output_dir, "project_summary.xlsx")

    try:
        # Create successful projects dataframe
        success_data = []

        for project in successful_projects:
            project_name = project.get("project_name", "Unknown")
            repo_url = project.get("project_github_url", "N/A")

            analysis = project.get("analysis", {})

            # Code quality metrics
            code_quality = analysis.get("code_quality", {})
            if isinstance(code_quality, dict):
                code_quality_score = code_quality.get("overall_score", "N/A")
            else:
                code_quality_score = "N/A"

            # Celo integration metrics
            celo_integration = analysis.get("celo_integration", {})
            if isinstance(celo_integration, dict):
                celo_integration_score = celo_integration.get("overall_score", "N/A")
                integrated = (
                    "Yes" if celo_integration.get("integrated", False) else "No"
                )
                integration_depth = celo_integration.get(
                    "integration_depth", "none"
                ).capitalize()

                # Features used
                features = celo_integration.get("features_used", [])
                feature_names = [
                    feature.get("feature", "Unknown") for feature in features
                ]
                features_text = ", ".join(feature_names) if feature_names else "None"
            else:
                celo_integration_score = "N/A"
                integrated = "No"
                integration_depth = "None"
                features_text = "None"

            # Architecture metrics
            architecture = analysis.get("architecture", {})
            if isinstance(architecture, dict):
                architecture_score = architecture.get("overall_score", "N/A")
            else:
                architecture_score = "N/A"

            # Repository type info
            repo_type = analysis.get("repo_type", {})
            if isinstance(repo_type, dict):
                production_readiness = repo_type.get("production_readiness", "N/A")
            else:
                production_readiness = "N/A"

            # Create a row for this project
            project_row = {
                "Project Name": project_name,
                "GitHub Repository": repo_url,
                "Code Quality Score": code_quality_score,
                "Celo Integration Score": celo_integration_score,
                "Architecture Score": architecture_score,
                "Production Readiness": production_readiness,
                "Integrated with Celo": integrated,
                "Integration Depth": integration_depth,
                "Celo Features Used": features_text,
            }

            success_data.append(project_row)

        # Create failures dataframe
        failure_data = []

        for project in failed_projects:
            project_name = project.get("name", "Unknown")
            repo_url = project.get("url", "N/A")
            error = project.get("error", "Unknown error")
            token_count = project.get("token_count", "N/A")

            # Create a row for this failed project
            project_row = {
                "Project Name": project_name,
                "GitHub Repository": repo_url,
                "Error": error,
                "Token Count": token_count,
            }

            failure_data.append(project_row)

        # Convert to dataframes
        success_df = pd.DataFrame(success_data) if success_data else pd.DataFrame()
        failure_df = pd.DataFrame(failure_data) if failure_data else pd.DataFrame()

        # Write to Excel
        with pd.ExcelWriter(excel_path) as writer:
            if not success_df.empty:
                success_df.to_excel(
                    writer, sheet_name="Successful Projects", index=False
                )
            if not failure_df.empty:
                failure_df.to_excel(writer, sheet_name="Failed Projects", index=False)

        logger.info(f"Generated Excel summary at {excel_path}")

    except Exception as e:
        logger.error(f"Error generating Excel summary: {e}")
