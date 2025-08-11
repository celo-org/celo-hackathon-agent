"""Worker module for background tasks."""

import asyncio
import logging
import re
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

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


async def analyze_repository_async(task_id: str, github_url: str, options: dict):
    """
    Async worker function to analyze a GitHub repository.
    This runs in a separate process but uses async SQLAlchemy for proper DB sync.

    Args:
        task_id: Task ID
        github_url: GitHub repository URL
        options: Analysis options
    """
    # Create async DB engine and session (same as API)
    DATABASE_URL = str(settings.DATABASE_URL).replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(DATABASE_URL)
    async_session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session_factory() as db:
        try:
            # Update task status
            from sqlalchemy import select

            stmt = select(AnalysisTask).where(AnalysisTask.id == task_id)
            result = await db.execute(stmt)
            task = result.scalar_one_or_none()

            if not task:
                logger.error(f"Task {task_id} not found")
                return

            task.status = "in_progress"
            task.progress = 10
            await db.commit()
            logger.debug(f"[WORKER] Updated task {task_id} to in_progress, progress: 10%")

            # Step 1: Fetch repository content
            # Run the sync fetcher in a thread pool to avoid async event loop conflicts
            import concurrent.futures

            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = loop.run_in_executor(
                    executor,
                    fetch_single_repository,
                    github_url,
                    True,  # include_metrics
                    settings.GITHUB_TOKEN,
                )
                repo_name, repo_data = await future

            logger.debug(f"[WORKER] Fetched repository data for {repo_name}")

            if not repo_data or not repo_data.get("content"):
                logger.error(f"[WORKER] Repository data is empty or missing content: {repo_data}")
                raise Exception(f"Failed to fetch repository: {github_url}")

            # Extract repo name if not returned by fetcher
            if not repo_name:
                repo_name = extract_repo_name_from_url(github_url)
                logger.debug(f"[WORKER] Extracted repo name from URL: {repo_name}")

            # Update progress
            task.progress = 40
            await db.commit()
            logger.debug(f"[WORKER] Updated task {task_id} progress: 40%")

            # Step 2: Analyze repository
            code_digest = repo_data["content"]
            metrics = repo_data.get("metrics", {})

            logger.debug(f"[WORKER] Code digest length: {len(code_digest) if code_digest else 0}")
            logger.debug(f"[WORKER] Metrics keys: {list(metrics.keys()) if metrics else []}")

            if not code_digest or "Error fetching repository" in code_digest:
                raise Exception(
                    f"Failed to fetch repository content: {code_digest[:200] if code_digest else 'No content'}"
                )

            # Validate API key before proceeding
            if not settings.GOOGLE_API_KEY or settings.GOOGLE_API_KEY == "your_gemini_api_key_here":
                raise Exception(
                    "GOOGLE_API_KEY is not configured. Please set a valid Gemini API key in your .env file."
                )

            # Get analysis options
            model = options.get("model", settings.DEFAULT_MODEL)

            # Safe temperature conversion with fallback
            temp_value = options.get("temperature", settings.TEMPERATURE)
            if temp_value is None or temp_value == "":
                temperature = 0.2  # Default fallback
            else:
                try:
                    temperature = float(temp_value)
                except (ValueError, TypeError):
                    temperature = 0.2  # Default fallback if conversion fails

            logger.debug(f"[WORKER] Using temperature: {temperature}")

            # Override model based on analysis_type if present
            analysis_type = options.get("analysis_type", "fast")
            if analysis_type == "fast":
                model = "gemini-2.5-flash"  # Fast model
            elif analysis_type == "deep":
                model = "gemini-2.5-flash"  # Deep model

            # Update the task's analysis_type field
            task.analysis_type = analysis_type
            await db.commit()

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

            logger.debug(f"Starting LLM analysis for {repo_name} using model {model}")

            try:
                # Run the LLM analysis in a thread pool to avoid potential async conflicts
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = loop.run_in_executor(
                        executor,
                        analyze_single_repository,
                        repo_name,
                        code_digest,
                        prompt_path,
                        model,  # model_name
                        temperature,
                        False,  # output_json
                        metrics,  # metrics_data
                    )
                    analysis = await future
                logger.debug(f"LLM analysis completed for {repo_name}")
            except Exception as llm_error:
                logger.error(f"LLM analysis failed for {repo_name}: {str(llm_error)}")
                raise Exception(f"LLM analysis failed: {str(llm_error)}")

            # Update progress
            task.progress = 80
            await db.commit()
            logger.debug(f"[WORKER] Updated task {task_id} progress: 80%")

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
            await db.commit()
            logger.debug(
                f"[WORKER] Task {task_id} completed successfully! Status: completed, Progress: 100%"
            )

        except Exception as e:
            logger.error(f"Error analyzing repository for task {task_id}: {str(e)}")

            # Update task status on error
            try:
                stmt = select(AnalysisTask).where(AnalysisTask.id == task_id)
                result = await db.execute(stmt)
                task = result.scalar_one_or_none()
                if task:
                    task.status = "failed"
                    task.error_message = str(e)
                    await db.commit()
                    logger.debug(f"[WORKER] Task {task_id} failed. Status: failed")
            except Exception as commit_error:
                logger.error(f"Error updating task status: {str(commit_error)}")

        finally:
            await engine.dispose()


def analyze_repository(task_id: str, github_url: str, options: dict):
    """
    Sync wrapper for the async worker function.
    This is called by the queue system.
    """
    try:
        # Run the async function
        asyncio.run(analyze_repository_async(task_id, github_url, options))
    except Exception as e:
        logger.error(f"Worker failed for task {task_id}: {str(e)}")


def extract_scores(analysis):
    """
    Extract scores from analysis result.

    Args:
        analysis: Analysis result (string or dict)

    Returns:
        dict: Extracted scores
    """
    if isinstance(analysis, dict) and "scores" in analysis:
        return analysis["scores"]

    # If it's a string (markdown), extract scores from text
    if isinstance(analysis, str):
        return extract_scores_from_markdown(analysis)

    return {}


def extract_scores_from_markdown(markdown_text):
    """
    Extract numerical scores from markdown text using regex patterns.

    Args:
        markdown_text: The markdown content to parse

    Returns:
        dict: Dictionary of extracted scores
    """
    scores = {}

    # Common score patterns to look for
    patterns = {
        "overall": [
            r"overall.*?score.*?(\d+(?:\.\d+)?)",
            r"total.*?score.*?(\d+(?:\.\d+)?)",
            r"final.*?score.*?(\d+(?:\.\d+)?)",
        ],
        "code_quality": [r"code.*?quality.*?(\d+(?:\.\d+)?)", r"quality.*?score.*?(\d+(?:\.\d+)?)"],
        "maintainability": [r"maintainability.*?(\d+(?:\.\d+)?)", r"maintenance.*?(\d+(?:\.\d+)?)"],
        "documentation": [r"documentation.*?(\d+(?:\.\d+)?)", r"docs.*?score.*?(\d+(?:\.\d+)?)"],
        "performance": [r"performance.*?(\d+(?:\.\d+)?)", r"speed.*?score.*?(\d+(?:\.\d+)?)"],
    }

    # Convert to lowercase for easier matching
    text_lower = markdown_text.lower()

    for category, pattern_list in patterns.items():
        for pattern in pattern_list:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                try:
                    scores[category] = float(matches[0])
                    break  # Use first match for this category
                except (ValueError, IndexError):
                    continue

    return scores
