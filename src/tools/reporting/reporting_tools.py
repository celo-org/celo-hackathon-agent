"""
Report generation tools for creating analysis reports.
"""

import os
import json
from typing import Dict, List, Any, Optional
from langchain.tools import tool, StructuredTool
from pydantic import BaseModel, Field

from src.models.types import ProjectAnalysisResult

class ProjectReportInput(BaseModel):
    """Input for project report generation."""
    project_result: Dict[str, Any] = Field(..., description="Project analysis result")
    output_dir: str = Field("reports", description="Directory to save the report")

class SummaryReportInput(BaseModel):
    """Input for summary report generation."""
    project_results: List[Dict[str, Any]] = Field(..., description="List of project analysis results")
    output_dir: str = Field("reports", description="Directory to save the report")

class ExportDataInput(BaseModel):
    """Input for data export."""
    project_results: List[Dict[str, Any]] = Field(..., description="List of project analysis results")
    output_dir: str = Field("reports", description="Directory to save the exported data")
    format: str = Field("json", description="Format for the exported data")

@tool("generate_project_report", args_schema=ProjectReportInput, return_direct=False)
def generate_project_report(project_result: Dict[str, Any], output_dir: str = "reports") -> Dict[str, Any]:
    """
    Generate a detailed Markdown report for a single project.
    
    Args:
        project_result: Project analysis result dictionary
        output_dir: Directory to save the report
        
    Returns:
        Dictionary containing report generation status and path
    """
    from src.reporting.report_generator import generate_project_report as gen_report
    
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate file name from project name
        project_name = project_result.get("project_name", "unknown")
        file_name = project_name.replace(" ", "_").lower()
        report_path = os.path.join(output_dir, f"{file_name}.md")
        
        # Generate the report
        gen_report(project_result, report_path)
        
        return {
            "success": True,
            "report_path": report_path,
            "project_name": project_name
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error generating project report: {str(e)}"
        }

@tool("create_summary_report", args_schema=SummaryReportInput, return_direct=False)
def create_summary_report(project_results: List[Dict[str, Any]], output_dir: str = "reports") -> Dict[str, Any]:
    """
    Create a summary report covering all analyzed projects.
    
    Args:
        project_results: List of project analysis results
        output_dir: Directory to save the report
        
    Returns:
        Dictionary containing summary report generation status and path
    """
    from src.reporting.report_generator import generate_summary_report as gen_summary
    
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Summary report path
        summary_path = os.path.join(output_dir, "summary.md")
        
        # Generate the summary report
        gen_summary(project_results, summary_path)
        
        return {
            "success": True,
            "report_path": summary_path,
            "projects_count": len(project_results)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error generating summary report: {str(e)}"
        }

@tool("export_analysis_data", args_schema=ExportDataInput, return_direct=False)
def export_analysis_data(
    project_results: List[Dict[str, Any]], 
    output_dir: str = "reports", 
    format: str = "json"
) -> Dict[str, Any]:
    """
    Export raw analysis data for further processing.
    
    Args:
        project_results: List of project analysis results
        output_dir: Directory to save the exported data
        format: Format for the exported data (json, csv)
        
    Returns:
        Dictionary containing export status and path
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Determine export format and file path
        if format.lower() == "json":
            export_path = os.path.join(output_dir, "results.json")
            
            # Make sure we never use template data and actually use the provided project results
            if not project_results or len(project_results) == 0:
                # If we somehow got empty results, create a placeholder structure
                empty_result = {
                    "warning": "No project analysis results were available",
                    "timestamp": None
                }
                with open(export_path, "w") as f:
                    json.dump([empty_result], f, indent=2)
            else:
                # Use the actual project data
                with open(export_path, "w") as f:
                    json.dump(project_results, f, indent=2)
                
            return {
                "success": True,
                "export_path": export_path,
                "format": "json",
                "projects_count": len(project_results)
            }
        elif format.lower() == "csv":
            # CSV export not implemented yet
            return {
                "success": False,
                "error": "CSV export not yet implemented",
                "suggestion": "Use JSON format instead"
            }
        else:
            return {
                "success": False,
                "error": f"Unsupported export format: {format}",
                "supported_formats": ["json"]
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error exporting analysis data: {str(e)}"
        }

def get_reporting_tools() -> List[StructuredTool]:
    """Get all reporting tools."""
    return [
        generate_project_report,
        create_summary_report,
        export_analysis_data
    ]