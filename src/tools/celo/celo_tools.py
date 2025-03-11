"""
Celo integration detection tools for analyzing GitHub repositories.
"""

from typing import Dict, List, Any, Optional
from langchain.tools import tool, StructuredTool
from pydantic import BaseModel, Field

from src.analyzer.celo_detector import CeloIntegrationDetector
from src.models.config import Config
from src.models.types import CeloIntegrationResult, CeloEvidence

class CeloKeywordsInput(BaseModel):
    """Input for Celo keyword detection."""
    repo_url: str = Field(..., description="URL of the GitHub repository to analyze")
    code_samples: Optional[List[str]] = Field(None, description="Optional list of code samples to check for Celo keywords")

class ContractIntegrationInput(BaseModel):
    """Input for smart contract integration analysis."""
    code_samples: List[str] = Field(..., description="List of code samples to analyze for contract integration")
    
class CeloUsageInput(BaseModel):
    """Input for evaluating Celo usage."""
    repo_owner: str = Field(..., description="Owner of the repository")
    repo_name: str = Field(..., description="Name of the repository")
    repo_description: Optional[str] = Field("", description="Description of the repository")
    evidence: Optional[List[Dict[str, str]]] = Field(None, description="Optional evidence of Celo integration")

def get_celo_detector() -> CeloIntegrationDetector:
    """Get a CeloIntegrationDetector instance with the current configuration."""
    config = Config.from_file()
    
    # LLM is None here, it will be set when the tool is called if available
    return CeloIntegrationDetector(config, llm=None)

@tool("detect_celo_keywords", args_schema=CeloKeywordsInput, return_direct=False)
def detect_celo_keywords(repo_url: str, code_samples: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Detect Celo-related keywords in repository files or code samples.
    
    Args:
        repo_url: URL of the GitHub repository to analyze
        code_samples: Optional list of code samples to check for Celo keywords
        
    Returns:
        Dictionary containing detected Celo keywords and their locations
    """
    # Import here to avoid circular imports
    from src.analyzer.github_repo import GitHubRepository
    from src.analyzer.celo_detector import CeloIntegrationDetector
    
    # Get configuration and detector
    config = Config.from_file()
    detector = get_celo_detector()
    github_repo = GitHubRepository(config)
    
    # Setup repository connection using gitingest
    repo_owner, repo_name = github_repo.setup_repository(repo_url)
    
    # Define keywords to search for
    celo_keywords = config.celo_keywords
    
    evidence = []
    
    # If code samples are provided, search them first
    if code_samples and len(code_samples) > 0:
        for sample in code_samples:
            sample_lines = sample.split('\n')
            file_name = "Unknown"
            
            # Try to extract file name from the first line (if it starts with "File: ")
            if sample_lines and sample_lines[0].startswith("File: "):
                file_name = sample_lines[0].replace("File: ", "").strip()
                
            # Search for keywords in the sample
            for keyword in celo_keywords:
                if keyword.lower() in sample.lower():
                    evidence.append({
                        "file": file_name,
                        "keyword": keyword
                    })
                    break  # One evidence per file is enough
    
    # If we have access to the repository via gitingest, search content
    if github_repo.repo_data and github_repo.content and (not evidence or len(evidence) == 0):
        try:
            # Use the CeloIntegrationDetector with gitingest data
            detector = CeloIntegrationDetector(config)
            repo_evidence = detector.search_repository_content(github_repo.content)
            if repo_evidence:
                evidence.extend(repo_evidence)
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error searching repository content: {str(e)}",
                "repo_owner": repo_owner,
                "repo_name": repo_name
            }
    
    # Determine if Celo is integrated based on evidence
    is_integrated = len(evidence) > 0
    
    return {
        "success": True,
        "repo_owner": repo_owner,
        "repo_name": repo_name,
        "celo_keywords": celo_keywords,
        "evidence": evidence,
        "is_integrated": is_integrated,
        "evidence_count": len(evidence)
    }

@tool("analyze_contract_integration", args_schema=ContractIntegrationInput, return_direct=False)
def analyze_contract_integration(code_samples: List[str]) -> Dict[str, Any]:
    """
    Analyze smart contract integration with Celo blockchain.
    
    Args:
        code_samples: List of code samples to analyze for contract integration
        
    Returns:
        Dictionary containing contract integration analysis results
    """
    # Import here to avoid circular imports
    from langchain_anthropic import ChatAnthropic
    import os
    
    # Get configuration and detector
    config = Config.from_file()
    
    # Initialize LLM if available
    anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not anthropic_api_key:
        return {
            "success": False,
            "error": "No Anthropic API key available for contract analysis",
            "suggestion": "Set ANTHROPIC_API_KEY in environment variables"
        }
    
    # Filter for solidity files or files with contract-related code
    contract_samples = []
    for sample in code_samples:
        if ".sol" in sample.lower() or "contract " in sample.lower() or "web3" in sample.lower():
            contract_samples.append(sample)
    
    if not contract_samples:
        return {
            "success": True,
            "has_contracts": False,
            "message": "No smart contract code detected in the provided samples"
        }
    
    try:
        # Initialize LLM for analysis
        llm = ChatAnthropic(
            model=config.model_name,
            temperature=config.temperature,
            anthropic_api_key=anthropic_api_key
        )
        
        # TODO: Implement detailed contract analysis with LLM
        # For now, return a placeholder with detected contracts
        
        return {
            "success": True,
            "has_contracts": True,
            "contract_count": len(contract_samples),
            "message": "Smart contract analysis not yet fully implemented with LLM"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error analyzing contract integration: {str(e)}"
        }

@tool("evaluate_celo_usage", args_schema=CeloUsageInput, return_direct=False)
def evaluate_celo_usage(
    repo_owner: str, 
    repo_name: str, 
    repo_description: str = "", 
    evidence: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Evaluate how extensively Celo blockchain is used in a repository.
    
    Args:
        repo_owner: Owner of the repository
        repo_name: Name of the repository
        repo_description: Description of the repository
        evidence: Optional evidence of Celo integration found by other tools
        
    Returns:
        Dictionary containing Celo usage evaluation results
    """
    # Import here to avoid circular imports
    from langchain_anthropic import ChatAnthropic
    import os
    
    # Get detector with configuration
    detector = get_celo_detector()
    
    # Set up LLM if API key is available
    anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
    if anthropic_api_key:
        try:
            detector.llm = ChatAnthropic(
                model=detector.config.model_name,
                temperature=detector.config.temperature,
                anthropic_api_key=anthropic_api_key
            )
        except Exception as e:
            return {
                "success": False,
                "error": f"Error initializing LLM: {str(e)}",
                "fallback": "Using basic heuristics instead"
            }
    
    # If no evidence provided, use heuristics based on repository name and owner
    if not evidence or len(evidence) == 0:
        # Check if repository name or owner contains "celo"
        has_celo_in_name = "celo" in repo_name.lower() or "celo" in repo_owner.lower()
        
        if has_celo_in_name:
            evidence = [{"file": "Repository name/owner", "keyword": "celo"}]
    
    # Determine integration status
    is_integrated = evidence is not None and len(evidence) > 0
    
    # If evidence exists and we have LLM, generate an analysis
    analysis = None
    if is_integrated and detector.llm is not None:
        try:
            # Format evidence for the prompt
            evidence_str = "\n".join([f"- Found '{e['keyword']}' in {e['file']}" for e in evidence])
            
            # Generate analysis
            analysis = detector.analyze_celo_evidence(evidence)
        except Exception as e:
            return {
                "success": True,
                "is_integrated": is_integrated,
                "evidence_count": len(evidence) if evidence else 0,
                "analysis_error": f"Error generating analysis: {str(e)}"
            }
    
    return {
        "success": True,
        "is_integrated": is_integrated,
        "evidence_count": len(evidence) if evidence else 0,
        "evidence": evidence,
        "analysis": analysis,
        "ai_powered": detector.llm is not None
    }

def get_celo_tools() -> List[StructuredTool]:
    """Get all Celo integration detection tools."""
    return [
        detect_celo_keywords,
        analyze_contract_integration,
        evaluate_celo_usage
    ]