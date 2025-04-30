"""
Reports router for the API.
"""

import logging
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from api.app.config import settings
from api.app.db.session import get_db_session
from api.app.db.models import User, Report
from api.app.routers.auth import get_current_user
from api.app.schemas.report import ReportSummary, ReportDetail, ReportList, ReportPublish

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=ReportList)
async def get_reports(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db_session),
    limit: int = 10,
    offset: int = 0,
):
    """
    Get all reports for the current user.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        limit: Maximum number of reports to return
        offset: Number of reports to skip
        
    Returns:
        ReportList: List of reports
    """
    # Query reports for the current user
    query = (
        select(Report)
        .where(Report.user_id == current_user.id)
        .order_by(Report.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    
    result = await db.execute(query)
    reports = result.scalars().all()
    
    # Get total report count
    total_query = (
        select(Report)
        .where(Report.user_id == current_user.id)
    )
    total_result = await db.execute(total_query)
    total = len(total_result.scalars().all())
    
    # Convert to response schema
    report_summaries = []
    for report in reports:
        report_summary = ReportSummary(
            report_id=report.id,
            github_url=report.github_url,
            repo_name=report.repo_name,
            created_at=report.created_at,
            ipfs_hash=report.ipfs_hash,
            published_at=report.published_at,
            scores=report.scores,
        )
        report_summaries.append(report_summary)
    
    return {"reports": report_summaries, "total": total}


@router.get("/{report_id}", response_model=ReportDetail)
async def get_report(
    report_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db_session),
):
    """
    Get a specific report.
    
    Args:
        report_id: Report ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        ReportDetail: Detailed report
    """
    # Query the report
    query = (
        select(Report)
        .where(Report.id == report_id, Report.user_id == current_user.id)
    )
    
    result = await db.execute(query)
    report = result.scalars().first()
    
    # Check if report exists
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
    
    # Convert to response schema
    return ReportDetail(
        report_id=report.id,
        github_url=report.github_url,
        repo_name=report.repo_name,
        created_at=report.created_at,
        ipfs_hash=report.ipfs_hash,
        published_at=report.published_at,
        scores=report.scores,
        content=report.content,
    )


@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db_session),
    format: str = "md",
):
    """
    Download a report as Markdown or JSON.
    
    Args:
        report_id: Report ID
        current_user: Current authenticated user
        db: Database session
        format: Output format (md or json)
        
    Returns:
        Response: File download
    """
    # Query the report
    query = (
        select(Report)
        .where(Report.id == report_id, Report.user_id == current_user.id)
    )
    
    result = await db.execute(query)
    report = result.scalars().first()
    
    # Check if report exists
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
    
    # In Phase 1, we'll return a placeholder response
    # In Phase 2, we'll implement actual report conversion and download
    
    content = "# Analysis Report (Placeholder)\n\nThis is a placeholder report content."
    content_type = "text/markdown"
    filename = f"{report.repo_name.replace('/', '_')}_analysis.md"
    
    if format.lower() == "json":
        import json
        content = json.dumps({"message": "Placeholder JSON report"}, indent=2)
        content_type = "application/json"
        filename = f"{report.repo_name.replace('/', '_')}_analysis.json"
    
    return Response(
        content=content,
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/{report_id}/publish", response_model=ReportSummary)
async def publish_report(
    report_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db_session),
):
    """
    Publish a report to IPFS.
    
    Args:
        report_id: Report ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        ReportSummary: Published report summary
    """
    # Query the report
    query = (
        select(Report)
        .where(Report.id == report_id, Report.user_id == current_user.id)
    )
    
    result = await db.execute(query)
    report = result.scalars().first()
    
    # Check if report exists
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
    
    # Check if report has already been published
    if report.ipfs_hash:
        return ReportSummary(
            report_id=report.id,
            github_url=report.github_url,
            repo_name=report.repo_name,
            created_at=report.created_at,
            ipfs_hash=report.ipfs_hash,
            published_at=report.published_at,
            scores=report.scores,
        )
    
    # In Phase 1, we'll set a placeholder IPFS hash
    # In Phase 2, we'll implement actual IPFS publishing
    
    from datetime import datetime
    
    # Set placeholder IPFS hash
    report.ipfs_hash = "QmPlaceholderHashForPhase1Implementation"
    report.published_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(report)
    
    logger.info(f"Published report to IPFS: {report.id}")
    
    return ReportSummary(
        report_id=report.id,
        github_url=report.github_url,
        repo_name=report.repo_name,
        created_at=report.created_at,
        ipfs_hash=report.ipfs_hash,
        published_at=report.published_at,
        scores=report.scores,
    )