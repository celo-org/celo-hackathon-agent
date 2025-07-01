"""Report service for the API."""

import json
import logging
from datetime import datetime
from typing import List, Optional, Tuple

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.models import Report
from app.db.session import get_db_session

logger = logging.getLogger(__name__)


class ReportService:
    """Service for managing reports."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the report service.

        Args:
            db: Database session
        """
        self.db = db

    async def get_user_reports(
        self, user_id: str, limit: int = 10, offset: int = 0
    ) -> List[Report]:
        """
        Get all reports for a user.

        Args:
            user_id: User ID
            limit: Maximum number of reports to return
            offset: Number of reports to skip

        Returns:
            List[Report]: List of reports
        """
        query = (
            select(Report)
            .where(Report.user_id == user_id)
            .order_by(Report.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_report(self, report_id: str, user_id: str) -> Optional[Report]:
        """
        Get a specific report.

        Args:
            report_id: Report ID (same as task_id)
            user_id: User ID

        Returns:
            Optional[Report]: Report or None if not found
        """
        query = select(Report).where(Report.id == report_id, Report.user_id == user_id)

        result = await self.db.execute(query)
        return result.scalars().first()

    async def delete_report(self, report_id: str, user_id: str) -> bool:
        """
        Delete a report.

        Args:
            report_id: Report ID (same as task_id)
            user_id: User ID

        Returns:
            bool: True if report was deleted, False otherwise
        """
        # Get the report
        report = await self.get_report(report_id, user_id)
        if not report:
            return False

        # Delete the report
        await self.db.delete(report)
        await self.db.commit()

        return True

    async def generate_report_content(
        self, report: Report, format: str = "md"
    ) -> Tuple[str, str, str]:
        """
        Generate report content in the specified format.

        Args:
            report: Report object
            format: Output format (md or json)

        Returns:
            tuple: (content, filename, content_type)
        """
        if format.lower() == "json":
            # JSON format
            content = json.dumps(report.content, indent=2)
            filename = f"{report.repo_name.replace('/', '_')}_analysis.json"
            content_type = "application/json"
        else:
            # Markdown format
            content = self._convert_to_markdown(report)
            filename = f"{report.repo_name.replace('/', '_')}_analysis.md"
            content_type = "text/markdown"

        return content, filename, content_type

    def _convert_to_markdown(self, report: Report) -> str:
        """
        Convert report content to Markdown format.

        Args:
            report: Report object

        Returns:
            str: Markdown content
        """
        content = report.content

        # Return markdown directly if available
        if isinstance(content, dict) and "markdown" in content:
            return content["markdown"]

        # Legacy support for raw_markdown key
        if isinstance(content, dict) and "raw_markdown" in content:
            return content["raw_markdown"]

        if not isinstance(content, dict):
            return f"# Analysis Report for {report.repo_name}\n\nError: Invalid report format"

        # Check for error
        if "error" in content:
            error_message = content.get("error", "Unknown error")
            return f"# Analysis Report for {report.repo_name}\n\nError: {error_message}\n\nPlease try running the analysis again."

        # If we get here, we have a legacy JSON report structure - convert it to markdown

        # Build markdown report
        md_content = []

        # Title
        md_content.append(f"# Analysis Report: {report.repo_name}")
        md_content.append(f"*Generated on: {report.created_at.strftime('%Y-%m-%d %H:%M UTC')}*\n")

        # Scores
        if report.scores:
            md_content.append("## Scores")
            md_content.append("| Category | Score |")
            md_content.append("| --- | --- |")

            for category, score in report.scores.items():
                md_content.append(f"| {category.title()} | {score} |")

            md_content.append("")

        # Summary (if available in the JSON)
        if "summary" in content:
            md_content.append("## Summary")

            if isinstance(content["summary"], dict):
                md_content.append(content["summary"].get("text", "No summary provided."))
            elif isinstance(content["summary"], str):
                md_content.append(content["summary"])

            md_content.append("")

        # Try to extract all top-level fields from the JSON
        for key, value in content.items():
            # Skip keys we've already processed
            if key in ["summary"]:
                continue

            # Add a section for each key
            md_content.append(f"## {key.title()}")

            if isinstance(value, dict):
                # Extract text or description field
                if "text" in value:
                    md_content.append(value["text"])
                elif "description" in value:
                    md_content.append(value["description"])

                # Extract score
                if "score" in value:
                    md_content.append(f"\nScore: {value['score']}/10")

                # Extract lists
                for list_key in ["details", "recommendations", "items"]:
                    if list_key in value and isinstance(value[list_key], list):
                        md_content.append(f"\n### {list_key.title()}")
                        for item in value[list_key]:
                            if isinstance(item, str):
                                md_content.append(f"- {item}")
                            elif isinstance(item, dict) and "text" in item:
                                md_content.append(f"- {item['text']}")

            elif isinstance(value, list):
                # Handle list values
                for item in value:
                    if isinstance(item, str):
                        md_content.append(f"- {item}")
                    elif isinstance(item, dict) and "text" in item:
                        md_content.append(f"- {item['text']}")

            elif isinstance(value, str):
                # Handle string values
                md_content.append(value)

            md_content.append("")

        # Join all sections
        return "\n".join(md_content)

    async def publish_to_ipfs(self, report: Report) -> Optional[str]:
        """
        Publish a report to IPFS.

        Args:
            report: Report object

        Returns:
            Optional[str]: IPFS hash or None if failed
        """
        from app.services.ipfs import get_ipfs_service

        # Get IPFS service
        ipfs_service = await get_ipfs_service()

        # Prepare metadata
        metadata = {
            "report_id": str(report.id),
            "github_url": report.github_url,
            "repo_name": report.repo_name,
            "user_id": str(report.user_id),
            "created_at": report.created_at.isoformat(),
            "published_at": datetime.utcnow().isoformat(),
        }

        # Publish to IPFS
        ipfs_hash = await ipfs_service.publish_to_ipfs(report.content, metadata)

        if not ipfs_hash:
            logger.error(f"Failed to publish report to IPFS: {report.id}")
            return None

        # Update report
        report.ipfs_hash = ipfs_hash
        report.published_at = datetime.utcnow()

        # Save changes
        await self.db.commit()
        await self.db.refresh(report)

        return ipfs_hash


# Dependency
async def get_report_service(db: AsyncSession = Depends(get_db_session)):
    """Get report service instance."""
    return ReportService(db)
