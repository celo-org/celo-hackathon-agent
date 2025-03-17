"""
Code quality analysis functionality using a question-based approach.
"""

import re
from typing import Dict, List, Any, Optional

from src.models.types import CodeQualityResult, CodeQualityMetrics
from src.models.config import Config
from src.utils.timeout import AIAnalysisError, with_timeout, TimeoutError


class CodeQualityAnalyzer:
    """Analyzes code quality using AI and heuristics with direct questions."""

    def __init__(self, config: Config, llm=None):
        """
        Initialize with configuration and optional LLM.

        Args:
            config: Configuration object
            llm: Optional LangChain LLM instance
        """
        self.config = config
        self.llm = llm

    def analyze_without_access(
        self, repo_owner: str, repo_name: str, repo_description: str
    ) -> CodeQualityResult:
        """
        Analyze code quality without direct repository access.

        Args:
            repo_owner: Owner of the repository
            repo_name: Name of the repository
            repo_description: Repository description

        Returns:
            CodeQualityResult with estimated quality
        """
        # Try AI-based estimation if available
        if self.llm is not None:
            try:
                return self.estimate_quality_with_ai(
                    repo_owner, repo_name, repo_description
                )
            except Exception as e:
                print(f"Error in AI estimation of code quality: {str(e)}")
                # Fall through to heuristic analysis on failure

        # Use heuristic analysis as fallback
        return self.estimate_quality_with_heuristics(repo_owner, repo_name)

    def estimate_quality_with_ai(
        self, repo_owner: str, repo_name: str, repo_description: str
    ) -> CodeQualityResult:
        """
        Estimate code quality using AI based on repository metadata.

        Args:
            repo_owner: Owner of the repository
            repo_name: Name of the repository
            repo_description: Repository description

        Returns:
            CodeQualityResult with AI-based quality estimation
        """
        try:
            # Use direct LLM invocation with lower temperature
            modified_llm = self.llm
            if hasattr(self.llm, 'temperature'):
                modified_llm = self.llm.with_config(temperature=0.1)
            
            # Create a dictionary to store our analysis results
            analysis_results = {}
            
            # List of aspects to analyze
            analysis_aspects = [
                {
                    "aspect": "readability",
                    "question": f"Rate the likely code readability and documentation quality of the GitHub repository {repo_owner}/{repo_name} with description '{repo_description}' on a scale of 0-100. Explain your reasoning."
                },
                {
                    "aspect": "standards",
                    "question": f"Rate the likely adherence to coding standards and best practices of the GitHub repository {repo_owner}/{repo_name} with description '{repo_description}' on a scale of 0-100. Explain your reasoning."
                },
                {
                    "aspect": "complexity",
                    "question": f"Rate the likely algorithmic complexity and efficiency of the GitHub repository {repo_owner}/{repo_name} with description '{repo_description}' on a scale of 0-100. Explain your reasoning."
                },
                {
                    "aspect": "testing",
                    "question": f"Rate the likely testing approach and test coverage of the GitHub repository {repo_owner}/{repo_name} with description '{repo_description}' on a scale of 0-100. Explain your reasoning."
                },
                {
                    "aspect": "overall_analysis",
                    "question": f"Provide a brief overall analysis of the likely code quality of the GitHub repository {repo_owner}/{repo_name} with description '{repo_description}'."
                },
                {
                    "aspect": "suggestions",
                    "question": f"Suggest improvements that might benefit the GitHub repository {repo_owner}/{repo_name} with description '{repo_description}'."
                }
            ]
            
            # Ask questions for each aspect
            for aspect_info in analysis_aspects:
                aspect = aspect_info["aspect"]
                question = aspect_info["question"]
                
                # Get response from LLM
                response = modified_llm.invoke(question).content
                
                # Parse the response
                if aspect in ["readability", "standards", "complexity", "testing"]:
                    score, reasoning = self._extract_score_and_reasoning(response)
                    analysis_results[aspect] = {"score": score, "reasoning": reasoning}
                elif aspect == "overall_analysis":
                    analysis_results[aspect] = response.strip()
                elif aspect == "suggestions":
                    analysis_results[aspect] = self._extract_suggestions(response)
            
            # Calculate weighted score
            readability_score = analysis_results.get("readability", {}).get("score", 0)
            standards_score = analysis_results.get("standards", {}).get("score", 0)
            complexity_score = analysis_results.get("complexity", {}).get("score", 0) 
            testing_score = analysis_results.get("testing", {}).get("score", 0)
            
            # Calculate weighted score based on weights in config
            overall_score = self.calculate_weighted_score(
                readability_score, standards_score, complexity_score, testing_score
            )

            # Return formatted result
            return {
                "overall_score": round(overall_score, 2),
                "readability": readability_score,
                "standards": standards_score,
                "complexity": complexity_score,
                "testing": testing_score,
                "ai_analysis": {
                    "overall_analysis": analysis_results.get("overall_analysis", "")
                    + " (Note: This is an estimate based on limited information)",
                    "suggestions": analysis_results.get("suggestions", []),
                    "readability_reasoning": analysis_results.get("readability", {}).get("reasoning", ""),
                    "standards_reasoning": analysis_results.get("standards", {}).get("reasoning", ""),
                    "complexity_reasoning": analysis_results.get("complexity", {}).get("reasoning", ""),
                    "testing_reasoning": analysis_results.get("testing", {}).get("reasoning", ""),
                },
                "metrics": {
                    "file_count": 0,
                    "test_file_count": 0,
                    "doc_file_count": 0,
                    "code_files_analyzed": 0,
                },
                "repositories_analyzed": 1,
                "note": "This analysis is based on AI estimation as direct repository access was not available.",
            }
        except Exception as e:
            raise AIAnalysisError(f"Error in AI estimation of code quality: {str(e)}")

    def estimate_quality_with_heuristics(
        self, repo_owner: str, repo_name: str
    ) -> CodeQualityResult:
        """
        Estimate code quality using heuristics based on repository name and owner.

        Args:
            repo_owner: Owner of the repository
            repo_name: Name of the repository

        Returns:
            CodeQualityResult with heuristic-based quality estimation
        """
        repo_name_lower = repo_name.lower()
        repo_owner_lower = repo_owner.lower()

        # Simple heuristic based on repository name and owner
        quality_indicators = [
            "awesome",
            "framework",
            "official",
            "production",
            "stable",
        ]
        quality_score = 0

        # Check for quality indicators in name and owner
        for indicator in quality_indicators:
            if indicator in repo_name_lower or indicator in repo_owner_lower:
                quality_score += 15

        # Apply premium for well-known organizations
        premium_orgs = [
            "microsoft",
            "google",
            "facebook",
            "apple",
            "amazon",
            "celo-org",
        ]
        if repo_owner_lower in premium_orgs:
            quality_score += 30

        # Cap at 85 - we can't give a perfect score without seeing the code
        quality_score = min(85, quality_score)

        # If we found no indicators, give a baseline score
        if quality_score == 0:
            quality_score = 50

        # Return consistent result structure
        return {
            "overall_score": quality_score,
            "readability": quality_score,
            "standards": quality_score,
            "complexity": quality_score,
            "testing": quality_score,
            "metrics": {
                "file_count": 0,
                "test_file_count": 0,
                "doc_file_count": 0,
                "code_files_analyzed": 0,
            },
            "repositories_analyzed": 1,
            "note": "This is a basic estimate based on repository metadata, as direct repository access was not available.",
        }

    @with_timeout(90)  # Increased timeout for more thorough analysis
    def analyze_code_samples(
        self, code_samples: List[str], file_metrics: CodeQualityMetrics
    ) -> CodeQualityResult:
        """
        Analyze code quality using AI based on code samples.

        Args:
            code_samples: List of code samples
            file_metrics: Repository file metrics

        Returns:
            CodeQualityResult with AI-based analysis
        """
        # If we have code samples and a working LLM, use AI analysis
        if code_samples and self.llm is not None:
            try:
                return self.analyze_with_ai(code_samples, file_metrics)
            except Exception as e:
                print(f"Error in AI analysis of code: {str(e)}")

        # Fallback to heuristic-based analysis
        return self.analyze_with_heuristics(file_metrics)

    def analyze_with_ai(
        self, code_samples: List[str], file_metrics: CodeQualityMetrics
    ) -> CodeQualityResult:
        """
        Analyze code quality using AI with direct questions.

        Args:
            code_samples: List of code samples
            file_metrics: Repository file metrics

        Returns:
            CodeQualityResult with AI-based analysis
        """
        # Combine code samples for analysis
        code_sample_text = "\n".join(code_samples)
        code_intro = f"Analyze the following code samples from a repository:\n\n{code_sample_text[:1000]}...\n(truncated for brevity)"
            
        try:
            # Use direct LLM invocation with lower temperature
            modified_llm = self.llm
            if hasattr(self.llm, 'temperature'):
                modified_llm = self.llm.with_config(temperature=0.1)
                
            # Dictionary to store analysis results
            analysis_results = {}
            
            # Define the analysis questions for each aspect
            analysis_aspects = [
                {
                    "aspect": "readability",
                    "question": f"{code_intro}\n\nRate the code readability and documentation quality on a scale of 0-100. Explain your reasoning in detail."
                },
                {
                    "aspect": "standards",
                    "question": f"{code_intro}\n\nRate the adherence to coding standards and best practices on a scale of 0-100. Explain your reasoning in detail."
                },
                {
                    "aspect": "complexity",
                    "question": f"{code_intro}\n\nRate the algorithmic complexity and efficiency on a scale of 0-100. Explain your reasoning in detail."
                },
                {
                    "aspect": "testing",
                    "question": f"{code_intro}\n\nRate the testing approach and test coverage on a scale of 0-100. Explain your reasoning in detail."
                },
                {
                    "aspect": "overall_analysis",
                    "question": f"{code_intro}\n\nProvide a brief overall analysis of the code quality."
                },
                {
                    "aspect": "suggestions",
                    "question": f"{code_intro}\n\nList specific suggestions for improving the code quality, one suggestion per line starting with a dash (-)."
                }
            ]
            
            # Ask questions for each aspect
            for aspect_info in analysis_aspects:
                aspect = aspect_info["aspect"]
                question = aspect_info["question"]
                
                print(f"Analyzing code quality: {aspect}...")
                
                # Get response from LLM
                response = modified_llm.invoke(question).content
                
                # Parse the response
                if aspect in ["readability", "standards", "complexity", "testing"]:
                    score, reasoning = self._extract_score_and_reasoning(response)
                    analysis_results[aspect] = {"score": score, "reasoning": reasoning}
                elif aspect == "overall_analysis":
                    analysis_results[aspect] = response.strip()
                elif aspect == "suggestions":
                    analysis_results[aspect] = self._extract_suggestions(response)
            
            # Extract scores
            readability_score = analysis_results.get("readability", {}).get("score", 0)
            standards_score = analysis_results.get("standards", {}).get("score", 0)
            complexity_score = analysis_results.get("complexity", {}).get("score", 0) 
            testing_score = analysis_results.get("testing", {}).get("score", 0)
            
            # Calculate weighted score
            overall_score = self.calculate_weighted_score(
                readability_score, standards_score, complexity_score, testing_score
            )
                
            # Return complete result
            return {
                "overall_score": round(overall_score, 2),
                "readability": readability_score,
                "standards": standards_score,
                "complexity": complexity_score,
                "testing": testing_score,
                "ai_analysis": {
                    "overall_analysis": analysis_results.get("overall_analysis", ""),
                    "suggestions": analysis_results.get("suggestions", []),
                    "readability_reasoning": analysis_results.get("readability", {}).get("reasoning", ""),
                    "standards_reasoning": analysis_results.get("standards", {}).get("reasoning", ""),
                    "complexity_reasoning": analysis_results.get("complexity", {}).get("reasoning", ""),
                    "testing_reasoning": analysis_results.get("testing", {}).get("reasoning", ""),
                },
                "metrics": file_metrics,
                "repositories_analyzed": 1,
            }
        except Exception as e:
            raise AIAnalysisError(f"Error in AI analysis: {str(e)}")

    def analyze_with_heuristics(
        self, file_metrics: CodeQualityMetrics
    ) -> CodeQualityResult:
        """
        Analyze code quality using heuristics based on file counts.

        Args:
            file_metrics: Repository file metrics

        Returns:
            CodeQualityResult with heuristic-based scores
        """
        file_count = file_metrics["file_count"]
        test_file_count = file_metrics["test_file_count"]
        doc_file_count = file_metrics["doc_file_count"]

        try:
            # Calculate scores using simple heuristics based on file counts
            # More docs = better readability (aim for ~10-20% docs)
            readability_score = min(
                100, 50 + (doc_file_count / max(1, file_count) * 500)
            )

            # More docs = better standards
            standards_score = min(100, 50 + (doc_file_count / max(1, file_count) * 500))

            # Aim for ~20% tests
            testing_score = min(100, test_file_count / max(1, file_count) * 500)

            # Complexity is hard to measure without deep code analysis, use a placeholder
            complexity_score = 70  # Default score

            # Calculate weighted score
            overall_score = self.calculate_weighted_score(
                readability_score, standards_score, complexity_score, testing_score
            )

            # Return complete result object
            return {
                "overall_score": round(overall_score, 2),
                "readability": round(readability_score, 2),
                "standards": round(standards_score, 2),
                "complexity": round(complexity_score, 2),
                "testing": round(testing_score, 2),
                "metrics": file_metrics,
                "repositories_analyzed": 1,
                "note": "Using file count heuristics for analysis due to unavailable AI processing.",
            }

        except Exception as e:
            error_msg = f"Error in fallback analysis: {str(e)}"
            print(error_msg)

            # Return structured error result
            return {
                "error": error_msg,
                "overall_score": 0,
                "readability": 0,
                "standards": 0,
                "complexity": 0,
                "testing": 0,
                "metrics": file_metrics,
                "repositories_analyzed": 0,
            }

    def calculate_weighted_score(
        self, readability: float, standards: float, complexity: float, testing: float
    ) -> float:
        """
        Calculate weighted overall score from component scores.

        Args:
            readability: Readability score (0-100)
            standards: Standards score (0-100)
            complexity: Complexity score (0-100)
            testing: Testing score (0-100)

        Returns:
            Weighted overall score (0-100)
        """
        # Calculate weighted score based on configuration weights
        weighted_score = (
            self.config.weights["readability"] * (readability / 100)
            + self.config.weights["standards"] * (standards / 100)
            + self.config.weights["complexity"] * (complexity / 100)
            + self.config.weights["testing"] * (testing / 100)
        ) * 100

        return weighted_score

    def _create_fallback_code_quality(
        self, error_message: str = None
    ) -> CodeQualityResult:
        """
        Create fallback code quality results when analysis fails.

        Args:
            error_message: Optional error message

        Returns:
            CodeQualityResult with fallback values
        """
        # Use a reasonable default score
        base_score = 75

        result = {
            "overall_score": base_score,
            "readability": base_score,
            "standards": base_score,
            "complexity": base_score,
            "testing": base_score,
            "metrics": {
                "file_count": 0,
                "test_file_count": 0,
                "doc_file_count": 0,
                "code_files_analyzed": 0,
            },
            "repositories_analyzed": 1,
        }

        if error_message:
            result["note"] = f"Used fallback quality estimation: {error_message}"

        return result
        
    def _extract_score_and_reasoning(self, response: str) -> tuple:
        """
        Extract a numeric score and reasoning from a response.
        
        Args:
            response: The LLM response text
            
        Returns:
            Tuple of (score, reasoning)
        """
        # First, try to find a score using regex
        score_patterns = [
            r'(?:score|rating)(?:\s*|:\s*|=\s*)(\d{1,3})(?:\/100|\s*\/\s*100)?',
            r'(\d{1,3})(?:\/100|\s*\/\s*100)',
            r'I would rate this as (\d{1,3})'
        ]
        
        score = 70  # Default score if no match
        for pattern in score_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                score = int(match.group(1))
                if score > 100:  # Sanity check
                    score = 100
                break
        
        # Extract reasoning - everything after the score or a reasoning label
        reasoning_patterns = [
            r'(?:reasoning|explanation|rationale|because)(?:\s*|:\s*)(.*)',
            r'(?:score|rating)(?:\s*|:\s*|=\s*)\d{1,3}(?:\/100|\s*\/\s*100)?(?:\s*|.\s*)(.*)'
        ]
        
        reasoning = ""
        for pattern in reasoning_patterns:
            match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
            if match:
                reasoning = match.group(1).strip()
                break
                
        # If no reasoning found but response exists, use the full response
        if not reasoning and response:
            # Remove any score-related text
            for pattern in score_patterns:
                response = re.sub(pattern, '', response, flags=re.IGNORECASE)
            reasoning = response.strip()
            
        return score, reasoning
    
    def _extract_suggestions(self, response: str) -> List[str]:
        """
        Extract a list of suggestions from a response.
        
        Args:
            response: The LLM response text
            
        Returns:
            List of suggestion strings
        """
        # Look for bulleted or numbered lists
        suggestion_pattern = r'(?:^|\n)[\*\-•][ \t]*(.*?)(?:\n|$)'
        numbered_pattern = r'(?:^|\n)\d+\.[ \t]*(.*?)(?:\n|$)'
        
        bullet_matches = re.findall(suggestion_pattern, response)
        numbered_matches = re.findall(numbered_pattern, response)
        
        suggestions = bullet_matches + numbered_matches
        
        # If no structured lists are found, split by newlines
        if not suggestions:
            lines = response.strip().split('\n')
            suggestions = [line.strip() for line in lines if line.strip() and len(line.strip()) > 10]
        
        # Clean up and remove duplicates
        clean_suggestions = []
        seen = set()
        for suggestion in suggestions:
            # Clean up the suggestion
            suggestion = suggestion.strip()
            
            # Skip if empty or too short
            if not suggestion or len(suggestion) < 10:
                continue
                
            # Skip if we've seen this suggestion before
            suggestion_lower = suggestion.lower()
            if suggestion_lower in seen:
                continue
                
            clean_suggestions.append(suggestion)
            seen.add(suggestion_lower)
            
        return clean_suggestions