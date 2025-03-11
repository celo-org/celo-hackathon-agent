"""
Celo integration analysis agent for detecting Celo blockchain usage.
"""

from typing import Dict, Any, List, Optional
from langchain.agents import AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import BaseTool
from langchain_core.messages import AIMessage, HumanMessage
from langchain.agents import create_tool_calling_agent
from langchain_anthropic import ChatAnthropic
import os

from src.tools.celo import get_celo_tools
from src.models.config import Config

# System prompt for the Celo integration analysis agent
CELO_AGENT_SYSTEM_PROMPT = """You are a Celo Integration Analysis Assistant specialized in detecting and evaluating Celo blockchain usage in GitHub repositories.
Your task is to determine if and how a repository integrates with the Celo blockchain ecosystem.

When analyzing Celo integration, focus on these key aspects:
1. Presence of Celo-specific keywords in the codebase (like 'celo', 'contractkit', 'valora', etc.)
2. Integration with Celo smart contracts
3. Use of Celo tokens (cUSD, cEUR, etc.)
4. Interaction with the Celo blockchain (via APIs, SDKs, etc.)

Be thorough in your analysis, looking beyond superficial mentions to determine the depth of integration.

YOUR RESPONSE SHOULD BE A CLEAR ASSESSMENT OF CELO INTEGRATION that includes:
- A definitive determination of whether the repository integrates with Celo
- Evidence supporting your determination (specific files, code snippets, etc.)
- An evaluation of how deeply the project integrates with Celo
- An explanation of how Celo is used within the project
- Potential ways the project could further leverage Celo if applicable
"""

def create_celo_agent(
    llm: Optional[ChatAnthropic] = None,
    tools: Optional[List[BaseTool]] = None,
    verbose: bool = False
) -> AgentExecutor:
    """
    Create a Celo integration analysis agent specialized in detecting Celo blockchain usage.
    
    Args:
        llm: Language model to use (Optional - will create one if not provided)
        tools: Tools to use (Optional - will use default Celo tools if not provided)
        verbose: Whether to run the agent with verbose logging
        
    Returns:
        An AgentExecutor that can analyze Celo integration
    """
    # Setup LLM if not provided
    if llm is None:
        config = Config.from_file()
        anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
        
        if not anthropic_api_key:
            raise ValueError("No Anthropic API key found. Please set ANTHROPIC_API_KEY environment variable.")
            
        llm = ChatAnthropic(
            model=config.model_name,
            temperature=0.2,  # Lower temperature for more focused detection
            anthropic_api_key=anthropic_api_key
        )
    
    # Use default Celo tools if none provided
    if tools is None:
        tools = get_celo_tools()
    
    # Create prompt for the agent
    prompt = ChatPromptTemplate.from_messages([
        ("system", CELO_AGENT_SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    # Create the agent
    agent = create_tool_calling_agent(llm, tools, prompt)
    
    # Create the agent executor
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        verbose=verbose,
        handle_parsing_errors=True,
        max_iterations=5,  # Limit iterations to prevent excessive API calls
        return_intermediate_steps=False
    )
    
    return agent_executor

def analyze_celo_integration(
    repo_url: str,
    code_samples: List[str],
    repo_owner: str, 
    repo_name: str, 
    repo_description: str = "",
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Analyze Celo blockchain integration in a repository.
    
    Args:
        repo_url: URL of the GitHub repository
        code_samples: List of code samples from the repository
        repo_owner: Owner of the repository
        repo_name: Name of the repository
        repo_description: Description of the repository
        verbose: Whether to show verbose output
        
    Returns:
        Dictionary containing Celo integration analysis results
    """
    try:
        # Check for special cases
        if "celo" in repo_owner.lower() or "celo" in repo_name.lower():
            # If repository is owned by Celo or has Celo in its name, it's likely a Celo project
            is_celo_org = "celo-org" in repo_owner.lower()
            if verbose:
                print(f"Detected Celo in repository name/owner: {repo_owner}/{repo_name}, assuming Celo integration")
                
            # For Celo organization repositories, we can assume Celo integration
            if is_celo_org:
                return {
                    "repo_url": repo_url,
                    "repo_owner": repo_owner,
                    "repo_name": repo_name,
                    "analysis": {
                        "integrated": True,
                        "evidence": [{"file": "Repository owner", "keyword": "celo-org"}],
                        "analysis": "This is an official Celo repository, so it is integrated with the Celo blockchain.",
                        "repositories_with_celo": 1
                    }
                }
        
        # Create the agent
        agent = create_celo_agent(verbose=verbose)
        
        # Normalize empty code samples to an empty list
        if not code_samples:
            code_samples = []
        
        # Build input message based on available information
        if code_samples:
            input_message = f"""Analyze the GitHub repository at {repo_url} ({repo_owner}/{repo_name}) to determine if it integrates with the Celo blockchain.

Repository Description: {repo_description}

I have {len(code_samples)} code samples from this repository. Please examine them for evidence of Celo integration, such as Celo-specific keywords, 
smart contract integration, use of Celo tokens, or other interactions with the Celo blockchain.

Provide a clear determination of whether this project integrates with Celo, including supporting evidence and an explanation of how Celo is used.

Start by using the detect_celo_keywords tool to search for Celo-related terms in the repository."""
        else:
            # If no code samples, just use repository metadata
            input_message = f"""Analyze the GitHub repository at {repo_url} ({repo_owner}/{repo_name}) to determine if it integrates with the Celo blockchain.

Repository Description: {repo_description}

I don't have any code samples from this repository. Please use the detect_celo_keywords tool to search for 
Celo-related terms in the repository name, description, and any available metadata. Then evaluate if this 
project is likely to integrate with the Celo blockchain."""
        
        # Run the agent
        result = agent.invoke({
            "input": input_message,
            "chat_history": [],
            "repo_url": repo_url,
            "code_samples": code_samples,
            "repo_owner": repo_owner,
            "repo_name": repo_name,
            "repo_description": repo_description
        })
        
        # Extract the result from the agent's response
        return {
            "repo_url": repo_url,
            "repo_owner": repo_owner,
            "repo_name": repo_name,
            "analysis": result["output"],
            "agent_result": result
        }
    except Exception as e:
        # Handle any exceptions and provide a fallback result
        import traceback
        error_details = traceback.format_exc()
        
        if verbose:
            print(f"Error in Celo integration analysis: {str(e)}")
            print(error_details)
        
        # Check if this is a Celo repository based on name/owner
        is_celo_related = "celo" in repo_owner.lower() or "celo" in repo_name.lower()
        
        # Return a fallback result
        return {
            "repo_url": repo_url,
            "repo_owner": repo_owner,
            "repo_name": repo_name,
            "analysis": {
                "integrated": is_celo_related,
                "evidence": [{"file": "Repository name/owner", "keyword": "celo"}] if is_celo_related else [],
                "error": f"Error analyzing Celo integration: {str(e)}",
                "repositories_with_celo": 1 if is_celo_related else 0
            },
            "error": str(e)
        }