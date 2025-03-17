"""
Deep code analysis functionality.
This module provides functionality to analyze code in depth, extracting features,
architecture patterns, and implementation details using LLM.
"""

import json
import re
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

    @with_timeout(180)  # Allow 3 minutes for deep analysis
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
            # Create a simple direct prompt
            prompt_text = DEEP_CODE_ANALYSIS_PROMPT + "\n\n" + "Analyze the following code samples:\n\n" + code_sample_text + "\n\nProvide your deep code analysis in JSON format."
            
            # Use direct LLM invocation to minimize potential errors
            modified_llm = self.llm
            if hasattr(self.llm, 'temperature'):
                # Use a lower temperature for more consistent results
                modified_llm = self.llm.with_config(temperature=0.1)
                
            # Run analysis with direct invocation
            analysis_result = modified_llm.invoke(prompt_text).content
            
            # Debug output to see what's happening
            print(f"Deep code analysis raw response length: {len(analysis_result)} characters")
            print(f"Response begins with: {analysis_result[:100]}...")

            # Extract JSON with improved error handling
            analysis_json = self._extract_json_from_llm_response(analysis_result)
            
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
            "codebase_breakdown": {
                "structure": "Analysis failed - using fallback response",
                "components": ["Unable to determine components"],
                "interactions": "Unable to analyze component interactions", 
                "code_organization": "Unable to analyze code organization"
            },
            "implemented_features": ["Unable to determine implemented features"],
            "missing_features": ["Unable to determine missing or incomplete features"],
            "frameworks": ["Unable to detect frameworks"],
            "technologies": ["Unable to detect technologies"],
            "architecture_patterns": ["Unable to detect architecture patterns"],
            "raw_analysis": None
        }

        if error_message:
            result["error"] = error_message

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
            # Look for first JSON-like object starting with { and ending with }
            r'(\{[\s\S]*?\})',
            # Look for JSON after common prefixes like "Here's the analysis:"
            r'(?:analysis|result|JSON).*?(\{[\s\S]*\})',
        ]
        
        # Store the original text as fallback
        json_candidate = text
        
        # Try each pattern to find a potential JSON block
        for pattern in json_patterns:
            matches = re.search(pattern, text)
            if matches:
                json_candidate = matches.group(1)
                print(f"Extracted JSON using pattern: {pattern[:30]}...")
                break
                
        # Try direct parsing first
        try:
            return json.loads(json_candidate)
        except json.JSONDecodeError:
            print("Standard JSON extraction failed, trying advanced cleaning...")
            
        # Fix double-bracketed pattern {{...}} which is a common error
        try:
            cleaned = re.sub(r'{{', '{', json_candidate)
            cleaned = re.sub(r'}}', '}', cleaned)
            
            # Fix single quotes to double quotes
            cleaned = re.sub(r"'([^']*)'", r'"\1"', cleaned)
            
            # Fix trailing commas
            cleaned = re.sub(r',\s*}', '}', cleaned)
            cleaned = re.sub(r',\s*]', ']', cleaned)
            
            # Try parsing again with cleaned JSON
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                print("First cleaning attempt failed, trying more aggressive methods...")
        except Exception as regex_error:
            print(f"Error in regex cleaning: {str(regex_error)}")
            
        # If we still don't have valid JSON, try even more aggressive extraction
        try:
            # Look for anything that might be a JSON object
            start_idx = json_candidate.find('{')
            end_idx = json_candidate.rfind('}')
            
            if start_idx >= 0 and end_idx > start_idx:
                extracted = json_candidate[start_idx:end_idx+1]
                
                # Try to fix common issues with a more comprehensive approach
                # Replace single quotes with double quotes
                extracted = extracted.replace("'", '"')
                
                # Fix unquoted property names
                property_pattern = r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)(\s*:)'
                extracted = re.sub(property_pattern, r'\1"\2"\3', extracted)
                
                try:
                    return json.loads(extracted)
                except json.JSONDecodeError as e:
                    print(f"Advanced extraction failed: {str(e)}")
        except Exception as e:
            print(f"Error in advanced extraction: {str(e)}")
        
        # If all else fails, return a fallback structure
        print("All JSON parsing attempts failed, using fallback structure")
        return {
            "codebase_breakdown": {
                "structure": "Structure analysis failed due to JSON parsing error",
                "components": ["Components could not be extracted due to parsing error"],
                "interactions": "Interaction analysis unavailable due to parsing error",
                "code_organization": "Organization analysis unavailable due to parsing error"
            },
            "implemented_features": [
                "Feature analysis unavailable due to parsing error",
                "Please run the analysis again for better results"
            ],
            "missing_features": [
                "Missing feature analysis unavailable due to parsing error"
            ],
            "frameworks": [
                "Framework detection unavailable due to parsing error"
            ],
            "technologies": [
                "Technology detection unavailable due to parsing error"
            ],
            "architecture_patterns": [
                "Architecture pattern detection unavailable due to parsing error"
            ],
            "additional_insights": "JSON parsing from LLM response failed. The raw response might contain useful information but could not be automatically parsed."
        }