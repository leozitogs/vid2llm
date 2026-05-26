"""Allow execution via ``python -m vid2llm``.

Delegates to the Typer application defined in :mod:`vid2llm.cli`.
"""

from __future__ import annotations

from vid2llm.cli import app

if __name__ == "__main__":
    app()
