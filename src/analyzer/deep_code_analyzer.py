"""
Deep code analysis functionality using a question-based approach.
This module provides functionality to analyze code in depth, extracting features,
architecture patterns, and implementation details using LLM.
"""

import re
from typing import Dict, List, Any, Optional

from src.models.types import DeepCodeAnalysisResult
from src.models.config import Config
from src.utils.timeout import AIAnalysisError, with_timeout, TimeoutError


class DeepCodeAnalyzer:
    """Analyzes codebase structure, features, and implementation details using targeted LLM questions."""

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
            return self._analyze_with_direct_questions(code_samples)
        except Exception as e:
            error_msg = f"Error in deep code analysis: {str(e)}"
            print(error_msg)
            return self._create_fallback_analysis(error_msg)

    def _analyze_with_direct_questions(self, code_samples: List[Dict[str, str]]) -> DeepCodeAnalysisResult:
        """
        Perform deep code analysis using direct questions instead of structured JSON.

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
        
        # Define analysis questions for each aspect we want to analyze
        analysis_questions = [
            {
                "category": "implemented_features",
                "question": "List all features that have been implemented in this codebase. Be specific and comprehensive.",
                "parse_func": self._parse_list_response
            },
            {
                "category": "missing_features",
                "question": "Identify any features that appear to be missing, incomplete, or potentially buggy in this codebase.",
                "parse_func": self._parse_list_response
            },
            {
                "category": "frameworks",
                "question": "List all frameworks used in this project (like React, Next.js, Express, etc.).",
                "parse_func": self._parse_list_response
            },
            {
                "category": "technologies",
                "question": "List all technologies used in this codebase (languages, databases, authentication methods, etc.).",
                "parse_func": self._parse_list_response
            },
            {
                "category": "architecture_patterns",
                "question": "Identify architectural patterns used in this codebase (MVC, microservices, event-driven, etc.).",
                "parse_func": self._parse_list_response
            },
            {
                "category": "codebase_structure",
                "question": "Describe the overall structure of this codebase, including organization and how components interact.",
                "parse_func": self._parse_text_response
            }
        ]
        
        # Create a new result structure
        result = {
            "codebase_breakdown": {
                "structure": "",
                "components": [],
                "interactions": "",
                "code_organization": "",
            },
            "implemented_features": [],
            "missing_features": [],
            "frameworks": [],
            "technologies": [],
            "architecture_patterns": [],
            "raw_analysis": {}
        }
        
        # Use direct LLM invocation with lower temperature
        modified_llm = self.llm
        if hasattr(self.llm, 'temperature'):
            # Use a lower temperature for more consistent results
            modified_llm = self.llm.with_config(temperature=0.1)
            
        # Run each question separately and parse the results
        for question_info in analysis_questions:
            try:
                print(f"Asking question about {question_info['category']}...")
                
                # Craft the prompt
                prompt = f"""Analyze the following code samples:

{code_sample_text}

QUESTION: {question_info['question']}

Please be specific and detailed in your response. 
Respond with a numbered list if applicable, or detailed paragraphs for structural questions.
"""
                
                # Get the response from the LLM
                response = modified_llm.invoke(prompt).content
                
                # Parse the response based on the category
                parsed_result = question_info["parse_func"](response)
                
                # Add the parsed result to our result structure
                if question_info["category"] == "codebase_structure":
                    result["codebase_breakdown"]["structure"] = parsed_result
                    
                    # Extract components from the structure response
                    components = self._extract_components(response)
                    result["codebase_breakdown"]["components"] = components
                    
                    # Add interactions and organization info (from the same response)
                    interactions = self._extract_interactions(response)
                    result["codebase_breakdown"]["interactions"] = interactions
                    
                    organization = self._extract_organization(response)
                    result["codebase_breakdown"]["code_organization"] = organization
                else:
                    result[question_info["category"]] = parsed_result
                
            except Exception as e:
                print(f"Error getting answer for {question_info['category']}: {str(e)}")
                # We continue with other questions even if one fails
        
        # Add raw analysis data
        result["raw_analysis"] = {
            "structure_description": result["codebase_breakdown"]["structure"],
            "components": result["codebase_breakdown"]["components"],
            "features": result["implemented_features"],
            "missing_features": result["missing_features"]
        }
        
        return result

    def _parse_list_response(self, response: str) -> List[str]:
        """Parse a response into a list of items."""
        # Remove any markdown formatting
        clean_response = response.replace('```', '')
        
        # Try to find numbered or bulleted list items
        bullet_pattern = r'(?:^|\n)[\*\-•][ \t]*(.*?)(?:\n|$)'
        numbered_pattern = r'(?:^|\n)\d+\.[ \t]*(.*?)(?:\n|$)'
        
        bullet_matches = re.findall(bullet_pattern, clean_response)
        numbered_matches = re.findall(numbered_pattern, clean_response)
        
        items = bullet_matches + numbered_matches
        
        # If no list structure is found, split by newlines and filter
        if not items:
            lines = clean_response.split('\n')
            items = [line.strip() for line in lines if line.strip() and len(line.strip()) > 10]
        
        # Remove duplicates while preserving order
        unique_items = []
        for item in items:
            item = item.strip()
            if item and item not in unique_items:
                unique_items.append(item)
                
        return unique_items
        
    def _parse_text_response(self, response: str) -> str:
        """Parse a free-text response."""
        # Remove any markdown formatting and clean up
        clean_response = response.replace('```', '')
        
        # Remove common prefixes like "Here's an analysis:"
        prefixes = [
            "here is", "here's", "based on", "after analyzing", 
            "the codebase", "from the provided", "looking at"
        ]
        
        lower_response = clean_response.lower()
        for prefix in prefixes:
            if lower_response.startswith(prefix):
                clean_response = clean_response[len(prefix):].strip()
        
        return clean_response
        
    def _extract_components(self, response: str) -> List[str]:
        """Extract component information from the structure response."""
        # Look for sections that mention components
        component_pattern = r'(?:components|modules|parts|sections).*?(?:\n|:)((?:.*?\n)+)'
        matches = re.search(component_pattern, response, re.IGNORECASE)
        
        if matches:
            component_section = matches.group(1)
            return self._parse_list_response(component_section)
        
        # Fallback - look for any capitalized terms that might be components
        # This is a very simplified approach
        component_candidates = re.findall(r'\b([A-Z][a-zA-Z]+(?:Component|View|Controller|Model|Service|Module|Manager))\b', response)
        
        if component_candidates:
            return list(set(component_candidates))
            
        # If all else fails, just extract some key phrases
        return self._extract_key_phrases(response, ["component", "module", "class", "service"])
            
    def _extract_interactions(self, response: str) -> str:
        """Extract interaction information from the structure response."""
        # Look for sections describing interactions
        interaction_pattern = r'(?:interact|communication|connection|flow).*?(?:\n|:)((?:.*?\n)+)'
        matches = re.search(interaction_pattern, response, re.IGNORECASE)
        
        if matches:
            return matches.group(1).strip()
        
        # If no specific section, look for sentences containing interaction terminology
        sentences = re.split(r'(?<=[.!?])\s+', response)
        interaction_sentences = []
        
        interaction_terms = ["interact", "communic", "connect", "flow", "call", "send", "receive", "depend"]
        for sentence in sentences:
            if any(term in sentence.lower() for term in interaction_terms):
                interaction_sentences.append(sentence)
                
        if interaction_sentences:
            return " ".join(interaction_sentences)
            
        return "Component interaction information not specifically identified."
        
    def _extract_organization(self, response: str) -> str:
        """Extract organization information from the structure response."""
        # Look for sections describing organization
        org_pattern = r'(?:organiz|structur|architect|folder|director).*?(?:\n|:)((?:.*?\n)+)'
        matches = re.search(org_pattern, response, re.IGNORECASE)
        
        if matches:
            return matches.group(1).strip()
            
        # If no specific section, extract relevant sentences
        sentences = re.split(r'(?<=[.!?])\s+', response)
        org_sentences = []
        
        org_terms = ["organiz", "structur", "folder", "direct", "package", "layout"]
        for sentence in sentences:
            if any(term in sentence.lower() for term in org_terms):
                org_sentences.append(sentence)
                
        if org_sentences:
            return " ".join(org_sentences)
            
        return "Code organization information not specifically identified."
        
    def _extract_key_phrases(self, text: str, keywords: List[str]) -> List[str]:
        """Extract phrases containing keywords."""
        result = []
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        for sentence in sentences:
            for keyword in keywords:
                if keyword.lower() in sentence.lower():
                    # Try to extract a concise phrase
                    parts = sentence.split(',')
                    for part in parts:
                        if keyword.lower() in part.lower():
                            # Clean and add to results
                            clean_part = part.strip().rstrip('.!?')
                            if len(clean_part) > 0 and len(clean_part) < 100:  # Avoid too long phrases
                                result.append(clean_part)
                                
        return list(set(result))[:5]  # Return up to 5 unique phrases

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