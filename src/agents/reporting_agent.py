"""
Reporting agent for generating analysis reports.
"""

from typing import Dict, Any, List, Optional
from langchain.agents import AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import BaseTool
from langchain_core.messages import AIMessage, HumanMessage
from langchain.agents import create_tool_calling_agent
from langchain_anthropic import ChatAnthropic
import os

from src.tools.reporting import get_reporting_tools
from src.models.config import Config

# System prompt for the reporting agent
REPORTING_AGENT_SYSTEM_PROMPT = """You are a Reporting Assistant specialized in creating clear, comprehensive reports from repository analysis data.
Your task is to transform technical analysis results into well-structured, readable reports that highlight key findings.

When creating reports, follow these guidelines:
1. Organize information logically with clear sections and headings
2. Highlight the most important findings first
3. Include relevant evidence and examples
4. Use visual elements like bullet points and numbered lists for readability
5. Provide context for technical details to make them understandable
6. Ensure all assertions are supported by evidence from the analysis

YOUR RESPONSE SHOULD BE A CONFIRMATION OF REPORT GENERATION that includes:
- A summary of what reports were created
- Key insights highlighted from the analysis
- Any issues encountered during report generation
- Recommendations for further analysis if applicable
"""

def create_reporting_agent(
    llm: Optional[ChatAnthropic] = None,
    tools: Optional[List[BaseTool]] = None,
    verbose: bool = False
) -> AgentExecutor:
    """
    Create a reporting agent specialized in generating analysis reports.
    
    Args:
        llm: Language model to use (Optional - will create one if not provided)
        tools: Tools to use (Optional - will use default reporting tools if not provided)
        verbose: Whether to run the agent with verbose logging
        
    Returns:
        An AgentExecutor that can generate reports
    """
    # Setup LLM if not provided
    if llm is None:
        config = Config.from_file()
        anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
        
        if not anthropic_api_key:
            raise ValueError("No Anthropic API key found. Please set ANTHROPIC_API_KEY environment variable.")
            
        llm = ChatAnthropic(
            model=config.model_name,
            temperature=0.3,  # Slightly higher temperature for creative report generation
            anthropic_api_key=anthropic_api_key
        )
    
    # Use default reporting tools if none provided
    if tools is None:
        tools = get_reporting_tools()
    
    # Create prompt for the agent
    prompt = ChatPromptTemplate.from_messages([
        ("system", REPORTING_AGENT_SYSTEM_PROMPT),
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
        max_iterations=5,  # Limit iterations as report generation is straightforward
        return_intermediate_steps=False
    )
    
    return agent_executor

def generate_reports(
    project_results: List[Dict[str, Any]], 
    output_dir: str = "reports",
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Generate reports for analyzed projects.
    
    Args:
        project_results: List of project analysis results
        output_dir: Directory to save the reports
        verbose: Whether to show verbose output
        
    Returns:
        Dictionary containing report generation results
    """
    # Create the agent
    agent = create_reporting_agent(verbose=verbose)
    
    # Build input message
    input_message = f"""Generate comprehensive reports for {len(project_results)} analyzed projects.

The reports should be saved in the '{output_dir}' directory. For each project, generate a detailed Markdown report 
that includes code quality assessment and Celo integration findings. Also create a summary report that provides an overview 
of all projects.

Follow these steps:
1. First, create a summary report with the create_summary_report tool
2. Then, generate individual project reports with the generate_project_report tool
3. Finally, export the raw data as JSON with the export_analysis_data tool

Make sure the reports are well-structured with clear sections, and highlight the key findings from each analysis."""
    
    # Run the agent
    result = agent.invoke({
        "input": input_message,
        "chat_history": [],
        "project_results": project_results,
        "output_dir": output_dir
    })
    
    # Extract the result from the agent's response
    return {
        "report_generation": "completed",
        "output_dir": output_dir,
        "project_count": len(project_results),
        "summary": result["output"],
        "agent_result": result
    }