"""
Analysis schemas for the API.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, HttpUrl


class AnalysisOptions(BaseModel):
    """Schema for analysis options."""
    prompt: Optional[str] = "default"  # Use default prompt if not specified
    model: Optional[str] = None  # Use default model from settings if not specified
    temperature: Optional[float] = None  # Use default temperature from settings if not specified
    include_metrics: Optional[bool] = True
    output_format: Optional[str] = "markdown"  # markdown or json


class AnalysisCreate(BaseModel):
    """Schema for creating a new analysis task."""
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
    
    class Config:
        from_attributes = True


class AnalysisTaskList(BaseModel):
    """Schema for listing analysis tasks."""
    tasks: List[AnalysisStatus]
    total: int