"""
Report schemas for the API.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class ReportScores(BaseModel):
    """Schema for report scores."""
    security: Optional[float] = None
    readability: Optional[float] = None
    standards: Optional[float] = None
    complexity: Optional[float] = None
    testing: Optional[float] = None
    overall: Optional[float] = None
    
    class Config:
        from_attributes = True


class ReportBase(BaseModel):
    """Base schema for reports."""
    task_id: str  # Using task_id instead of report_id for consistency with analysis tasks
    github_url: str
    repo_name: str
    created_at: datetime
    ipfs_hash: Optional[str] = None
    published_at: Optional[datetime] = None
    scores: Optional[Dict[str, float]] = None
    
    class Config:
        from_attributes = True


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
    
    class Config:
        from_attributes = True


class ReportPublish(BaseModel):
    """Schema for publishing a report to IPFS."""
    task_id: str
    
    class Config:
        from_attributes = True