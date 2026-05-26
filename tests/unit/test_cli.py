"""Smoke tests for the vid2llm command-line interface.

These tests verify the CLI stub behaves correctly. They will evolve as
real commands are added in later phases.
"""

from __future__ import annotations

from typer.testing import CliRunner

from vid2llm import __version__
from vid2llm.cli import app

_runner = CliRunner()


def test_cli_runs_without_arguments() -> None:
    """Running vid2llm with no arguments exits successfully."""
    result = _runner.invoke(app, [])

    assert result.exit_code == 0


def test_cli_output_contains_version() -> None:
    """The CLI banner includes the installed package version."""
    result = _runner.invoke(app, [])

    assert __version__ in result.stdout


def test_cli_output_mentions_roadmap() -> None:
    """The CLI banner informs the user that no commands are available yet."""
    result = _runner.invoke(app, [])

    assert "ROADMAP" in result.stdout
