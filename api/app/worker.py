"""Worker module for background tasks."""

import logging
import os
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.append(project_root)

from app.config import settings
from app.db.models import AnalysisTask, Report

# Import CLI analysis tools
from src.fetcher import fetch_single_repository
from src.analyzer import analyze_single_repository
from src.file_parser import extract_repo_name_from_url

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
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
    logger.info(f"Starting analysis for task {task_id}: {github_url}")
    
    # Create DB engine and session
    engine = create_engine(settings.DATABASE_URL.replace('+aiosqlite', ''))
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
        logger.info(f"Fetching repository: {github_url}")
        repo_name, repo_data = fetch_single_repository(
            github_url, 
            include_metrics=True,
            github_token=settings.GITHUB_TOKEN
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
        logger.info(f"Analyzing repository: {repo_name}")
        code_digest = repo_data["content"]
        metrics = repo_data.get("metrics", {})
        
        # Get analysis options
        model = options.get("model", settings.DEFAULT_MODEL)
        temperature = float(options.get("temperature", settings.TEMPERATURE))
        prompt = options.get("prompt", "prompts/default.txt")
        
        analysis = analyze_single_repository(
            repo_name,
            code_digest,
            prompt,
            model_name=model,
            temperature=temperature,
            output_json=True,
            metrics_data=metrics,
        )
        
        # Update progress
        task.progress = 80
        db.commit()
        
        # Step 3: Create report
        logger.info(f"Creating report for: {repo_name}")
        
        # Extract scores from analysis
        scores = extract_scores(analysis)
        
        report = Report(
            task_id=task_id,
            user_id=task.user_id,
            github_url=github_url,
            repo_name=repo_name,
            content=analysis,
            scores=scores
        )
        
        db.add(report)
        
        # Update task status
        task.status = "completed"
        task.progress = 100
        task.completed_at = datetime.utcnow()
        
        # Commit all changes
        db.commit()
        
        logger.info(f"Analysis completed for task {task_id}")
        
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
        return {}
        
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
            
    return scores