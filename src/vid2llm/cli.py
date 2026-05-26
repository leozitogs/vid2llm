"""Command-line interface entry point for vid2llm.

This module exposes a Typer application that is registered as the
``vid2llm`` console script in ``pyproject.toml``. The current implementation
is a stub that reports the installed version and points users to the
project roadmap. Feature commands arrive in later phases.
"""

from __future__ import annotations

import typer
from rich.console import Console

from vid2llm import __version__

app = typer.Typer(
    name="vid2llm",
    help="Turn any video into LLM-ready frames.",
    no_args_is_help=False,
    add_completion=False,
)

_console = Console()


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """Print the package banner when no subcommand is provided.

    Args:
        ctx: Typer context, used to detect whether a subcommand was invoked.
    """
    if ctx.invoked_subcommand is not None:
        return

    _console.print(f"[bold]vid2llm[/bold] [dim]v{__version__}[/dim]")
    _console.print("[yellow]no commands available yet, see ROADMAP[/yellow]")
