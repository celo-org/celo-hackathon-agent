"""Report service for the API."""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.config import settings
from app.db.models import Report, User
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
        self, 
        user_id: str, 
        limit: int = 10, 
        offset: int = 0
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
            report_id: Report ID
            user_id: User ID
            
        Returns:
            Optional[Report]: Report or None if not found
        """
        query = (
            select(Report)
            .where(Report.id == report_id, Report.user_id == user_id)
        )
        
        result = await self.db.execute(query)
        return result.scalars().first()
    
    async def generate_report_content(
        self, 
        report: Report, 
        format: str = "md"
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
        
        if not isinstance(content, dict):
            return f"# Analysis Report for {report.repo_name}\n\nError: Invalid report format"
            
        # Build markdown report
        md_content = []
        
        # Title
        md_content.append(f"# Analysis Report: {report.repo_name}")
        md_content.append(f"*Generated on: {report.created_at.strftime('%Y-%m-%d %H:%M UTC')}*\n")
        
        # Summary
        if "summary" in content:
            md_content.append("## Summary")
            
            if isinstance(content["summary"], dict):
                md_content.append(content["summary"].get("text", "No summary provided."))
            elif isinstance(content["summary"], str):
                md_content.append(content["summary"])
            
            md_content.append("")
        
        # Scores
        if report.scores:
            md_content.append("## Scores")
            md_content.append("| Category | Score |")
            md_content.append("| --- | --- |")
            
            for category, score in report.scores.items():
                md_content.append(f"| {category.title()} | {score} |")
                
            md_content.append("")
        
        # Add other sections
        sections = [
            "readability", "standards", "complexity", "testing", "security",
            "strengths", "weaknesses", "recommendations"
        ]
        
        for section in sections:
            if section in content:
                md_content.append(f"## {section.title()}")
                
                section_content = content[section]
                if isinstance(section_content, dict):
                    # Handle structured section
                    if "description" in section_content:
                        md_content.append(section_content["description"])
                    
                    if "details" in section_content and isinstance(section_content["details"], list):
                        for item in section_content["details"]:
                            md_content.append(f"- {item}")
                    
                    if "recommendations" in section_content and isinstance(section_content["recommendations"], list):
                        md_content.append("\n### Recommendations")
                        for item in section_content["recommendations"]:
                            md_content.append(f"- {item}")
                
                elif isinstance(section_content, list):
                    # Handle list section
                    for item in section_content:
                        if isinstance(item, str):
                            md_content.append(f"- {item}")
                        elif isinstance(item, dict) and "text" in item:
                            md_content.append(f"- {item['text']}")
                
                elif isinstance(section_content, str):
                    # Handle string section
                    md_content.append(section_content)
                
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
        
        logger.info(f"Published report to IPFS: {report.id} with hash: {ipfs_hash}")
        
        return ipfs_hash

# Dependency
async def get_report_service(db: AsyncSession = Depends(get_db_session)):
    """Get report service instance."""
    return ReportService(db)