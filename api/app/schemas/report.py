"""
Report schemas for the API.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class ReportScores(BaseModel):
    """Schema for report scores."""
    security: Optional[float] = None
    functionality: Optional[float] = None
    readability: Optional[float] = None
    dependencies: Optional[float] = None
    evidence: Optional[float] = None
    overall: Optional[float] = None


class ReportBase(BaseModel):
    """Base schema for reports."""
    report_id: str
    github_url: str
    repo_name: str
    created_at: datetime
    ipfs_hash: Optional[str] = None
    published_at: Optional[datetime] = None
    scores: Optional[ReportScores] = None


class ReportSummary(ReportBase):
    """Schema for report summary (without full content)."""
    pass


class ReportDetail(ReportBase):
    """Schema for detailed report including content."""
    content: Dict[str, Any]


class ReportList(BaseModel):
    """Schema for listing reports."""
    reports: List[ReportSummary]
    total: int


class ReportPublish(BaseModel):
    """Schema for publishing a report to IPFS."""
    report_id: str