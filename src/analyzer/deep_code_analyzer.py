"""
Deep code analysis functionality.
This module provides functionality to analyze code in depth, extracting features,
architecture patterns, and implementation details using LLM.
"""

import json
from typing import Dict, List, Any, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.models.types import DeepCodeAnalysisResult
from src.models.config import Config
from src.utils.timeout import AIAnalysisError, with_timeout, TimeoutError
from prompts.deep_code_analysis import DEEP_CODE_ANALYSIS_PROMPT, HUMAN_DEEP_CODE_ANALYSIS_PROMPT


class DeepCodeAnalyzer:
    """Analyzes codebase structure, features, and implementation details using AI."""

    def __init__(self, config: Config, llm=None):
        """
        Initialize with configuration and optional LLM.

        Args:
            config: Configuration object
            llm: Optional LangChain LLM instance
        """
        self.config = config
        self.llm = llm

    @with_timeout(120)  # Allow 2 minutes for deep analysis
    def analyze_codebase(self, code_samples: List[Dict[str, str]]) -> DeepCodeAnalysisResult:
        """
        Analyze codebase structure and features using AI.

        Args:
            code_samples: List of code samples with filename and content

        Returns:
            DeepCodeAnalysisResult with AI-based analysis
        """
        if not code_samples or self.llm is None:
            return self._create_fallback_analysis("No code samples provided or LLM not available")

        try:
            return self._analyze_with_ai(code_samples)
        except Exception as e:
            error_msg = f"Error in deep code analysis: {str(e)}"
            print(error_msg)
            return self._create_fallback_analysis(error_msg)

    def _analyze_with_ai(self, code_samples: List[Dict[str, str]]) -> DeepCodeAnalysisResult:
        """
        Perform deep code analysis using AI.

        Args:
            code_samples: List of code samples with filename and content

        Returns:
            DeepCodeAnalysisResult with AI-based analysis
        """
        # Format code samples for analysis
        formatted_samples = []
        for sample in code_samples:
            formatted_samples.append(f"File: {sample.get('filename', 'unknown')}\n\n{sample.get('content', '')}")
        
        code_sample_text = "\n\n---\n\n".join(formatted_samples)

        # Create prompt for deep code analysis
        try:
            # Use a simpler prompt template to avoid variable issues
            analysis_prompt = ChatPromptTemplate.from_template(
                DEEP_CODE_ANALYSIS_PROMPT + "\n\n" + HUMAN_DEEP_CODE_ANALYSIS_PROMPT
            )

            # Run analysis with AI model
            analysis_chain = analysis_prompt | self.llm | StrOutputParser()
            analysis_result = analysis_chain.invoke({"code_samples": code_sample_text})

            # Attempt to extract JSON from response
            # Sometimes the model returns markdown-formatted JSON with ```json tags
            if "```json" in analysis_result and "```" in analysis_result:
                # Extract content between ```json and ``` 
                json_start = analysis_result.find("```json") + 7
                json_end = analysis_result.find("```", json_start)
                if json_end > json_start:
                    analysis_result = analysis_result[json_start:json_end].strip()
            elif "```" in analysis_result:
                # Extract content between ``` and ```
                json_start = analysis_result.find("```") + 3
                json_end = analysis_result.find("```", json_start)
                if json_end > json_start:
                    analysis_result = analysis_result[json_start:json_end].strip()

            # Attempt to parse JSON, supporting both compact and pretty-printed formats
            try:
                analysis_json = json.loads(analysis_result)
            except json.JSONDecodeError:
                # Try to clean up and fix common JSON formatting issues
                # Remove comments, fix trailing commas, etc.
                cleaned_json = analysis_result.replace(",\n}", "\n}")  # Fix trailing commas
                cleaned_json = cleaned_json.replace(",]", "]")  # Fix trailing commas in arrays
                
                # Try parsing again with cleaned JSON
                analysis_json = json.loads(cleaned_json)
            
            # Ensure we have all expected fields
            codebase_breakdown = analysis_json.get("codebase_breakdown", {})
            implemented_features = analysis_json.get("implemented_features", [])
            missing_features = analysis_json.get("missing_features", [])
            frameworks = analysis_json.get("frameworks", [])
            technologies = analysis_json.get("technologies", [])
            architecture_patterns = analysis_json.get("architecture_patterns", [])
            
            # Return the structured analysis result
            return {
                "codebase_breakdown": codebase_breakdown,
                "implemented_features": implemented_features,
                "missing_features": missing_features, 
                "frameworks": frameworks,
                "technologies": technologies,
                "architecture_patterns": architecture_patterns,
                "raw_analysis": analysis_json
            }
            
        except json.JSONDecodeError as e:
            raise AIAnalysisError(f"Error parsing AI response: {str(e)}")
        except Exception as e:
            raise AIAnalysisError(f"Error in AI analysis: {str(e)}")

    def _create_fallback_analysis(self, error_message: str = None) -> DeepCodeAnalysisResult:
        """
        Create fallback analysis results when analysis fails.

        Args:
            error_message: Optional error message

        Returns:
            DeepCodeAnalysisResult with fallback values
        """
        result = {
            "codebase_breakdown": {},
            "implemented_features": [],
            "missing_features": [],
            "frameworks": [],
            "technologies": [],
            "architecture_patterns": [],
            "raw_analysis": None
        }

        if error_message:
            result["error"] = error_message

        return result