"""
Orchestration system for managing the analysis workflow with parallel execution.
"""

import os
import pandas as pd
import time
import logging
import concurrent.futures
from typing import Dict, List, Any, Optional, Tuple
from threading import Lock

from src.agents.repo_agent import analyze_repository
from src.agents.code_quality_agent import analyze_code_quality
from src.agents.celo_agent import analyze_celo_integration
from src.agents.reporting_agent import generate_reports
from src.models.config import Config
from src.utils.spinner import Spinner

# Configure logger
logger = logging.getLogger(__name__)

class AnalysisOrchestrator:
    """Orchestrates the analysis process with parallel execution when possible."""
    
    def __init__(self, config_path: str = "config.json", output_dir: str = "reports", 
                 max_workers: int = 2, verbose: bool = False):
        """
        Initialize the orchestrator.
        
        Args:
            config_path: Path to configuration file
            output_dir: Directory to save reports
            max_workers: Maximum number of parallel workers
            verbose: Whether to show verbose output
        """
        self.config_path = config_path
        self.output_dir = output_dir
        self.max_workers = max_workers
        self.verbose = verbose
        self.config = Config.from_file(config_path)
        self.progress_lock = Lock()  # For thread-safe progress updates
        
        # Check for API key
        self.anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not self.anthropic_api_key:
            raise ValueError("No Anthropic API key found. Please set ANTHROPIC_API_KEY environment variable.")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    def _analyze_repo_process(self, repo_url: str, spinner: Optional[Spinner] = None) -> Dict[str, Any]:
        """
        Complete analysis process for a single repository.
        
        Args:
            repo_url: URL of the GitHub repository
            spinner: Optional spinner for progress updates
            
        Returns:
            Dictionary with analysis results
        """
        try:
            # Update progress
            if spinner:
                with self.progress_lock:
                    spinner.update(f"Analyzing repository structure: {repo_url}")
            
            # Step 1: Repository analysis
            repo_start = time.time()
            repo_analysis = analyze_repository(repo_url, self.verbose)
            repo_time = time.time() - repo_start
            
            # Extract key information
            repo_owner = repo_analysis.get("repo_owner", "unknown")
            repo_name = repo_analysis.get("repo_name", "unknown")
            repo_description = repo_analysis.get("repo_description", "")
            
            # Find code samples in results
            code_samples = []
            if "agent_result" in repo_analysis:
                # Try to find code samples in the agent result
                for key, value in repo_analysis["agent_result"].items():
                    if key == "code_samples" and isinstance(value, list):
                        code_samples = value
                        break
                
                # If not found directly, check in intermediate steps
                if not code_samples and "intermediate_steps" in repo_analysis["agent_result"]:
                    for step in repo_analysis["agent_result"]["intermediate_steps"]:
                        if isinstance(step, tuple) and len(step) >= 2:
                            tool_result = step[1]
                            if isinstance(tool_result, dict) and "code_samples" in tool_result:
                                code_samples = tool_result.get("code_samples", [])
                                break
            
            # Update progress
            if spinner:
                with self.progress_lock:
                    spinner.update(f"Analyzing code quality: {repo_owner}/{repo_name}")
            
            # Step 2: Code quality analysis
            quality_start = time.time()
            quality_analysis = analyze_code_quality(
                code_samples, 
                repo_owner, 
                repo_name, 
                repo_description, 
                verbose=self.verbose
            )
            quality_time = time.time() - quality_start
            
            # Update progress
            if spinner:
                with self.progress_lock:
                    spinner.update(f"Checking Celo integration: {repo_owner}/{repo_name}")
            
            # Step 3: Celo integration analysis
            celo_start = time.time()
            celo_analysis = analyze_celo_integration(
                repo_url,
                code_samples,
                repo_owner,
                repo_name,
                repo_description,
                verbose=self.verbose
            )
            celo_time = time.time() - celo_start
            
            # Update progress
            if spinner:
                with self.progress_lock:
                    spinner.update(f"Completed analysis of {repo_owner}/{repo_name}")
            
            # Log timing information
            logger.info(f"Analysis timing for {repo_url}: "
                      f"Repo: {repo_time:.1f}s, "
                      f"Quality: {quality_time:.1f}s, "
                      f"Celo: {celo_time:.1f}s")
            
            # Return combined results
            return {
                "project_name": f"{repo_owner}/{repo_name}",
                "project_description": repo_description,
                "project_github_url": repo_url,
                "github_urls": [repo_url],
                "project_owner_github_url": [f"https://github.com/{repo_owner}"],
                "project_url": f"https://github.com/{repo_owner}/{repo_name}",
                "analysis": {
                    "repo_details": repo_analysis.get("repo_details", repo_analysis.get("analysis", "")),
                    "code_quality": quality_analysis.get("code_quality", quality_analysis.get("analysis", "")),
                    "celo_integration": celo_analysis.get("celo_integration", celo_analysis.get("analysis", ""))
                },
                "timing": {
                    "repository_analysis": repo_time,
                    "code_quality_analysis": quality_time,
                    "celo_integration_analysis": celo_time,
                    "total": repo_time + quality_time + celo_time
                }
            }
        except Exception as e:
            logger.error(f"Error analyzing {repo_url}: {str(e)}", exc_info=True)
            if spinner:
                with self.progress_lock:
                    spinner.update(f"Error analyzing {repo_url}: {str(e)}")
            
            # Return error result
            return {
                "project_name": f"Error: {repo_url}",
                "project_description": "Analysis failed",
                "project_github_url": repo_url,
                "github_urls": [repo_url],
                "project_owner_github_url": [],
                "project_url": repo_url,
                "analysis": {
                    "error": f"Analysis failed: {str(e)}",
                    "repo_details": "Not evaluated",
                    "code_quality": "Not evaluated",
                    "celo_integration": "Not evaluated"
                }
            }
    
    def analyze_single_repository(self, repo_url: str, spinner: Optional[Spinner] = None) -> Dict[str, Any]:
        """
        Analyze a single repository.
        
        Args:
            repo_url: URL of the GitHub repository
            spinner: Optional spinner for progress updates
            
        Returns:
            Dictionary containing analysis results
        """
        return self._analyze_repo_process(repo_url, spinner)
    
    def analyze_projects_from_excel(self, excel_path: str, spinner: Optional[Spinner] = None) -> List[Dict[str, Any]]:
        """
        Analyze multiple projects from an Excel file.
        
        Args:
            excel_path: Path to Excel file with project data
            spinner: Optional spinner for progress updates
            
        Returns:
            List of dictionaries with analysis results
        """
        # Load projects from Excel
        try:
            if spinner:
                spinner.update(f"Loading projects from {excel_path}")
                
            df = pd.read_excel(excel_path)
            required_columns = [
                "project_name",
                "project_description",
                "project_github_url",
                "project_owner_github_url",
                "project_url",
            ]
            
            # Check if required columns exist
            for col in required_columns:
                if col not in df.columns:
                    raise ValueError(f"Missing required column: {col}")
            
            project_results = []
            
            # Process each project
            for index, row in df.iterrows():
                project_name = row["project_name"]
                project_description = row["project_description"]
                raw_github_urls = row["project_github_url"]
                
                if spinner:
                    spinner.update(f"Processing project {index+1}/{len(df)}: {project_name}")
                
                # Process GitHub URLs
                github_urls = []
                if isinstance(raw_github_urls, str):
                    github_urls = [url.strip() for url in raw_github_urls.split(',') if url.strip()]
                elif pd.notna(raw_github_urls):
                    github_urls = [str(raw_github_urls)]
                
                # If no valid GitHub URLs, create a default result and continue
                if not github_urls:
                    if spinner:
                        spinner.update(f"No valid GitHub URLs for {project_name}")
                        
                    logger.warning(f"No valid GitHub URLs found for project {project_name}")
                    
                    # Create a default result with error
                    project_result = {
                        "project_name": project_name,
                        "project_description": project_description,
                        "project_github_url": "No valid GitHub URL provided",
                        "github_urls": [],
                        "project_owner_github_url": [],
                        "project_url": row["project_url"],
                        "analysis": {
                            "error": "No valid GitHub URL provided",
                            "repo_details": "Not evaluated",
                            "code_quality": "Not evaluated",
                            "celo_integration": "Not evaluated"
                        }
                    }
                    
                    project_results.append(project_result)
                    continue
                
                # Process owner GitHub URLs
                owner_github_urls = []
                raw_owner_urls = row["project_owner_github_url"]
                if isinstance(raw_owner_urls, str):
                    owner_github_urls = [url.strip() for url in raw_owner_urls.split(',') if url.strip()]
                elif pd.notna(raw_owner_urls):
                    owner_github_urls = [str(raw_owner_urls)]
                
                # Initialize combined analysis results
                combined_analysis = {
                    "repo_details": [],
                    "code_quality": {"overall_score": 0, "repositories_analyzed": 0},
                    "celo_integration": {"integrated": False, "evidence": [], "repositories_with_celo": 0}
                }
                
                # Analyze repositories in parallel
                repo_results = []
                
                if spinner:
                    spinner.update(f"Analyzing {len(github_urls)} repositories for {project_name}")
                
                # Use parallel execution if multiple repositories and max_workers > 1
                if len(github_urls) > 1 and self.max_workers > 1:
                    with concurrent.futures.ThreadPoolExecutor(max_workers=min(self.max_workers, len(github_urls))) as executor:
                        # Submit all repository analysis tasks
                        future_to_url = {
                            executor.submit(self._analyze_repo_process, url, spinner): url 
                            for url in github_urls if url and url.startswith('http')
                        }
                        
                        # Collect results as they complete
                        for future in concurrent.futures.as_completed(future_to_url):
                            url = future_to_url[future]
                            try:
                                result = future.result()
                                repo_results.append(result)
                            except Exception as e:
                                logger.error(f"Error analyzing {url}: {str(e)}")
                                if spinner:
                                    spinner.update(f"Error analyzing {url}: {str(e)}")
                else:
                    # Process sequentially
                    for url_index, github_url in enumerate(github_urls):
                        # Skip empty URLs
                        if not github_url or not github_url.startswith('http'):
                            continue
                            
                        if spinner:
                            spinner.update(f"Analyzing repository {url_index+1}/{len(github_urls)}: {github_url}")
                            
                        result = self._analyze_repo_process(github_url, spinner)
                        repo_results.append(result)
                
                # Combine results from all repositories
                if repo_results:
                    # Process each repository result
                    for repo_result in repo_results:
                        # Add repo details
                        if "repo_details" in repo_result["analysis"]:
                            combined_analysis["repo_details"].append(repo_result["analysis"]["repo_details"])
                        
                        # Update code quality scores
                        if "code_quality" in repo_result["analysis"]:
                            quality = repo_result["analysis"]["code_quality"]
                            if isinstance(quality, dict) and "overall_score" in quality:
                                combined_analysis["code_quality"]["repositories_analyzed"] += 1
                                combined_analysis["code_quality"]["overall_score"] += quality["overall_score"]
                                
                                # Preserve detailed metrics from the first repository with complete analysis
                                if (combined_analysis["code_quality"]["repositories_analyzed"] == 1 or 
                                    not any(key in combined_analysis["code_quality"] for key in 
                                           ["readability", "standards", "complexity", "testing", "ai_analysis", "metrics"])):
                                    for key in ["readability", "standards", "complexity", "testing", "ai_analysis", "metrics"]:
                                        if key in quality:
                                            combined_analysis["code_quality"][key] = quality[key]
                        
                        # Update Celo integration status
                        if "celo_integration" in repo_result["analysis"]:
                            celo = repo_result["analysis"]["celo_integration"]
                            if isinstance(celo, dict) and "integrated" in celo:
                                if celo["integrated"]:
                                    combined_analysis["celo_integration"]["integrated"] = True
                                    combined_analysis["celo_integration"]["repositories_with_celo"] += 1
                                    
                                    # Add evidence
                                    if "evidence" in celo and celo["evidence"]:
                                        # Mark evidence with repository URL
                                        for evidence in celo["evidence"]:
                                            if "repository" not in evidence:
                                                evidence["repository"] = repo_result["project_github_url"]
                                        combined_analysis["celo_integration"]["evidence"].extend(celo["evidence"])
                    
                    # Calculate average code quality score
                    if combined_analysis["code_quality"]["repositories_analyzed"] > 0:
                        avg_score = combined_analysis["code_quality"]["overall_score"] / combined_analysis["code_quality"]["repositories_analyzed"]
                        combined_analysis["code_quality"]["overall_score"] = avg_score
                
                # Create final project result
                project_result = {
                    "project_name": project_name,
                    "project_description": project_description,
                    "project_github_url": raw_github_urls,
                    "github_urls": github_urls,
                    "project_owner_github_url": owner_github_urls,
                    "project_url": row["project_url"],
                    "analysis": combined_analysis
                }
                
                project_results.append(project_result)
                
                if spinner:
                    spinner.update(f"Completed analysis of project: {project_name}")
            
            return project_results
            
        except Exception as e:
            logger.error(f"Error analyzing projects from Excel: {str(e)}", exc_info=True)
            raise Exception(f"Error analyzing projects from Excel: {str(e)}")
    
    def run(self, excel_path: str, spinner: Optional[Spinner] = None) -> Dict[str, Any]:
        """
        Run the complete analysis pipeline.
        
        Args:
            excel_path: Path to Excel file with project data
            spinner: Optional spinner for progress updates
            
        Returns:
            Dictionary with overall analysis results
        """
        start_time = time.time()
        
        try:
            # Step 1: Analyze projects
            if spinner:
                spinner.update(f"Starting analysis of projects from {excel_path}")
                
            project_results = self.analyze_projects_from_excel(excel_path, spinner)
            
            # Step 2: Generate reports
            if spinner:
                spinner.update(f"Generating reports for {len(project_results)} projects")
                
            report_result = generate_reports(project_results, self.output_dir, self.verbose)
            
            # Calculate elapsed time
            elapsed_time = time.time() - start_time
            
            if spinner:
                spinner.update(f"Analysis completed in {elapsed_time:.1f} seconds")
            
            # Return results
            return {
                "status": "success",
                "projects_analyzed": len(project_results),
                "output_directory": self.output_dir,
                "elapsed_time": elapsed_time,
                "report_summary": report_result.get("summary", "")
            }
        except Exception as e:
            logger.error(f"Error in analysis pipeline: {str(e)}", exc_info=True)
            if spinner:
                spinner.update(f"Error in analysis pipeline: {str(e)}")
            
            return {
                "status": "error",
                "error": str(e),
                "output_directory": self.output_dir,
                "elapsed_time": time.time() - start_time
            }