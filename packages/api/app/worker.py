"""Worker module for background tasks."""

import logging
import re
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import core modules - direct imports from installed packages
from analyzer import analyze_single_repository

# Import logging setup from installed package
from config import setup_logging
from fetcher import fetch_single_repository
from file_parser import extract_repo_name_from_url

from app.config import settings
from app.db.models import AnalysisTask, Report

# Configure logging using centralized setup
setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


def analyze_repository(task_id: str, github_url: str, options: dict):
    """
    Worker function to analyze a GitHub repository.
    This runs in a separate process.

    Args:
        task_id: Task ID
        github_url: GitHub repository URL
        options: Analysis options
    """
    # Create DB engine and session
    engine = create_engine(settings.DATABASE_URL.replace("+aiosqlite", ""))
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # Update task status
        task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
        if not task:
            logger.error(f"Task {task_id} not found")
            return

        task.status = "in_progress"
        task.progress = 10
        db.commit()

        # Step 1: Fetch repository content
        repo_name, repo_data = fetch_single_repository(
            github_url, include_metrics=True, github_token=settings.GITHUB_TOKEN
        )

        if not repo_data or not repo_data["content"]:
            raise Exception(f"Failed to fetch repository: {github_url}")

        # Extract repo name if not returned by fetcher
        if not repo_name:
            repo_name = extract_repo_name_from_url(github_url)

        # Update progress
        task.progress = 40
        db.commit()

        # Step 2: Analyze repository
        code_digest = repo_data["content"]
        metrics = repo_data.get("metrics", {})

        # Get analysis options
        model = options.get("model", settings.DEFAULT_MODEL)
        temperature = float(options.get("temperature", settings.TEMPERATURE))

        # Override model based on analysis_type if present
        analysis_type = options.get("analysis_type", "fast")
        if analysis_type == "fast":
            model = "gemini-2.5-flash-preview-04-17"  # Fast model
        elif analysis_type == "deep":
            model = "gemini-2.5-pro-preview-03-25"  # Deep model

        # Update the task's analysis_type field
        task.analysis_type = analysis_type
        db.commit()

        # Set the correct path to the prompt file
        # If prompt is just a name, assume it's in the prompts directory
        prompt_option = options.get("prompt", "default")

        # Make sure it has the .txt extension
        if not prompt_option.endswith(".txt"):
            prompt_option = f"{prompt_option}.txt"

        if "/" not in prompt_option:
            # Use the shared config prompts directory
            config_root = project_root / "config"
            prompt_path = config_root / "prompts" / prompt_option
        else:
            prompt_path = prompt_option

        analysis = analyze_single_repository(
            repo_name,
            code_digest,
            prompt_path,
            model_name=model,
            temperature=temperature,
            output_json=False,
            metrics_data=metrics,
        )

        # Update progress
        task.progress = 80
        db.commit()

        # Step 3: Create report
        # Extract scores from the markdown analysis
        if not isinstance(analysis, str):
            logger.error(f"Unexpected analysis result type: {type(analysis)}")
            # Convert to string if not already
            if isinstance(analysis, dict) and "raw_text" in analysis:
                # Extract from error object
                analysis_text = analysis["raw_text"]
            elif isinstance(analysis, dict) and "raw_markdown" in analysis:
                # Extract from markdown wrapper
                analysis_text = analysis["raw_markdown"]
            else:
                # Convert dict to string or use error message
                try:
                    import json

                    analysis_text = f"Error: Received JSON instead of markdown:\n```json\n{json.dumps(analysis, indent=2)}\n```"
                except Exception:
                    analysis_text = "Error: Failed to generate report. Please try again."
        else:
            # Already a string
            analysis_text = analysis

        # Extract scores from markdown
        scores = extract_scores_from_markdown(analysis_text)

        # Create the report with markdown content and use the same ID as the task
        report = Report(
            id=task_id,  # Use the same ID as the task for easier UI integration
            task_id=task_id,
            user_id=task.user_id,
            github_url=github_url,
            repo_name=repo_name,
            content={
                "markdown": analysis_text
            },  # Store as a JSON with markdown key for compatibility
            scores=scores,
            analysis_type=analysis_type,  # Store analysis type in report
        )

        db.add(report)

        # Update task status
        task.status = "completed"
        task.progress = 100
        task.completed_at = datetime.utcnow()

        # Commit all changes
        db.commit()

    except Exception as e:
        logger.error(f"Error analyzing repository for task {task_id}: {str(e)}")

        # Update task status on error
        try:
            task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
            if task:
                task.status = "failed"
                task.error_message = str(e)
                db.commit()
        except Exception as commit_error:
            logger.error(f"Error updating task status: {str(commit_error)}")

    finally:
        db.close()


def extract_scores(analysis):
    """
    Extract scores from analysis result for quick access.

    Args:
        analysis: Analysis result

    Returns:
        dict: Extracted scores
    """
    if not isinstance(analysis, dict):
        return {"overall": 0}

    # Special case for markdown content - try to extract scores from markdown tables
    if "type" in analysis and analysis["type"] == "markdown" and "raw_markdown" in analysis:
        return extract_scores_from_markdown(analysis["raw_markdown"])

    # Check if this is an error object
    if "error" in analysis:
        return {"overall": 0}

    scores = {}

    # Extract category scores
    categories = ["readability", "standards", "complexity", "testing", "security"]
    for category in categories:
        if category in analysis and isinstance(analysis[category], dict):
            scores[category] = analysis[category].get("score", 0)

    # Add overall score if available
    if "overall" in analysis and isinstance(analysis["overall"], dict):
        scores["overall"] = analysis["overall"].get("score", 0)
    elif len(scores) > 0:
        # Calculate average if no overall score is provided
        scores["overall"] = sum(scores.values()) / len(scores)
    else:
        # Default overall score if no scores are found
        scores["overall"] = 0

    return scores


def extract_scores_from_markdown(markdown_text):
    """
    Extract scores from markdown text, typically from tables.

    Args:
        markdown_text: Markdown text to extract scores from

    Returns:
        dict: Extracted scores
    """
    scores = {}

    # Look for score patterns like "7/10" or "7.5/10"
    score_pattern = r"(\w+)\s*\|\s*([0-9.]+)/10\s*\|"
    matches = re.findall(score_pattern, markdown_text)

    for category, score in matches:
        # Clean up category name (lowercase, remove special characters)
        clean_category = category.strip().lower()
        clean_category = re.sub(r"[^a-zA-Z0-9]", "_", clean_category)

        try:
            # Convert score to float
            scores[clean_category] = float(score.strip())
        except ValueError:
            continue

    # Extract overall score specifically
    overall_pattern = r"overall.*\|\s*([0-9.]+)/10\s*\|"
    overall_match = re.search(overall_pattern, markdown_text, re.IGNORECASE)

    if overall_match:
        try:
            scores["overall"] = float(overall_match.group(1).strip())
        except ValueError:
            pass
    elif len(scores) > 0:
        # Calculate average if no overall score is found
        scores["overall"] = sum(scores.values()) / len(scores)
    else:
        # Default overall score if no scores are found
        scores["overall"] = 0

    return scores
