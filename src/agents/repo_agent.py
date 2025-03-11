"""
Repository analysis agent for exploring GitHub repositories.
"""

from typing import Dict, Any, List, Optional
from langchain.agents import AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import BaseTool
from langchain_core.messages import AIMessage, HumanMessage
from langchain.agents import create_tool_calling_agent
from langchain_anthropic import ChatAnthropic
import os

from src.tools.repo import get_repository_tools
from src.models.config import Config

# System prompt for the repository analysis agent
REPO_AGENT_SYSTEM_PROMPT = """You are a Repository Analysis Assistant specialized in exploring GitHub repositories. 
Your task is to analyze GitHub repositories to understand their structure, contents, and gather code samples for further analysis.

When analyzing a repository, follow these steps:
1. First, fetch basic metadata about the repository to understand its size, activity, and primary language
2. Then, explore the repository structure to get a high-level overview of its organization
3. Finally, collect code samples that represent the repository's codebase

Be thorough and methodical in your analysis. Document what you find clearly and provide context for your observations.

For large repositories, focus on the most important parts:
- Main application code
- Core functionality
- Representative examples of the codebase
- Configuration files that might indicate technology choices

YOUR RESPONSE SHOULD BE A CONCISE SUMMARY OF YOUR FINDINGS, focused on the most relevant information for further analysis.
Include clear sections for Repository Information, Directory Structure, and Code Sample Overview.
"""

def create_repository_agent(
    llm: Optional[ChatAnthropic] = None,
    tools: Optional[List[BaseTool]] = None,
    verbose: bool = False
) -> AgentExecutor:
    """
    Create a repository analysis agent specialized in exploring GitHub repositories.
    
    Args:
        llm: Language model to use (Optional - will create one if not provided)
        tools: Tools to use (Optional - will use default repository tools if not provided)
        verbose: Whether to run the agent with verbose logging
        
    Returns:
        An AgentExecutor that can analyze repositories
    """
    # Setup LLM if not provided
    if llm is None:
        config = Config.from_file()
        anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
        
        if not anthropic_api_key:
            raise ValueError("No Anthropic API key found. Please set ANTHROPIC_API_KEY environment variable.")
            
        llm = ChatAnthropic(
            model=config.model_name,
            temperature=0.2,  # Lower temperature for more focused exploration
            anthropic_api_key=anthropic_api_key
        )
    
    # Use default repository tools if none provided
    if tools is None:
        tools = get_repository_tools()
    
    # Create prompt for the agent
    prompt = ChatPromptTemplate.from_messages([
        ("system", REPO_AGENT_SYSTEM_PROMPT),
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
        max_iterations=10,  # Limit iterations to prevent excessive API calls
        return_intermediate_steps=False
    )
    
    return agent_executor

def analyze_repository(repo_url: str, verbose: bool = False) -> Dict[str, Any]:
    """
    Analyze a GitHub repository using the repository agent.
    
    Args:
        repo_url: URL of the GitHub repository to analyze
        verbose: Whether to show verbose output
        
    Returns:
        Dictionary containing analysis results
    """
    # Create the agent
    agent = create_repository_agent(verbose=verbose)
    
    # Run the agent with the repository URL
    result = agent.invoke({
        "input": f"Analyze the GitHub repository at {repo_url}. Explore its structure, collect metadata, and gather representative code samples for further analysis.",
        "chat_history": []
    })
    
    # Extract the result from the agent's response
    return {
        "repo_url": repo_url,
        "analysis": result["output"],
        "agent_result": result
    }