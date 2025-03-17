"""
Code quality analysis functionality.
"""

import json
import re
from typing import Dict, List, Tuple, Any, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import StrOutputParser

from src.models.types import CodeQualityResult, CodeQualityMetrics
from src.models.config import Config
from src.utils.timeout import AIAnalysisError, with_timeout, TimeoutError
from prompts.code_quality import CODE_QUALITY_PROMPT, HUMAN_CODE_QUALITY_PROMPT


class CodeQualityAnalyzer:
    """Analyzes code quality using AI and heuristics."""

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
            # Create direct prompt text
            prompt_text = f"""You are a senior software engineer tasked with making a rough estimate of a GitHub repository's code quality.
            Based on the limited information provided about the repository (name, organization, description), 
            provide a reasonable estimate of what the code quality might be like.
            
            Repository: {repo_owner}/{repo_name}
            Description: {repo_description}
            
            I don't have direct access to the code, so please make an educated guess based on the repository name,
            owner, and any other information you might know about this project. If you've heard of this repository
            before, you can use that knowledge.
            
            Respond in JSON format:
            {{
                "readability": {{"score": 0-100, "reasoning": "explanation"}},
                "standards": {{"score": 0-100, "reasoning": "explanation"}},
                "complexity": {{"score": 0-100, "reasoning": "explanation"}},
                "testing": {{"score": 0-100, "reasoning": "explanation"}},
                "overall_analysis": "brief overall analysis",
                "suggestions": ["suggestion1", "suggestion2"]
            }}
            """

            # Use direct LLM invocation with lower temperature
            modified_llm = self.llm
            if hasattr(self.llm, 'temperature'):
                modified_llm = self.llm.with_config(temperature=0.1)
                
            analysis_result = modified_llm.invoke(prompt_text).content
            
            # Parse the response with error handling
            analysis_json = self._extract_json_from_llm_response(analysis_result)

            # Extract scores and reasoning from AI response
            readability = analysis_json.get("readability", {})
            standards = analysis_json.get("standards", {})
            complexity = analysis_json.get("complexity", {})
            testing = analysis_json.get("testing", {})

            readability_score = (
                readability.get("score", 0) if isinstance(readability, dict) else 0
            )
            standards_score = (
                standards.get("score", 0) if isinstance(standards, dict) else 0
            )
            complexity_score = (
                complexity.get("score", 0) if isinstance(complexity, dict) else 0
            )
            testing_score = testing.get("score", 0) if isinstance(testing, dict) else 0

            # Calculate weighted score
            overall_score = self.calculate_weighted_score(
                readability_score, standards_score, complexity_score, testing_score
            )

            # Compile and return the results
            return {
                "overall_score": round(overall_score, 2),
                "readability": readability_score,
                "standards": standards_score,
                "complexity": complexity_score,
                "testing": testing_score,
                "ai_analysis": {
                    "overall_analysis": analysis_json.get("overall_analysis", "")
                    + " (Note: This is an estimate based on limited information)",
                    "suggestions": analysis_json.get("suggestions", []),
                    "readability_reasoning": readability.get("reasoning", ""),
                    "standards_reasoning": standards.get("reasoning", ""),
                    "complexity_reasoning": complexity.get("reasoning", ""),
                    "testing_reasoning": testing.get("reasoning", ""),
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

    @with_timeout(60)
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
        Analyze code quality using AI.

        Args:
            code_samples: List of code samples
            file_metrics: Repository file metrics

        Returns:
            CodeQualityResult with AI-based analysis
        """
        # Combine code samples for analysis
        code_sample_text = "\n".join(code_samples)

        # Create prompt for code quality analysis
        try:
            # Create a direct prompt that doesn't rely on template formatting
            prompt_text = CODE_QUALITY_PROMPT + "\n\n" + "Analyze the following code samples:\n\n" + code_sample_text + "\n\nProvide your quality assessment in JSON format."
            
            # Use direct LLM invocation to minimize potential errors
            modified_llm = self.llm
            if hasattr(self.llm, 'temperature'):
                # Use a lower temperature for more consistent results
                modified_llm = self.llm.with_config(temperature=0.1)
                
            # Run analysis with direct invocation
            analysis_result = modified_llm.invoke(prompt_text).content
            
            # Debug output to see what's happening
            print(f"Code quality analysis raw response length: {len(analysis_result)} characters")
            print(f"Response begins with: {analysis_result[:100]}...")

            # Extract and parse JSON
            analysis_json = self._extract_json_from_llm_response(analysis_result)

            # Extract scores and reasoning
            readability = analysis_json.get("readability", {})
            standards = analysis_json.get("standards", {})
            complexity = analysis_json.get("complexity", {})
            testing = analysis_json.get("testing", {})

            readability_score = (
                readability.get("score", 0) if isinstance(readability, dict) else 0
            )
            standards_score = (
                standards.get("score", 0) if isinstance(standards, dict) else 0
            )
            complexity_score = (
                complexity.get("score", 0) if isinstance(complexity, dict) else 0
            )
            testing_score = testing.get("score", 0) if isinstance(testing, dict) else 0

            # Calculate weighted score
            overall_score = self.calculate_weighted_score(
                readability_score, standards_score, complexity_score, testing_score
            )

            # Compile and return the results
            return {
                "overall_score": round(overall_score, 2),
                "readability": readability_score,
                "standards": standards_score,
                "complexity": complexity_score,
                "testing": testing_score,
                "ai_analysis": {
                    "overall_analysis": analysis_json.get("overall_analysis", ""),
                    "suggestions": analysis_json.get("suggestions", []),
                    "readability_reasoning": readability.get("reasoning", ""),
                    "standards_reasoning": standards.get("reasoning", ""),
                    "complexity_reasoning": complexity.get("reasoning", ""),
                    "testing_reasoning": testing.get("reasoning", ""),
                },
                "metrics": file_metrics,
                "repositories_analyzed": 1,
            }
        except json.JSONDecodeError as e:
            raise AIAnalysisError(f"Error parsing AI response: {str(e)}")
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
        
    def _extract_json_from_llm_response(self, text: str) -> Dict[str, Any]:
        """
        Extract valid JSON from LLM response text with improved error handling.
        
        Args:
            text: Raw text from LLM
            
        Returns:
            Parsed JSON object
        """
        # First, try to find and extract a JSON object from the response
        json_patterns = [
            # Look for content between JSON code blocks
            r'```(?:json)?\s*(\{[\s\S]*?\})\s*```',
            # Look for content between JSON tags
            r'<json>\s*(\{[\s\S]*?\})\s*</json>',
            # Look for content between brackets (full response)
            r'^(?:\s*)\{[\s\S]*\}(?:\s*)$',
            # Look for just the first JSON object in the response
            r'(\{[\s\S]*?\})(?:\s|$)',
        ]
        
        # Store the best candidate
        json_candidate = text
        
        # Try each pattern to find a potential JSON block
        for pattern in json_patterns:
            matches = re.search(pattern, text)
            if matches:
                json_candidate = matches.group(1)
                print(f"Extracted JSON using pattern: {pattern[:30]}...")
                break
                
        # If we still don't have valid JSON, try more aggressive cleaning
        try:
            return json.loads(json_candidate)
        except json.JSONDecodeError:
            print("Standard JSON extraction failed, trying advanced cleaning...")
            
        # Fix double-bracketed pattern {{...}} which is a common error
        cleaned = re.sub(r'{{', '{', json_candidate)
        cleaned = re.sub(r'}}', '}', cleaned)
        
        # Fix single quotes to double quotes (outside of strings)
        def replace_quotes(match):
            return '"' + match.group(1) + '"'
            
        cleaned = re.sub(r"'([^']*)'", replace_quotes, cleaned)
        
        # Fix trailing commas
        cleaned = re.sub(r',\s*}', '}', cleaned)
        cleaned = re.sub(r',\s*]', ']', cleaned)
        
        # Try parsing the cleaned JSON
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            print(f"Advanced JSON cleaning failed: {str(e)}")
            
            # If all cleaning fails, provide a fallback response
            return {
                "readability": {"score": 70, "reasoning": "Analysis failed, using fallback scores"},
                "standards": {"score": 70, "reasoning": "Analysis failed, using fallback scores"},
                "complexity": {"score": 70, "reasoning": "Analysis failed, using fallback scores"},
                "testing": {"score": 70, "reasoning": "Analysis failed, using fallback scores"},
                "overall_analysis": "JSON parsing failed. Using fallback scores.",
                "suggestions": ["Run analysis again to get proper analysis"]
            }