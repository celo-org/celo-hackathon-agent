"""
File parsing utilities for the AI Project Analyzer.
"""

import os
import re
import logging
from typing import List

import pandas as pd


def parse_input_file(file_path: str) -> List[str]:
    """
    Parse an Excel or CSV file to extract GitHub repository URLs.

    Args:
        file_path: Path to the Excel or CSV file containing GitHub URLs.

    Returns:
        List of GitHub repository URLs.

    Raises:
        ValueError: If the file type is not supported or no GitHub URLs are found.
        FileNotFoundError: If the file does not exist.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # Determine file type from extension
    file_ext = os.path.splitext(file_path)[1].lower()

    try:
        # Load the file based on extension
        if file_ext == ".csv":
            df = pd.read_csv(file_path)
        elif file_ext in [".xlsx", ".xls"]:
            df = pd.read_excel(file_path)
        else:
            raise ValueError(
                f"Unsupported file type: {file_ext}. Please provide a CSV or Excel file."
            )

        # Find columns that might contain GitHub URLs
        github_columns = find_github_columns(df)

        if not github_columns:
            raise ValueError(
                "No GitHub URL columns found in the file. "
                "Please ensure your file has a column with 'github' or 'Github' in the name."
            )

        # Extract URLs from the identified columns
        urls = extract_github_urls(df, github_columns)

        if not urls:
            raise ValueError("No valid GitHub repository URLs found in the file.")

        return urls

    except Exception as e:
        logging.error(f"Error parsing file {file_path}: {str(e)}")
        raise


def find_github_columns(df: pd.DataFrame) -> List[str]:
    """
    Find columns in the DataFrame that might contain GitHub URLs.

    Args:
        df: DataFrame to search for GitHub URL columns.

    Returns:
        List of column names that might contain GitHub URLs.
    """
    github_columns = []

    for col in df.columns:
        # Check if column name contains 'github' or 'Github' or 'Github URL'
        if re.search(r"(?i)github|github url", str(col)):
            github_columns.append(col)

    return github_columns


def extract_github_urls(df: pd.DataFrame, columns: List[str]) -> List[str]:
    """
    Extract GitHub repository URLs from specified columns in a DataFrame.

    Args:
        df: DataFrame containing the data.
        columns: List of column names to extract GitHub URLs from.

    Returns:
        List of valid GitHub repository URLs.
    """
    github_urls = []
    github_pattern = re.compile(r"https?://(?:www\.)?github\.com/[\w.-]+/[\w.-]+/?")

    for col in columns:
        for value in df[col].dropna():
            value = str(value).strip()
            if match := github_pattern.search(value):
                url = match.group(0)
                # Ensure URL doesn't end with unwanted characters
                if url.endswith(")") and "(" not in url:
                    url = url[:-1]
                # Normalize URLs to not have trailing slash
                if url.endswith("/"):
                    url = url[:-1]
                # Add to list if not already present
                if url not in github_urls:
                    github_urls.append(url)

    return github_urls


def validate_github_url(url: str) -> bool:
    """
    Validate if a URL is a proper GitHub repository URL.

    Args:
        url: URL to validate.

    Returns:
        True if the URL is a valid GitHub repository URL, False otherwise.
    """
    github_repo_pattern = re.compile(r"^https?://(?:www\.)?github\.com/[\w.-]+/[\w.-]+/?$")
    return bool(github_repo_pattern.match(url))
