"""
Reports router for the API.
"""

import logging
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.config import settings
from app.db.session import get_db_session
from app.db.models import User, Report
from app.routers.auth import get_current_user
from app.schemas.report import ReportSummary, ReportDetail, ReportList
from app.services.report import ReportService, get_report_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=ReportList)
async def get_reports(
    current_user: Annotated[User, Depends(get_current_user)],
    report_service: ReportService = Depends(get_report_service),
    limit: int = 10,
    offset: int = 0,
):
    """
    Get all reports for the current user.
    
    Args:
        current_user: Current authenticated user
        report_service: Report service
        limit: Maximum number of reports to return
        offset: Number of reports to skip
        
    Returns:
        ReportList: List of reports
    """
    # Get reports
    reports = await report_service.get_user_reports(
        user_id=str(current_user.id),
        limit=limit,
        offset=offset,
    )
    
    # Count total reports using the report service's db session
    total_query = (
        select(Report)
        .where(Report.user_id == current_user.id)
    )
    total_result = await report_service.db.execute(total_query)
    total = len(total_result.scalars().all())
    
    # Convert to response schema
    report_summaries = []
    for report in reports:
        # Ensure scores is not None
        scores = report.scores if report.scores is not None else {"overall": 0}
        
        report_summary = ReportSummary(
            task_id=str(report.id),  # Now using task_id instead of report_id
            github_url=report.github_url,
            repo_name=report.repo_name,
            created_at=report.created_at,
            ipfs_hash=report.ipfs_hash,
            published_at=report.published_at,
            scores=scores,
        )
        report_summaries.append(report_summary)
    
    return {"reports": report_summaries, "total": total}


@router.get("/{task_id}", response_model=ReportDetail)
async def get_report(
    task_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    report_service: ReportService = Depends(get_report_service),
):
    """
    Get a specific report.
    
    Args:
        task_id: Task ID (same as report ID)
        current_user: Current authenticated user
        report_service: Report service
        
    Returns:
        ReportDetail: Detailed report
    """
    # Get report
    report = await report_service.get_report(
        report_id=task_id,
        user_id=str(current_user.id),
    )
    
    # Check if report exists
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
    
    # Convert to response schema
    # Ensure scores is not None
    scores = report.scores if report.scores is not None else {"overall": 0}
    
    return ReportDetail(
        task_id=str(report.id),  # Now using task_id instead of report_id
        github_url=report.github_url,
        repo_name=report.repo_name,
        created_at=report.created_at,
        ipfs_hash=report.ipfs_hash,
        published_at=report.published_at,
        scores=scores,
        content=report.content,
    )


@router.get("/{task_id}/download")
async def download_report(
    task_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    report_service: ReportService = Depends(get_report_service),
    format: str = "md",
):
    """
    Download a report as Markdown or JSON.
    
    Args:
        task_id: Task ID (same as report ID)
        current_user: Current authenticated user
        report_service: Report service
        format: Output format (md or json)
        
    Returns:
        Response: File download
    """
    # Get report
    report = await report_service.get_report(
        report_id=task_id,
        user_id=str(current_user.id),
    )
    
    # Check if report exists
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
    
    # Generate report content
    content, filename, content_type = await report_service.generate_report_content(
        report=report,
        format=format,
    )
    
    return Response(
        content=content,
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/{task_id}/publish", response_model=ReportSummary)
async def publish_report(
    task_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    report_service: ReportService = Depends(get_report_service),
):
    """
    Publish a report to IPFS.
    
    Args:
        task_id: Task ID (same as report ID)
        current_user: Current authenticated user
        report_service: Report service
        
    Returns:
        ReportSummary: Published report summary
    """
    # Get report
    report = await report_service.get_report(
        report_id=task_id,
        user_id=str(current_user.id),
    )
    
    # Check if report exists
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
    
    # Check if report has already been published
    if report.ipfs_hash:
        # Ensure scores is not None
        scores = report.scores if report.scores is not None else {"overall": 0}
        
        return ReportSummary(
            task_id=str(report.id),  # Now using task_id instead of report_id
            github_url=report.github_url,
            repo_name=report.repo_name,
            created_at=report.created_at,
            ipfs_hash=report.ipfs_hash,
            published_at=report.published_at,
            scores=scores,
        )
    
    # Publish to IPFS
    await report_service.publish_to_ipfs(report)
    
    # Ensure scores is not None
    scores = report.scores if report.scores is not None else {"overall": 0}
    
    return ReportSummary(
        task_id=str(report.id),  # Now using task_id instead of report_id
        github_url=report.github_url,
        repo_name=report.repo_name,
        created_at=report.created_at,
        ipfs_hash=report.ipfs_hash,
        published_at=report.published_at,
        scores=scores,
    )