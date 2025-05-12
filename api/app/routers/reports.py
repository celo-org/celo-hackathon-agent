"""
Reports router for the API.
"""

import io
import logging
import zipfile
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status, Response, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel

from app.config import settings
from app.db.session import get_db_session
from app.db.models import User, Report
from app.routers.auth import get_current_user
from app.schemas.report import ReportSummary, ReportDetail, ReportList
from app.services.report import ReportService, get_report_service

logger = logging.getLogger(__name__)

router = APIRouter()


class BatchDownloadRequest(BaseModel):
    """Request body for batch downloading reports."""

    task_ids: List[str]


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
    total_query = select(Report).where(Report.user_id == current_user.id)
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


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    task_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    report_service: ReportService = Depends(get_report_service),
):
    """
    Delete a report.

    Args:
        task_id: Task ID (same as report ID)
        current_user: Current authenticated user
        report_service: Report service

    Returns:
        None: Returns 204 No Content on success
    """
    # Delete report
    success = await report_service.delete_report(
        report_id=task_id,
        user_id=str(current_user.id),
    )

    # Check if report exists and was deleted
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    # Return no content
    return None


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


@router.post("/download-batch")
async def download_reports_batch(
    batch_request: BatchDownloadRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    report_service: ReportService = Depends(get_report_service),
    format: str = "md",
):
    """
    Download multiple reports as a ZIP file.

    Args:
        batch_request: List of task IDs to download
        current_user: Current authenticated user
        report_service: Report service
        format: Output format for reports (md or json)

    Returns:
        Response: ZIP file download containing all requested reports
    """
    if not batch_request.task_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No task IDs provided",
        )

    # Limit the number of reports to download at once
    if len(batch_request.task_ids) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Too many reports requested. Maximum is 50.",
        )

    # Create ZIP file in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # Process each report
        for task_id in batch_request.task_ids:
            try:
                # Get report
                report = await report_service.get_report(
                    report_id=task_id,
                    user_id=str(current_user.id),
                )

                if not report:
                    logger.warning(f"Report {task_id} not found, skipping")
                    continue

                # Generate report content
                content, filename, _ = await report_service.generate_report_content(
                    report=report,
                    format=format,
                )

                # Add to ZIP
                zip_file.writestr(filename, content)

            except Exception as e:
                logger.error(f"Error processing report {task_id}: {str(e)}")
                # Continue with other reports even if one fails
                continue

    # Get ZIP data
    zip_buffer.seek(0)
    zip_data = zip_buffer.read()

    # Check if we added any files
    if len(zip_data) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No valid reports found for the requested IDs",
        )

    # Return ZIP file
    timestamp = str(current_user.id).split("-")[
        0
    ]  # Use part of user ID as unique identifier
    return Response(
        content=zip_data,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=reports-{timestamp}.zip"
        },
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
