"""
CLI module for the AI Project Analyzer.

This module provides the Typer CLI interface.
"""

import logging
import os

# Import from core package
import sys
import time
from pathlib import Path

import typer
from rich import print as rich_print
from rich.console import Console
from rich.progress import Progress

# Add packages to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.src.analyzer import AVAILABLE_MODELS, analyze_repositories
from core.src.config import setup_logging
from core.src.fetcher import fetch_repositories
from core.src.reporter import save_reports

app = typer.Typer(help="Analyze GitHub repositories using LLMs", add_completion=False)

logger = logging.getLogger(__name__)
console = Console()


@app.command()
def analyze(
    github_urls: str = typer.Option(
        ..., "--github-urls", help="Comma-separated list of GitHub repository URLs"
    ),
    prompt: str = typer.Option(
        "config/prompts/default.txt", "--prompt", "-p", help="Path to the prompt file"
    ),
    output: str = typer.Option("reports", "--output", "-o", help="Directory to save reports"),
    log_level: str = typer.Option(
        "INFO",
        "--log-level",
        "-l",
        help="Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    ),
    model: str = typer.Option(
        "gemini-2.5-flash-preview-04-17",
        "--model",
        "-m",
        help="Gemini model to use for analysis",
    ),
    temperature: float = typer.Option(
        0.2,
        "--temperature",
        "-t",
        min=0.0,
        max=1.0,
        help="Temperature for generation (0.0-1.0, lower is more deterministic)",
    ),
    analysis_type: str = typer.Option(
        "fast",
        "--analysis-type",
        "-a",
        help="Analysis type: 'fast' (uses Gemini Flash) or 'deep' (uses Gemini Pro)",
    ),
    json_output: bool = typer.Option(
        False, "--json", "-j", help="Output analysis in JSON format instead of Markdown"
    ),
) -> None:
    """
    Analyze GitHub repositories using LLMs.
    """
    # Start timing
    start_time = time.time()

    # Setup logging
    setup_logging(log_level)

    # Validate model
    if model not in AVAILABLE_MODELS:
        available_models = ", ".join(AVAILABLE_MODELS.keys())
        rich_print(
            f"[bold red]Error:[/bold red] Invalid model '{model}'. Available models: {available_models}"
        )
        raise typer.Exit(code=1)

    # Override model based on analysis type
    if analysis_type == "fast":
        model = "gemini-2.5-flash-preview-04-17"
    elif analysis_type == "deep":
        model = "gemini-2.5-pro-preview-03-25"
    else:
        rich_print(
            f"[bold yellow]Warning:[/bold yellow] Unknown analysis type '{analysis_type}', using specified model."
        )

    # Parse GitHub URLs
    urls = [url.strip() for url in github_urls.split(",")]

    # Display analysis details
    rich_print("[bold]AI Project Analyzer[/bold]")
    rich_print(f"Model: [cyan]{model}[/cyan] (Temperature: {temperature})")
    rich_print(f"Analysis type: [cyan]{analysis_type}[/cyan]")
    rich_print(f"Output format: [cyan]{'JSON' if json_output else 'Markdown'}[/cyan]")
    rich_print(f"Repositories to analyze: [cyan]{len(urls)}[/cyan]")

    # Fetch repository digests with progress bar
    with Progress() as progress:
        fetch_task = progress.add_task("[green]Fetching repositories...", total=len(urls))

        repo_digests = {}

        for url in urls:
            # Update task description
            progress.update(fetch_task, description=f"[green]Fetching {url}...")

            # Fetch single repo
            single_result = fetch_repositories([url])
            if single_result:
                repo_digests.update(single_result)

            # Advance progress
            progress.advance(fetch_task)

    if not repo_digests:
        rich_print("[bold red]Error:[/bold red] No repositories were successfully fetched.")
        raise typer.Exit(code=1)

    # Analyze repositories
    rich_print(f"\nAnalyzing [cyan]{len(repo_digests)}[/cyan] repositories...")
    analyses = analyze_repositories(
        repo_digests,
        prompt,
        model_name=model,
        temperature=temperature,
        output_json=json_output,
    )

    if not analyses:
        rich_print("[bold red]Error:[/bold red] No repositories were successfully analyzed.")
        raise typer.Exit(code=1)

    # Save reports
    rich_print("\nSaving analysis reports...")
    report_paths = save_reports(analyses, output)

    # Print summary
    rich_print("\n[bold green]Analysis Complete![/bold green]")

    # Show summary report if it exists
    if "__summary__" in report_paths:
        summary_path = report_paths["__summary__"]
        rich_print(f"\n[bold yellow]Summary Report:[/bold yellow] {summary_path}")

    # List individual reports
    rich_print("\n[bold]Individual Reports:[/bold]")
    for repo_name, report_path in report_paths.items():
        if repo_name != "__summary__":
            rich_print(f"- [cyan]{repo_name}[/cyan]: {report_path}")

    # Print output directory info
    output_dir = os.path.dirname(next(iter(report_paths.values())))
    rich_print(f"\nAll reports saved to: [bold]{output_dir}[/bold]")

    # Log execution time
    end_time = time.time()
    duration = end_time - start_time
    rich_print(f"\nTotal execution time: [bold]{duration:.2f}[/bold] seconds")


if __name__ == "__main__":
    app()
