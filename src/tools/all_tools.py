"""
Combine all tools for agent use.
"""

from typing import List
from langchain.tools import BaseTool

from src.tools.repo import get_repository_tools
from src.tools.code_quality import get_code_quality_tools
from src.tools.celo import get_celo_tools
from src.tools.reporting import get_reporting_tools

def get_all_tools() -> List[BaseTool]:
    """
    Get all available tools for the Celo Hackathon Analysis agent.
    
    Returns:
        List of all tools from all categories
    """
    all_tools = []
    
    # Add repository tools
    all_tools.extend(get_repository_tools())
    
    # Add code quality tools
    all_tools.extend(get_code_quality_tools())
    
    # Add Celo integration tools
    all_tools.extend(get_celo_tools())
    
    # Add reporting tools
    all_tools.extend(get_reporting_tools())
    
    return all_tools