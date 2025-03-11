"""
Code quality analysis tools for evaluating GitHub repositories.
"""

from typing import Dict, List, Any, Optional
from langchain.tools import tool, StructuredTool
from pydantic import BaseModel, Field

from src.analyzer.code_quality import CodeQualityAnalyzer
from src.models.config import Config
from src.models.types import CodeQualityResult

class CodeQualityInput(BaseModel):
    """Input for code quality analysis."""
    code_samples: List[str] = Field(..., description="List of code samples to analyze")
    repo_owner: str = Field(..., description="Owner of the repository")
    repo_name: str = Field(..., description="Name of the repository")
    repo_description: Optional[str] = Field("", description="Description of the repository")

class CodeMetricsInput(BaseModel):
    """Input for code metrics computation."""
    file_metrics: Dict[str, int] = Field(..., description="File metrics information")
    
class CodeStandardsInput(BaseModel):
    """Input for code standards evaluation."""
    code_samples: List[str] = Field(..., description="List of code samples to evaluate")
    language: Optional[str] = Field(None, description="Primary programming language of the repository")

def get_code_quality_analyzer() -> CodeQualityAnalyzer:
    """Get a CodeQualityAnalyzer instance with the current configuration."""
    config = Config.from_file()
    
    # LLM is None here, it will be set when the tool is called if available
    return CodeQualityAnalyzer(config, llm=None)

@tool("analyze_code_quality", args_schema=CodeQualityInput, return_direct=False)
def analyze_code_quality(
    code_samples: List[str], 
    repo_owner: str, 
    repo_name: str, 
    repo_description: str = ""
) -> Dict[str, Any]:
    """
    Analyze code quality using AI-based assessment of code samples.
    
    Args:
        code_samples: List of code samples to analyze
        repo_owner: Owner of the repository
        repo_name: Name of the repository
        repo_description: Description of the repository
        
    Returns:
        Dictionary containing code quality assessment results
    """
    # Import here to avoid circular imports
    from langchain_anthropic import ChatAnthropic
    import os
    
    analyzer = get_code_quality_analyzer()
    
    # Set up LLM if API key is available
    anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
    if anthropic_api_key:
        try:
            analyzer.llm = ChatAnthropic(
                model=analyzer.config.model_name,
                temperature=analyzer.config.temperature,
                anthropic_api_key=anthropic_api_key
            )
        except Exception as e:
            return {
                "success": False,
                "error": f"Error initializing LLM: {str(e)}",
                "fallback": "Using heuristic-based analysis instead"
            }
    
    try:
        # Determine if we have code samples for direct analysis
        if code_samples and len(code_samples) > 0:
            # Compute metrics based on number of files
            file_metrics = {
                "file_count": len(code_samples),
                "test_file_count": sum(1 for sample in code_samples if "test" in sample.lower() or "spec" in sample.lower()),
                "doc_file_count": sum(1 for sample in code_samples if ".md" in sample.lower() or "readme" in sample.lower()),
                "code_files_analyzed": len(code_samples)
            }
            
            # Analyze code samples
            result = analyzer.analyze_code_samples(code_samples, file_metrics)
            
            return {
                "success": True,
                "code_quality": result,
                "ai_powered": analyzer.llm is not None
            }
        else:
            # No code samples, use repository metadata for estimation
            result = analyzer.analyze_without_access(repo_owner, repo_name, repo_description)
            
            return {
                "success": True,
                "code_quality": result,
                "warning": "Analysis based on repository metadata only, no code samples provided",
                "ai_powered": analyzer.llm is not None
            }
    except Exception as e:
        # Fallback to heuristic analysis
        try:
            result = analyzer.estimate_quality_with_heuristics(repo_owner, repo_name)
            return {
                "success": True,
                "code_quality": result,
                "warning": f"AI analysis failed, using heuristics instead: {str(e)}",
                "ai_powered": False
            }
        except Exception as fallback_e:
            return {
                "success": False,
                "error": f"Error analyzing code quality: {str(e)}",
                "fallback_error": str(fallback_e)
            }

@tool("compute_code_metrics", args_schema=CodeMetricsInput, return_direct=False)
def compute_code_metrics(file_metrics: Dict[str, int]) -> Dict[str, Any]:
    """
    Compute numerical metrics about code quality from repository data.
    
    Args:
        file_metrics: Dictionary of file metrics information
        
    Returns:
        Dictionary containing computed code metrics
    """
    analyzer = get_code_quality_analyzer()
    
    try:
        # Extract metrics data
        file_count = file_metrics.get("file_count", 0)
        test_file_count = file_metrics.get("test_file_count", 0)
        doc_file_count = file_metrics.get("doc_file_count", 0)
        code_files_analyzed = file_metrics.get("code_files_analyzed", 0)
        
        # Calculate ratios and percentages
        metrics = {
            "test_to_code_ratio": test_file_count / max(1, file_count - test_file_count - doc_file_count),
            "documentation_ratio": doc_file_count / max(1, file_count),
            "test_coverage_estimate": min(100, (test_file_count / max(1, file_count - doc_file_count)) * 100),
            "total_files": file_count,
            "test_files": test_file_count,
            "documentation_files": doc_file_count,
            "code_files": file_count - test_file_count - doc_file_count
        }
        
        # Generate scores using the same algorithm from the analyzer
        readability_score = min(100, 50 + (doc_file_count / max(1, file_count) * 500))
        standards_score = min(100, 50 + (doc_file_count / max(1, file_count) * 500))
        testing_score = min(100, test_file_count / max(1, file_count) * 500)
        complexity_score = 70  # Default score
        
        # Calculate overall score
        overall_score = analyzer.calculate_weighted_score(
            readability_score, standards_score, complexity_score, testing_score
        )
        
        return {
            "success": True,
            "metrics": metrics,
            "scores": {
                "readability": round(readability_score, 2),
                "standards": round(standards_score, 2),
                "complexity": round(complexity_score, 2),
                "testing": round(testing_score, 2),
                "overall": round(overall_score, 2)
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error computing code metrics: {str(e)}"
        }

@tool("evaluate_code_standards", args_schema=CodeStandardsInput, return_direct=False)
def evaluate_code_standards(code_samples: List[str], language: Optional[str] = None) -> Dict[str, Any]:
    """
    Evaluate code samples against common coding standards and best practices.
    
    Args:
        code_samples: List of code samples to evaluate
        language: Primary programming language of the repository
        
    Returns:
        Dictionary containing code standards evaluation results
    """
    # Import here to avoid circular imports
    from langchain_anthropic import ChatAnthropic
    import os
    
    if not code_samples or len(code_samples) == 0:
        return {
            "success": False,
            "error": "No code samples provided for evaluation"
        }
    
    # Set up LLM if API key is available
    anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
    if anthropic_api_key:
        try:
            config = Config.from_file()
            llm = ChatAnthropic(
                model=config.model_name,
                temperature=config.temperature,
                anthropic_api_key=anthropic_api_key
            )
            
            # Determine language if not provided
            if not language:
                # Try to infer language from code samples
                lang_indicators = {
                    ".js": "JavaScript",
                    ".jsx": "JavaScript (React)",
                    ".ts": "TypeScript",
                    ".tsx": "TypeScript (React)",
                    ".py": "Python",
                    ".sol": "Solidity",
                    ".java": "Java",
                    ".go": "Go",
                    ".rb": "Ruby",
                    ".php": "PHP",
                    ".cs": "C#",
                    ".c": "C",
                    ".cpp": "C++"
                }
                
                for sample in code_samples:
                    for ext, lang in lang_indicators.items():
                        if ext in sample.lower():
                            language = lang
                            break
                    if language:
                        break
                
                language = language or "Unknown"
            
            # Now we have language, evaluate standards
            standards_evaluation = {
                "language": language,
                "findings": []
            }
            
            # TODO: Implement actual LLM-based code standards evaluation
            # For now, return a placeholder
            return {
                "success": True,
                "language": language,
                "message": "Code standards evaluation not yet implemented with LLM"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error setting up LLM for standards evaluation: {str(e)}"
            }
    else:
        return {
            "success": False,
            "error": "No Anthropic API key available for standards evaluation",
            "suggestion": "Set ANTHROPIC_API_KEY in environment variables"
        }

def get_code_quality_tools() -> List[StructuredTool]:
    """Get all code quality analysis tools."""
    return [
        analyze_code_quality,
        compute_code_metrics,
        evaluate_code_standards
    ]