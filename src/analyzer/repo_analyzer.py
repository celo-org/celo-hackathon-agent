"""
Repository analyzer that combines all analysis components.
"""

import os
from typing import Dict, Any, Optional, Callable

from langchain_anthropic import ChatAnthropic

from src.models.config import Config
from src.models.types import RepositoryAnalysisResult
from src.analyzer.github_repo import GitHubRepository
from src.analyzer.code_quality import CodeQualityAnalyzer
from src.analyzer.celo_detector import CeloIntegrationDetector
from src.analyzer.deep_code_analyzer import DeepCodeAnalyzer
from src.utils.spinner import run_with_active_spinner


class RepositoryAnalyzer:
    """
    Analyzes GitHub repositories for code quality and Celo blockchain integration.
    
    This class combines GitHub API access, code analysis, and AI-powered evaluation
    to provide insights into repository quality and Celo integration.
    """
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the repository analyzer with configuration.
        
        Args:
            config_path: Path to the configuration file
        """
        # Load configuration
        self.config = Config.from_file(config_path)
        
        # Set up Anthropic model if API key is available
        self.llm = None
        self.anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
        if self.anthropic_api_key:
            try:
                self.llm = ChatAnthropic(
                    model=self.config.model_name,
                    temperature=self.config.temperature,
                    anthropic_api_key=self.anthropic_api_key
                )
            except Exception as e:
                print(f"Error initializing Claude model: {str(e)}")
                print("Using fallback analysis methods only.")
        else:
            print("Warning: No Anthropic API key found. Using fallback analysis methods only.")
        
        # Initialize components
        self.github_repo = GitHubRepository(self.config)
        self.code_analyzer = CodeQualityAnalyzer(self.config, self.llm)
        self.celo_detector = CeloIntegrationDetector(self.config, self.llm)
        self.deep_code_analyzer = DeepCodeAnalyzer(self.config, self.llm)
        
    def analyze_repository(self, repo_url: str, callback: Optional[Callable] = None) -> RepositoryAnalysisResult:
        """
        Analyze a GitHub repository for code quality and Celo integration.
        
        Args:
            repo_url: URL of the GitHub repository
            callback: Optional callback function to report progress
            
        Returns:
            RepositoryAnalysisResult containing analysis results
        """
        try:
            # Setup GitHub connection
            if callback:
                callback(f"Setting up GitHub tools for {repo_url}")
            
            repo_owner, repo_name = self.github_repo.setup_repository(repo_url)
            
            # Step 1: Get repository details
            repo_details = self._get_repository_details_safely(repo_owner, repo_name, repo_url, callback)
            
            # Step 2: Analyze code quality
            code_quality = self._analyze_code_quality_safely(repo_owner, repo_name, repo_details.get("description", ""), callback)
            
            # Step 3: Check for Celo integration
            celo_integration = self._check_celo_integration_safely(repo_owner, repo_name, repo_details.get("description", ""), callback)
            
            # Step 4: Perform deep code analysis if LLM is available
            deep_code_analysis = self._perform_deep_code_analysis_safely(repo_owner, repo_name, callback)
            
            # Compile results
            if callback:
                callback(f"Compiling analysis results for {repo_owner}/{repo_name}")
                
            results = {
                "repo_details": repo_details,
                "code_quality": code_quality,
                "celo_integration": celo_integration,
                "deep_code_analysis": deep_code_analysis
            }
            
            return results
            
        except Exception as e:
            error_message = f"Error analyzing repository: {str(e)}"
            
            if callback:
                # Show error in spinner
                callback(f"Error analyzing {repo_url}: {str(e)}")
                
            # Create a result with error information
            return {
                "error": error_message,
                "repo_details": self.github_repo.create_fallback_repo_details(
                    repo_owner=repo_url.split('/')[-2] if 'github.com' in repo_url else "unknown",
                    repo_name=repo_url.split('/')[-1] if 'github.com' in repo_url else "unknown",
                    repo_url=repo_url
                ),
                "code_quality": self.code_analyzer._create_fallback_code_quality(error_message) if hasattr(self.code_analyzer, '_create_fallback_code_quality') else {"error": error_message},
                "celo_integration": {"integrated": False, "evidence": []},
                "deep_code_analysis": self.deep_code_analyzer._create_fallback_analysis(error_message) if hasattr(self.deep_code_analyzer, '_create_fallback_analysis') else {"error": error_message}
            }
    
    def _get_repository_details_safely(self, repo_owner: str, repo_name: str, repo_url: str, callback=None) -> Dict[str, Any]:
        """
        Safely get repository details with error handling and fallback.
        
        Args:
            repo_owner: Owner of the repository
            repo_name: Name of the repository
            repo_url: URL of the repository
            callback: Optional callback function for progress updates
            
        Returns:
            Repository details dictionary
        """
        if callback:
            callback(f"Fetching repository details for {repo_owner}/{repo_name}")
            
            try:
                return run_with_active_spinner(
                    func=self.github_repo.get_repository_details,
                    message=f"Fetching repository details for {repo_owner}/{repo_name}",
                    callback=callback
                )
            except Exception as e:
                # Handle API or connection errors
                error_message = str(e)
                callback(f"Error fetching repository details: {error_message}")
                return self.github_repo.create_fallback_repo_details(repo_owner, repo_name, repo_url)
        else:
            try:
                return self.github_repo.get_repository_details()
            except Exception:
                return self.github_repo.create_fallback_repo_details(repo_owner, repo_name, repo_url)
    
    def _analyze_code_quality_safely(self, repo_owner: str, repo_name: str, repo_description: str, callback=None) -> Dict[str, Any]:
        """
        Safely analyze code quality with error handling and fallback.
        
        Args:
            repo_owner: Owner of the repository
            repo_name: Name of the repository
            repo_description: Repository description
            callback: Optional callback function for progress updates
            
        Returns:
            Code quality analysis dictionary
        """
        if callback:
            callback(f"Analyzing code quality for {repo_owner}/{repo_name}")
        
        # Choose analysis method based on repository access
        if self.github_repo.repo is None:
            # No repository access, use estimation
            if callback:
                try:
                    return run_with_active_spinner(
                        func=self.code_analyzer.analyze_without_access,
                        args=(repo_owner, repo_name, repo_description),
                        message=f"Estimating code quality for {repo_owner}/{repo_name}",
                        callback=callback
                    )
                except Exception as e:
                    error_message = str(e)
                    callback(f"Error estimating code quality: {error_message}")
                    return self.code_analyzer.estimate_quality_with_heuristics(repo_owner, repo_name)
            else:
                return self.code_analyzer.analyze_without_access(repo_owner, repo_name, repo_description)
        else:
            # Have repository access, analyze code samples
            if callback:
                try:
                    # First collect code samples
                    file_metrics, code_samples = run_with_active_spinner(
                        func=self.github_repo.collect_code_samples,
                        args=(callback,),  # Pass the callback to the function
                        message=f"Collecting code samples from {repo_owner}/{repo_name}",
                        callback=callback
                    )
                    
                    # Then analyze them
                    return run_with_active_spinner(
                        func=self.code_analyzer.analyze_code_samples,
                        args=(code_samples, file_metrics),
                        message=f"Analyzing code samples from {repo_owner}/{repo_name}",
                        callback=callback
                    )
                except Exception as e:
                    error_message = str(e)
                    callback(f"Error analyzing code quality: {error_message}")
                    return self.code_analyzer.estimate_quality_with_heuristics(repo_owner, repo_name)
            else:
                try:
                    file_metrics, code_samples = self.github_repo.collect_code_samples()
                    return self.code_analyzer.analyze_code_samples(code_samples, file_metrics)
                except Exception:
                    return self.code_analyzer.estimate_quality_with_heuristics(repo_owner, repo_name)
    
    def _check_celo_integration_safely(self, repo_owner: str, repo_name: str, repo_description: str, callback=None) -> Dict[str, Any]:
        """
        Safely check Celo integration with error handling and fallback.
        
        Args:
            repo_owner: Owner of the repository
            repo_name: Name of the repository
            repo_description: Repository description
            callback: Optional callback function for progress updates
            
        Returns:
            Celo integration analysis dictionary
        """
        if callback:
            callback(f"Checking Celo integration for {repo_owner}/{repo_name}")
        
        # Choose analysis method based on repository access
        if self.github_repo.repo is None:
            # No repository access, use estimation
            if callback:
                try:
                    return run_with_active_spinner(
                        func=self.celo_detector.check_without_access,
                        args=(repo_owner, repo_name, repo_description),
                        message=f"Estimating Celo integration for {repo_owner}/{repo_name}",
                        callback=callback
                    )
                except Exception as e:
                    error_message = str(e)
                    callback(f"Error estimating Celo integration: {error_message}")
                    has_celo_in_name = "celo" in repo_name.lower()
                    return {
                        "integrated": has_celo_in_name,
                        "evidence": [{"file": "Repository name", "keyword": "celo"}] if has_celo_in_name else [],
                        "repositories_with_celo": 1 if has_celo_in_name else 0
                    }
            else:
                return self.celo_detector.check_without_access(repo_owner, repo_name, repo_description)
        else:
            # Have repository access, check directly
            if callback:
                try:
                    return run_with_active_spinner(
                        func=self.celo_detector.check_integration,
                        args=(self.github_repo.repo, repo_owner, repo_name),
                        message=f"Checking Celo integration in {repo_owner}/{repo_name}",
                        callback=callback
                    )
                except Exception as e:
                    error_message = str(e)
                    callback(f"Error checking Celo integration: {error_message}")
                    has_celo_in_name = "celo" in repo_name.lower()
                    return {
                        "integrated": has_celo_in_name,
                        "evidence": [{"file": "Repository name", "keyword": "celo"}] if has_celo_in_name else [],
                        "repositories_with_celo": 1 if has_celo_in_name else 0
                    }
            else:
                try:
                    return self.celo_detector.check_integration(self.github_repo.repo, repo_owner, repo_name)
                except Exception:
                    has_celo_in_name = "celo" in repo_name.lower()
                    return {
                        "integrated": has_celo_in_name,
                        "evidence": [{"file": "Repository name", "keyword": "celo"}] if has_celo_in_name else [],
                        "repositories_with_celo": 1 if has_celo_in_name else 0
                    }
                    
    def _perform_deep_code_analysis_safely(self, repo_owner: str, repo_name: str, callback=None) -> Dict[str, Any]:
        """
        Safely perform deep code analysis with error handling and fallback.
        
        Args:
            repo_owner: Owner of the repository
            repo_name: Name of the repository
            callback: Optional callback function for progress updates
            
        Returns:
            Deep code analysis dictionary
        """
        # Only proceed if LLM is available
        if self.llm is None:
            if callback:
                callback(f"Skipping deep code analysis for {repo_owner}/{repo_name} - LLM not available")
            return self.deep_code_analyzer._create_fallback_analysis("LLM not available for deep analysis")
        
        # Only proceed if we have repository access
        if self.github_repo.repo is None:
            if callback:
                callback(f"Skipping deep code analysis for {repo_owner}/{repo_name} - repository access not available")
            return self.deep_code_analyzer._create_fallback_analysis("Repository access not available for deep analysis")
        
        if callback:
            callback(f"Performing deep code analysis for {repo_owner}/{repo_name}")
        
        try:
            # First collect detailed code samples with filenames
            file_samples = []
            
            if callback:
                try:
                    # Get code samples with filenames
                    _, code_samples = run_with_active_spinner(
                        func=self.github_repo.collect_code_samples,
                        args=(callback,),
                        message=f"Collecting code samples from {repo_owner}/{repo_name} for deep analysis",
                        callback=callback
                    )
                    
                    # Convert to format expected by deep code analyzer
                    for i, sample in enumerate(code_samples):
                        if hasattr(self.github_repo, 'code_sample_files') and i < len(self.github_repo.code_sample_files):
                            filename = self.github_repo.code_sample_files[i]
                        else:
                            filename = f"sample_{i}.txt"
                            
                        file_samples.append({
                            "filename": filename,
                            "content": sample
                        })
                    
                    # Then perform deep analysis
                    return run_with_active_spinner(
                        func=self.deep_code_analyzer.analyze_codebase,
                        args=(file_samples,),
                        message=f"Performing deep code analysis for {repo_owner}/{repo_name}",
                        callback=callback
                    )
                except Exception as e:
                    error_message = str(e)
                    callback(f"Error performing deep code analysis: {error_message}")
                    return self.deep_code_analyzer._create_fallback_analysis(error_message)
            else:
                try:
                    # Non-interactive mode
                    _, code_samples = self.github_repo.collect_code_samples()
                    
                    # Convert to format expected by deep code analyzer
                    for i, sample in enumerate(code_samples):
                        if hasattr(self.github_repo, 'code_sample_files') and i < len(self.github_repo.code_sample_files):
                            filename = self.github_repo.code_sample_files[i]
                        else:
                            filename = f"sample_{i}.txt"
                            
                        file_samples.append({
                            "filename": filename,
                            "content": sample
                        })
                    
                    return self.deep_code_analyzer.analyze_codebase(file_samples)
                except Exception as e:
                    return self.deep_code_analyzer._create_fallback_analysis(str(e))
        except Exception as e:
            if callback:
                callback(f"Error in deep code analysis: {str(e)}")
            return self.deep_code_analyzer._create_fallback_analysis(str(e))