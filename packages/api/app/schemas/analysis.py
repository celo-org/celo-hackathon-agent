"""
Analysis schemas for the API.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class AnalysisOptions(BaseModel):
    """Schema for analysis options."""

    prompt: Optional[str] = "default"  # Use default prompt if not specified
    model: Optional[str] = None  # Use default model from settings if not specified
    temperature: Optional[float] = None  # Use default temperature from settings if not specified
    include_metrics: Optional[bool] = True
    output_format: Optional[str] = "markdown"  # markdown or json
    analysis_type: Optional[str] = "fast"  # fast or deep


class AnalysisCreate(BaseModel):
    """Schema for creating a new analysis task."""

    github_urls: List[str] = Field(..., min_items=1)
    options: Optional[AnalysisOptions] = None


# Add missing schemas that the router expects
class AnalysisSubmissionRequest(BaseModel):
    """Schema for analysis submission request."""

    github_urls: List[str] = Field(..., min_items=1)
    options: Optional[AnalysisOptions] = None


class AnalysisStatus(BaseModel):
    """Schema for analysis task status."""

    task_id: str
    status: str
    github_url: str
    progress: int
    submitted_at: datetime
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None
    analysis_type: Optional[str] = "fast"  # fast or deep analysis type

    class Config:
        from_attributes = True


# Add missing response schemas
class AnalysisSubmissionResponse(AnalysisStatus):
    """Schema for analysis submission response."""

    pass


class AnalysisTaskResponse(AnalysisStatus):
    """Schema for single analysis task response."""

    pass


class AnalysisTaskList(BaseModel):
    """Schema for listing analysis tasks."""

    tasks: List[AnalysisStatus]
    total: int

    class Config:
        from_attributes = True


class AnalysisTaskListResponse(AnalysisTaskList):
    """Schema for analysis task list response."""

    pass
