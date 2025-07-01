"""Tests for CLI module."""

from typer.testing import CliRunner


def test_cli_imports():
    """Test that CLI module imports successfully."""
    from cli.src.cli import app

    assert app is not None


def test_cli_help():
    """Test CLI help command."""
    from cli.src.cli import app

    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Analyze GitHub repositories using LLMs" in result.output
