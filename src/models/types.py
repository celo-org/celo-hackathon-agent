"""
Data type definitions for the Celo Hackathon Analyzer.
"""

from typing import Dict, List, Optional, TypedDict, Union


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


class CodeQualityScores(TypedDict):
    """Code quality scores type definition"""
    overall_score: float
    readability: float
    standards: float
    complexity: float
    testing: float


class CodeQualityMetrics(TypedDict):
    """Code quality metrics type definition"""
    file_count: int
    test_file_count: int
    doc_file_count: int
    code_files_analyzed: int
    code_lines: Optional[int]
    comment_lines: Optional[int]


class AIAnalysis(TypedDict):
    """AI analysis details type definition"""
    overall_analysis: str
    suggestions: List[str]
    readability_reasoning: str
    standards_reasoning: str
    complexity_reasoning: str
    testing_reasoning: str


class CodeQualityResult(TypedDict):
    """Complete code quality analysis result"""
    overall_score: float
    readability: float
    standards: float
    complexity: float
    testing: float
    ai_analysis: Optional[AIAnalysis]
    metrics: CodeQualityMetrics
    repositories_analyzed: Optional[int]
    note: Optional[str]
    error: Optional[str]


class CeloEvidence(TypedDict):
    """Evidence of Celo integration"""
    file: str
    keyword: str
    repository: Optional[str]


class CeloIntegrationResult(TypedDict):
    """Celo integration analysis result"""
    integrated: bool
    evidence: List[CeloEvidence]
    analysis: Optional[str]
    repositories_with_celo: Optional[int]
    error: Optional[str]


class RepositoryAnalysisResult(TypedDict):
    """Complete repository analysis result"""
    repo_details: RepoDetails
    code_quality: CodeQualityResult
    celo_integration: CeloIntegrationResult
    error: Optional[str]


class ProjectAnalysisResult(TypedDict):
    """Complete project analysis result"""
    project_name: str
    project_description: str
    project_github_url: str
    github_urls: List[str]
    project_owner_github_url: List[str]
    project_url: str
    analysis: Dict[str, Union[List[RepoDetails], CodeQualityResult, CeloIntegrationResult]]
    error: Optional[str]