"""
Data type definitions for the Celo Hackathon Analyzer.
"""

from typing import Dict, List, Optional, TypedDict, Union, Any


class ContributorDetails(TypedDict):
    """Contributor details type definition"""
    login: str
    profile_url: str
    contributions: int
    avatar_url: Optional[str]


class CommitStats(TypedDict):
    """Repository commit statistics"""
    total_commits: int
    first_commit_date: str
    latest_commit_date: str
    commit_frequency: float  # average commits per week
    commit_history: Optional[Dict[str, int]]  # monthly commit counts


class RepoDetails(TypedDict):
    """Repository details type definition"""
    name: str
    description: str
    url: str
    stars: int
    forks: int
    open_issues: int
    last_update: str
    language: str
    contributors: Optional[List[ContributorDetails]]
    total_contributors: Optional[int]
    commit_stats: Optional[CommitStats]
    main_languages: Optional[Dict[str, float]]  # language percentages
    license_type: Optional[str]
    created_at: Optional[str]  # repository creation date
    size_kb: Optional[int]  # repository size in KB
    repo_type: Optional[str]  # type of repository (web app, smart contract, etc.)


class CodeExample(TypedDict):
    """Code example for findings illustration"""
    file: str
    snippet: str
    explanation: str


class ConfidenceLevel(TypedDict):
    """Confidence level for analysis sections"""
    level: str  # high, medium, low
    reasoning: str


class RepositoryAnalysisResult(TypedDict):
    """Complete repository analysis result"""
    repo_details: RepoDetails
    code_quality: Dict[str, Any]  # Overall code quality assessment
    celo_integration: Dict[str, Any]  # Celo integration details
    architecture: Dict[str, Any]  # Architecture evaluation
    findings: Dict[str, Any]  # Key findings
    recommendations: List[str]  # Improvement recommendations
    code_examples: List[CodeExample]  # Illustrative code examples
    confidence_levels: Dict[str, ConfidenceLevel]  # Confidence in different areas
    token_metrics: Optional[Dict[str, int]]  # Token usage metrics
    error: Optional[str]


class ProjectAnalysisResult(TypedDict):
    """Complete project analysis result"""
    project_name: str
    project_description: str
    project_github_url: str
    github_urls: List[str]
    project_owner_github_url: List[str]
    project_url: str
    analysis: Dict[str, Any]  # Combined analysis results
    error: Optional[str]