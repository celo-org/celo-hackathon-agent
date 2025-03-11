"""
Coordinator agent for orchestrating the entire analysis pipeline.
"""

from typing import Dict, Any, List, Optional
from langchain.agents import AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import BaseTool
from langchain_core.messages import AIMessage, HumanMessage
from langchain.agents import create_tool_calling_agent
from langchain_anthropic import ChatAnthropic
import os
import pandas as pd

from src.tools.all_tools import get_all_tools
from src.agents.repo_agent import analyze_repository
from src.agents.code_quality_agent import analyze_code_quality
from src.agents.celo_agent import analyze_celo_integration
from src.agents.reporting_agent import generate_reports
from src.models.config import Config

# System prompt for the coordinator agent
COORDINATOR_SYSTEM_PROMPT = """You are a Project Analysis Coordinator responsible for orchestrating the evaluation of GitHub repositories for code quality and Celo blockchain integration.
Your task is to manage the entire analysis pipeline, from gathering repository information to generating final reports.

As Coordinator, you will:
1. Analyze repository structure and content
2. Evaluate code quality
3. Detect Celo blockchain integration
4. Generate comprehensive reports

For each step, use the appropriate specialized agents to perform detailed analysis. Collect their results and pass relevant information to subsequent agents.
Be methodical and thorough, ensuring each repository is fully analyzed.

YOUR RESPONSE SHOULD BE A COMPREHENSIVE SUMMARY that includes:
- Key findings from the repository analysis
- Code quality assessment highlights
- Celo integration status and details
- Confirmation of report generation
- Overall insights across all analyzed projects
"""

def create_coordinator_agent(
    llm: Optional[ChatAnthropic] = None,
    tools: Optional[List[BaseTool]] = None,
    verbose: bool = False
) -> AgentExecutor:
    """
    Create a coordinator agent that orchestrates the entire analysis pipeline.
    
    Args:
        llm: Language model to use (Optional - will create one if not provided)
        tools: Tools to use (Optional - will use all tools if not provided)
        verbose: Whether to run the agent with verbose logging
        
    Returns:
        An AgentExecutor that can coordinate the analysis
    """
    # Setup LLM if not provided
    if llm is None:
        config = Config.from_file()
        anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
        
        if not anthropic_api_key:
            raise ValueError("No Anthropic API key found. Please set ANTHROPIC_API_KEY environment variable.")
            
        llm = ChatAnthropic(
            model=config.model_name,
            temperature=0.3,  # Balanced temperature for coordination
            anthropic_api_key=anthropic_api_key
        )
    
    # Use all tools if none provided
    if tools is None:
        tools = get_all_tools()
    
    # Create prompt for the agent
    prompt = ChatPromptTemplate.from_messages([
        ("system", COORDINATOR_SYSTEM_PROMPT),
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
        max_iterations=15,  # Allow more iterations for complex coordination
        return_intermediate_steps=True  # Include intermediate steps for debugging
    )
    
    return agent_executor

class AnalysisPipeline:
    """Orchestrates the end-to-end analysis process using specialized agents."""
    
    def __init__(self, config_path: str = "config.json", output_dir: str = "reports", verbose: bool = False):
        """
        Initialize the analysis pipeline.
        
        Args:
            config_path: Path to the configuration file
            output_dir: Directory to save reports
            verbose: Whether to show verbose output
        """
        self.config_path = config_path
        self.output_dir = output_dir
        self.verbose = verbose
        self.config = Config.from_file(config_path)
        
        # Check for API key
        self.anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not self.anthropic_api_key:
            raise ValueError("No Anthropic API key found. Please set ANTHROPIC_API_KEY environment variable.")
        
        # Initialize shared LLM instance
        self.llm = ChatAnthropic(
            model=self.config.model_name,
            temperature=0.2,
            anthropic_api_key=self.anthropic_api_key
        )
    
    def analyze_single_repository(self, repo_url: str) -> Dict[str, Any]:
        """
        Analyze a single repository.
        
        Args:
            repo_url: URL of the GitHub repository to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        # 1. Analyze repository structure
        repo_analysis = analyze_repository(repo_url, self.verbose)
        
        # Extract repository metadata
        repo_owner = repo_analysis.get("agent_result", {}).get("repo_owner", "unknown")
        repo_name = repo_analysis.get("agent_result", {}).get("repo_name", "unknown")
        repo_description = repo_analysis.get("agent_result", {}).get("repo_description", "")
        
        # Extract code samples
        code_samples = repo_analysis.get("agent_result", {}).get("code_samples", [])
        if not code_samples:
            # Try to extract from intermediate steps if not in the main result
            for step in repo_analysis.get("agent_result", {}).get("intermediate_steps", []):
                if isinstance(step, tuple) and len(step) >= 2:
                    tool_result = step[1]
                    if isinstance(tool_result, dict) and "code_samples" in tool_result:
                        code_samples = tool_result.get("code_samples", [])
                        break
        
        # 2. Analyze code quality
        quality_analysis = analyze_code_quality(
            code_samples,
            repo_owner,
            repo_name,
            repo_description,
            verbose=self.verbose
        )
        
        # 3. Analyze Celo integration
        celo_analysis = analyze_celo_integration(
            repo_url,
            code_samples,
            repo_owner,
            repo_name,
            repo_description,
            verbose=self.verbose
        )
        
        # 4. Combine results
        return {
            "project_name": f"{repo_owner}/{repo_name}",
            "project_description": repo_description,
            "project_github_url": repo_url,
            "github_urls": [repo_url],
            "project_owner_github_url": [f"https://github.com/{repo_owner}"],
            "project_url": f"https://github.com/{repo_owner}/{repo_name}",
            "analysis": {
                "repo_details": repo_analysis.get("analysis", ""),
                "code_quality": quality_analysis.get("analysis", ""),
                "celo_integration": celo_analysis.get("analysis", "")
            }
        }
    
    def analyze_projects_from_excel(self, excel_path: str) -> List[Dict[str, Any]]:
        """
        Analyze multiple projects from an Excel file.
        
        Args:
            excel_path: Path to Excel file containing project data
            
        Returns:
            List of dictionaries containing analysis results
        """
        # Load projects from Excel
        try:
            df = pd.read_excel(excel_path)
            required_columns = [
                "project_name",
                "project_description",
                "project_github_url",
                "project_owner_github_url",
                "project_url",
            ]
            
            # Check if required columns exist
            for col in required_columns:
                if col not in df.columns:
                    raise ValueError(f"Missing required column: {col}")
            
            project_results = []
            
            # Process each project
            for index, row in df.iterrows():
                project_name = row["project_name"]
                project_description = row["project_description"]
                raw_github_urls = row["project_github_url"]
                
                # Process GitHub URLs
                github_urls = []
                if isinstance(raw_github_urls, str):
                    github_urls = [url.strip() for url in raw_github_urls.split(',') if url.strip()]
                elif pd.notna(raw_github_urls):
                    github_urls = [str(raw_github_urls)]
                
                # If no valid GitHub URLs, create a default result and continue
                if not github_urls:
                    project_result = {
                        "project_name": project_name,
                        "project_description": project_description,
                        "project_github_url": "No valid GitHub URL provided",
                        "github_urls": [],
                        "project_owner_github_url": [],
                        "project_url": row["project_url"],
                        "analysis": {
                            "error": "No valid GitHub URL provided",
                            "code_quality": "Not evaluated",
                            "celo_integration": "Not evaluated"
                        }
                    }
                    project_results.append(project_result)
                    continue
                
                # Process owner GitHub URLs
                owner_github_urls = []
                raw_owner_urls = row["project_owner_github_url"]
                if isinstance(raw_owner_urls, str):
                    owner_github_urls = [url.strip() for url in raw_owner_urls.split(',') if url.strip()]
                elif pd.notna(raw_owner_urls):
                    owner_github_urls = [str(raw_owner_urls)]
                
                # Initialize combined analysis results
                combined_analysis = {
                    "repo_details": [],
                    "code_quality": {"overall_score": 0, "repositories_analyzed": 0},
                    "celo_integration": {"integrated": False, "evidence": [], "repositories_with_celo": 0}
                }
                
                # Analyze each GitHub repository
                for github_url in github_urls:
                    # Skip empty URLs
                    if not github_url or not github_url.startswith('http'):
                        continue
                    
                    # Analyze this repository
                    repo_result = self.analyze_single_repository(github_url)
                    
                    # Combine results
                    if "repo_details" in repo_result["analysis"]:
                        combined_analysis["repo_details"].append(repo_result["analysis"]["repo_details"])
                    
                    # Add more combination logic here as needed
                    # This is simplified for now
                
                # Create final project result
                project_result = {
                    "project_name": project_name,
                    "project_description": project_description,
                    "project_github_url": raw_github_urls,
                    "github_urls": github_urls,
                    "project_owner_github_url": owner_github_urls,
                    "project_url": row["project_url"],
                    "analysis": combined_analysis
                }
                
                project_results.append(project_result)
            
            return project_results
            
        except Exception as e:
            raise Exception(f"Error analyzing projects from Excel: {str(e)}")
    
    def run(self, excel_path: str) -> Dict[str, Any]:
        """
        Run the complete analysis pipeline.
        
        Args:
            excel_path: Path to Excel file containing project data
            
        Returns:
            Dictionary containing overall analysis results
        """
        # Analyze projects
        project_results = self.analyze_projects_from_excel(excel_path)
        
        # Generate reports
        report_result = generate_reports(project_results, self.output_dir, self.verbose)
        
        return {
            "projects_analyzed": len(project_results),
            "output_directory": self.output_dir,
            "project_results": project_results,
            "report_summary": report_result.get("summary", "")
        }