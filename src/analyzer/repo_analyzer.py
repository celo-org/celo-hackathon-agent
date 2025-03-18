"""
Repository analyzer that combines all analysis components.
"""

import os
import time
import json
from typing import Dict, Any, Optional, Callable

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.callbacks.manager import get_openai_callback
import anthropic

from src.models.config import Config
from src.models.types import RepositoryAnalysisResult
from src.analyzer.github_repo import GitHubRepository
from src.utils.logger import logger

# System prompt template for repository analysis
SYSTEM_PROMPT = """
You are an expert code reviewer and software architect specializing in blockchain applications, particularly those built on the Celo platform.

Your task is to thoroughly analyze the provided GitHub repository data and generate a comprehensive analysis report.

ABOUT CELO:
Celo is a mobile-first blockchain platform focused on making financial tools accessible to anyone with a mobile phone. Key technologies include:
- ContractKit: JavaScript library for interacting with Celo
- Celo wallet and identity protocols
- Stable tokens: cUSD, cEUR, cREAL
- Mobile-first design principles
- Social payments using phone numbers as identifiers

ANALYSIS INSTRUCTIONS:
1. Repository Type Detection:
   - Identify the type of repository (web app, mobile app, smart contract, API, library, etc.)
   - Determine the main programming languages and frameworks used

2. Code Quality Assessment:
   - Evaluate code readability, standards compliance, complexity, and testing coverage
   - Provide a score for each area (0-100) with detailed reasoning

3. Celo Integration Analysis:
   - Determine if and how the project integrates with Celo blockchain
   - Look for Celo dependencies, contract imports, and Celo-specific code
   - Identify which Celo features are being utilized

4. Architecture Evaluation:
   - Analyze the overall system architecture
   - Identify design patterns and architectural approaches
   - Evaluate code organization and module structure

5. Key Findings:
   - Highlight 3-5 important observations about the codebase
   - Note particularly good implementations or areas of concern

6. Improvement Recommendations:
   - Suggest concrete ways to improve the code or architecture
   - Prioritize recommendations by potential impact

// Code Examples section removed

8. Confidence Assessment:
   - For each section of your analysis, indicate your confidence level (High/Medium/Low)
   - Explain what factors influenced your confidence rating

OUTPUT FORMAT:
Return your analysis as a JSON object with the following structure:

{
  "repo_type": {
    "type": "string", 
    "languages": ["list", "of", "languages"],
    "frameworks": ["list", "of", "frameworks"]
  },
  "code_quality": {
    "overall_score": number,
    "readability": {"score": number, "analysis": "string"},
    "standards": {"score": number, "analysis": "string"},
    "complexity": {"score": number, "analysis": "string"},
    "testing": {"score": number, "analysis": "string"}
  },
  "celo_integration": {
    "integrated": boolean,
    "features_used": ["list", "of", "celo", "features"],
    "evidence": ["list", "of", "evidence", "found"],
    "integration_quality": {"score": number, "analysis": "string"}
  },
  "architecture": {
    "patterns": ["list", "of", "design", "patterns"],
    "structure_quality": {"score": number, "analysis": "string"},
    "modularity": {"score": number, "analysis": "string"}
  },
  "findings": {
    "strengths": ["list", "of", "strengths"],
    "concerns": ["list", "of", "concerns"],
    "overall_assessment": "string"
  },
  "recommendations": [
    {"priority": "High/Medium/Low", "description": "string", "justification": "string"},
    ...
  ],
  // Code examples section removed
  "confidence_levels": {
    "code_quality": {"level": "High/Medium/Low", "reasoning": "string"},
    "celo_integration": {"level": "High/Medium/Low", "reasoning": "string"},
    "architecture": {"level": "High/Medium/Low", "reasoning": "string"}
  }
}

IMPORTANT NOTES:
- Base your analysis ONLY on the code provided, not external assumptions
- Be specific and provide concrete examples whenever possible
- Maintain objectivity and professional tone throughout
- If you're uncertain about any aspect, indicate that clearly in your confidence assessment
- Focus on substantive issues rather than stylistic preferences
- Consider the project's apparent goals when making recommendations
"""


class RepositoryAnalyzer:
    """
    Analyzes GitHub repositories for code quality and Celo blockchain integration.

    This class combines GitHub API access, code analysis, and AI-powered evaluation
    to provide insights into repository quality and Celo integration.
    """

    def __init__(
        self,
        config_path: str = "config.json",
        model_provider: Optional[str] = None,
        verbose: bool = False,
    ):
        """
        Initialize the repository analyzer with configuration.

        Args:
            config_path: Path to the configuration file
            model_provider: Optional model provider override (anthropic, openai, google)
            verbose: Whether to enable verbose output
        """
        # Load configuration
        self.config = Config.from_file(config_path)
        self.verbose = verbose

        # Set up LLM based on provider
        self.llm = None
        self.model_provider = model_provider or self.config.default_model

        logger.debug(f"Initializing repository analyzer with model provider: {self.model_provider}")
        
        # Initialize LLM based on provider
        if self.model_provider == "anthropic":
            self._init_anthropic_model()
        elif self.model_provider == "openai":
            self._init_openai_model()
        elif self.model_provider == "google":
            self._init_google_model()
        else:
            logger.warn(f"Unknown model provider '{self.model_provider}'. Falling back to default.")
            self._init_anthropic_model()

        # Initialize GitHub repository handler
        self.github_repo = GitHubRepository(self.config)

    def _init_anthropic_model(self):
        """Initialize Anthropic Claude model."""
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
            
        logger.info(f"Using Anthropic model: {self.config.model_name}")
        self.llm = ChatAnthropic(
            model=self.config.model_name,
            temperature=self.config.temperature,
            anthropic_api_key=api_key,
        )

    def _init_openai_model(self):
        """Initialize OpenAI model."""
        logger.info("Using OpenAI model: gpt-4")
        self.llm = ChatOpenAI(
            model_name="gpt-4",
            temperature=self.config.temperature,
            openai_api_key=os.environ.get("OPENAI_API_KEY"),
        )

    def _init_google_model(self):
        """Initialize Google Gemini model."""
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")
            
        logger.info("Using Google Gemini model: gemini-2.0-flash")
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=self.config.temperature,
            google_api_key=api_key,
        )

    def analyze_repository(
        self, repo_url: str, callback: Optional[Callable] = None
    ) -> RepositoryAnalysisResult:
        """
        Analyze a GitHub repository.

        Args:
            repo_url: URL of the GitHub repository
            callback: Optional callback for progress updates

        Returns:
            Analysis results
        """
        # Initialize analysis result
        analysis_result = {}

        try:
            # Set up repository and get repository details
            repo_details = self._get_repository_details_safely(repo_url, callback)
            analysis_result["repo_details"] = repo_details

            # Collect code samples with progress updates
            if callback:
                callback("Collecting code samples")
                
            start_time = time.time()
            file_metrics, code_samples = self.github_repo.collect_code_samples(
                progress_callback=callback
            )
            elapsed = time.time() - start_time
            
            if callback:
                callback(f"Collected code samples in {elapsed:.2f}s")
            
            logger.debug(f"Code samples collected in {elapsed:.2f}s")

            # Process collected data to find Celo integration evidence
            celo_evidence = []
            if callback:
                callback("Searching for blockchain integration evidence")
                
            start_time = time.time()
            for keyword in self.config.celo_keywords:
                keyword_found = self.github_repo.search_files_for_keywords(
                    self.github_repo.code_sample_files, [keyword]
                )
                celo_evidence.extend(keyword_found)
                
            elapsed = time.time() - start_time
            logger.debug(f"Found {len(celo_evidence)} blockchain integration evidence points in {elapsed:.2f}s")

            # Generate digest for LLM analysis
            if callback:
                callback("Generating repository digest for AI analysis")

            start_time = time.time()
            repo_digest = self._generate_repo_digest(
                repo_details, file_metrics, code_samples, celo_evidence
            )
            elapsed = time.time() - start_time
            
            # Log digest size
            logger.debug(f"Repository digest generated in {elapsed:.2f}s - Size: {len(repo_digest)} characters")
            
            if len(repo_digest) < 500:
                logger.warn("Repository digest is suspiciously small!")
                logger.debug(f"Full digest: {repo_digest}")

            # Analyze digest with LLM
            if callback:
                callback("Analyzing repository with AI model")
            
            repo_analysis = self._analyze_with_llm(repo_digest, callback)

            # Combine all analysis components into final result
            for key, value in repo_analysis.items():
                analysis_result[key] = value

            # Add celo evidence to results if not already included
            if "celo_integration" in analysis_result and isinstance(
                analysis_result["celo_integration"], dict
            ):
                if (
                    not analysis_result["celo_integration"].get("evidence")
                    and celo_evidence
                ):
                    analysis_result["celo_integration"]["evidence"] = celo_evidence

            return analysis_result

        except Exception as e:
            error_msg = f"Error analyzing repository: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}

    def _get_repository_details_safely(
        self, repo_url: str, callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Get repository details safely with progress updates.

        Args:
            repo_url: URL of the GitHub repository
            callback: Optional callback for progress updates

        Returns:
            Repository details
        """
        # Use callback to report progress if provided
        if callback:
            callback(f"Fetching repository data for {repo_url}")
            
        start_time = time.time()
        
        # Setup the repository
        self.github_repo.setup_repository(repo_url)

        # Get repository details
        repo_details = self.github_repo.get_repository_details()
        
        elapsed = time.time() - start_time
        if callback:
            callback(f"Fetched repository data in {elapsed:.2f}s")
            
        logger.debug(f"Repository data fetched in {elapsed:.2f}s")
        
        return repo_details

    def _generate_repo_digest(
        self,
        repo_details: Dict[str, Any],
        file_metrics: Dict[str, int],
        code_samples: list,
        celo_evidence: list,
    ) -> str:
        """
        Generate a comprehensive digest of the repository for LLM analysis.

        Args:
            repo_details: Repository details
            file_metrics: File metrics
            code_samples: Code samples
            celo_evidence: Celo integration evidence

        Returns:
            Repository digest string
        """
        # Start with repository information
        digest = f"# Repository Information\n"
        digest += f"Name: {repo_details['name']}\n"
        digest += f"Description: {repo_details['description']}\n"
        digest += f"URL: {repo_details['url']}\n"
        digest += f"Stars: {repo_details['stars']}\n"
        digest += f"Forks: {repo_details['forks']}\n"
        digest += f"Main Language: {repo_details['language']}\n\n"

        # Add language breakdown if available
        if repo_details.get("main_languages"):
            digest += "## Language Breakdown\n"
            for lang, percentage in repo_details["main_languages"].items():
                digest += f"- {lang}: {percentage}%\n"
            digest += "\n"

        # Add file metrics
        digest += "## File Metrics\n"
        digest += f"Total Files: {file_metrics['file_count']}\n"
        digest += f"Test Files: {file_metrics['test_file_count']}\n"
        digest += f"Documentation Files: {file_metrics['doc_file_count']}\n"
        digest += f"Code Files Analyzed: {file_metrics['code_files_analyzed']}\n\n"

        # Add Celo integration evidence if found
        if celo_evidence:
            digest += "## Blockchain Integration Evidence\n"
            for evidence in celo_evidence:
                digest += f"- Found keyword '{evidence['keyword']}' in file '{evidence['file']}'\n"
            digest += "\n"

        # Add code samples
        digest += "## Code Samples\n"
        logger.debug(f"Adding {len(code_samples)} code samples to digest")
        for i, sample in enumerate(code_samples):
            if self.verbose:
                logger.debug(f"Adding sample {i+1}, length: {len(sample)}")
            digest += f"{sample}\n"
            
        # Log digest length for debugging
        logger.debug(f"Total digest length: {len(digest)} characters")
        if self.verbose:
            logger.debug(f"Digest first 200 chars: {digest[:200]}")
            logger.debug(f"Digest last 200 chars: {digest[-200:]}")

        return digest

    def _analyze_with_llm(
        self, repo_digest: str, callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Analyze repository digest with LLM.

        Args:
            repo_digest: Repository digest to analyze
            callback: Optional callback for progress updates

        Returns:
            Analysis results
        """
        try:
            # Count input tokens - just estimate for non-Anthropic
            start_time = time.time()
            
            if self.verbose:
                input_tokens = 0
                if self.model_provider == "anthropic":
                    input_tokens = anthropic.count_tokens(SYSTEM_PROMPT + repo_digest)
                else:
                    # Rough estimate: 4 chars per token
                    input_tokens = (len(SYSTEM_PROMPT) + len(repo_digest)) // 4
                
                logger.debug(f"Input tokens (estimated): {input_tokens}")
                
                if callback:
                    callback(f"Sending approximately {input_tokens} tokens to LLM for analysis")

            # Track token usage with OpenAI callback (works for multiple providers)
            with get_openai_callback() as cb:
                try:
                    # No need to truncate for Gemini with 900k token limit
                    logger.debug(f"Repository digest length: {len(repo_digest)} characters")
                    
                    # We estimate about 4 characters per token, so max 3.6M characters
                    if len(repo_digest) > 3600000:  # Only warn at extreme sizes
                        logger.warn(f"Repository digest is extremely large ({len(repo_digest)} chars). May approach model limits.")
                    
                    # Get LLM response
                    logger.debug(f"Sending prompt to LLM: system={len(SYSTEM_PROMPT)} chars, user={len(repo_digest)} chars")
                    
                    if callback:
                        callback("Waiting for AI model response...")
                        
                    response = self.llm.invoke(
                        [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": repo_digest},
                        ]
                    )
                    content = response.content
                    
                    # Debug output
                    if self.verbose:
                        logger.debug(f"LLM response received. Length: {len(content)}")
                        logger.debug(f"Response starts with: {content[:100]}...")

                    # Log token usage
                    if self.verbose:
                        if callback:
                            callback(
                                f"Analysis completed. Input tokens: {cb.prompt_tokens}, Output tokens: {cb.completion_tokens}"
                            )
                        logger.debug(
                            f"Token usage - Input: {cb.prompt_tokens}, Output: {cb.completion_tokens}, Total: {cb.total_tokens}"
                        )
                except Exception as api_error:
                    logger.error(f"API call error: {str(api_error)}")
                    if callback:
                        callback(f"Error calling AI model: {str(api_error)}")
                    return {"error": f"API call failed: {str(api_error)}"}

            # Parse JSON from response
            try:
                if callback:
                    callback("Extracting analysis from AI response")
                    
                # Extract JSON from response (may be wrapped in markdown code blocks)
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    json_str = content.split("```")[1].split("```")[0].strip()
                else:
                    json_str = content
                
                # Debug JSON extraction
                if self.verbose:
                    logger.debug(f"Extracted JSON string (first 100 chars): {json_str[:100]}...")

                analysis_result = json.loads(json_str)

                # Add token metrics if verbose mode is enabled
                if self.verbose:
                    analysis_result["token_metrics"] = {
                        "input_tokens": cb.prompt_tokens,
                        "output_tokens": cb.completion_tokens,
                        "total_tokens": cb.total_tokens,
                    }
                
                elapsed = time.time() - start_time
                logger.debug(f"LLM analysis completed in {elapsed:.2f}s")
                
                if callback:
                    callback(f"AI analysis completed in {elapsed:.2f}s")

                return analysis_result

            except json.JSONDecodeError as json_err:
                logger.error(f"Failed to parse JSON from LLM response: {str(json_err)}")
                if callback:
                    callback("Error parsing AI analysis result")
                return {
                    "error": f"Failed to parse analysis result: {str(json_err)}",
                    "raw_response": content[:500] + "...(truncated)" if len(content) > 500 else content,
                }

        except Exception as e:
            error_msg = f"Error in LLM analysis: {str(e)}"
            logger.error(error_msg)
            if callback:
                callback(f"Error in AI analysis: {str(e)}")
            return {"error": error_msg}
