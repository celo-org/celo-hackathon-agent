"""
Code quality analysis agent for evaluating repository code.
"""

from typing import Dict, Any, List, Optional
from langchain.agents import AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import BaseTool
from langchain_core.messages import AIMessage, HumanMessage
from langchain.agents import create_tool_calling_agent
from langchain_anthropic import ChatAnthropic
import os

from src.tools.code_quality import get_code_quality_tools
from src.models.config import Config

# System prompt for the code quality analysis agent
CODE_QUALITY_AGENT_SYSTEM_PROMPT = """You are a Code Quality Analysis Assistant specialized in evaluating code quality in GitHub repositories.
Your task is to analyze code samples to assess their quality, readability, adherence to best practices, and other quality metrics.

When evaluating code quality, focus on these key aspects:
1. Readability and Documentation: How well the code is documented and how easy it is to understand
2. Coding Standards and Best Practices: Adherence to language-specific conventions and patterns
3. Algorithm Complexity and Efficiency: Whether the code is efficient and well-optimized
4. Testing and Coverage: The presence and quality of tests

Be objective and constructive in your assessment. Provide specific examples from the code to support your evaluation.

YOUR RESPONSE SHOULD BE A DETAILED QUALITY ASSESSMENT that includes:
- An overall quality score and summary
- Scores for key metrics (readability, standards, complexity, testing)
- Specific strengths identified in the code
- Areas for potential improvement
- Actionable recommendations for enhancing code quality
"""

def create_code_quality_agent(
    llm: Optional[ChatAnthropic] = None,
    tools: Optional[List[BaseTool]] = None,
    verbose: bool = False
) -> AgentExecutor:
    """
    Create a code quality analysis agent specialized in evaluating code.
    
    Args:
        llm: Language model to use (Optional - will create one if not provided)
        tools: Tools to use (Optional - will use default code quality tools if not provided)
        verbose: Whether to run the agent with verbose logging
        
    Returns:
        An AgentExecutor that can analyze code quality
    """
    # Setup LLM if not provided
    if llm is None:
        config = Config.from_file()
        anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
        
        if not anthropic_api_key:
            raise ValueError("No Anthropic API key found. Please set ANTHROPIC_API_KEY environment variable.")
            
        llm = ChatAnthropic(
            model=config.model_name,
            temperature=0.2,  # Lower temperature for more objective analysis
            anthropic_api_key=anthropic_api_key
        )
    
    # Use default code quality tools if none provided
    if tools is None:
        tools = get_code_quality_tools()
    
    # Create prompt for the agent
    prompt = ChatPromptTemplate.from_messages([
        ("system", CODE_QUALITY_AGENT_SYSTEM_PROMPT),
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
        max_iterations=5,  # Limit iterations as code quality analysis should be straightforward
        return_intermediate_steps=False
    )
    
    return agent_executor

def analyze_code_quality(
    code_samples: List[str], 
    repo_owner: str, 
    repo_name: str, 
    repo_description: str = "",
    file_metrics: Optional[Dict[str, int]] = None,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Analyze code quality of provided code samples.
    
    Args:
        code_samples: List of code samples to analyze
        repo_owner: Owner of the repository
        repo_name: Name of the repository
        repo_description: Description of the repository
        file_metrics: Optional metrics about the files in the repository
        verbose: Whether to show verbose output
        
    Returns:
        Dictionary containing code quality analysis results
    """
    # Create the agent
    agent = create_code_quality_agent(verbose=verbose)
    
    # Build input message
    input_message = f"""Analyze the code quality of the GitHub repository {repo_owner}/{repo_name}.

Repository Description: {repo_description}

I have {len(code_samples)} code samples from this repository. Please evaluate their quality, focusing on readability, 
coding standards, algorithm complexity, and testing. Provide an overall assessment and suggestions for improvement.

Use the analyze_code_quality tool to perform a comprehensive analysis with these code samples."""
    
    # If file metrics are provided, add them to the input
    if file_metrics:
        metrics_str = ", ".join([f"{k}: {v}" for k, v in file_metrics.items()])
        input_message += f"\n\nThe repository contains the following files: {metrics_str}"
    
    # Run the agent with the code samples and repo info
    result = agent.invoke({
        "input": input_message,
        "chat_history": [],
        "code_samples": code_samples,
        "repo_owner": repo_owner,
        "repo_name": repo_name,
        "repo_description": repo_description,
        "file_metrics": file_metrics
    })
    
    # Extract the result from the agent's response
    return {
        "repo_owner": repo_owner,
        "repo_name": repo_name,
        "analysis": result["output"],
        "agent_result": result
    }