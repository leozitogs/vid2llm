"""vid2llm: turn any video into LLM-ready frames.

This package provides a focused toolkit for extracting frames from videos
and preparing them for consumption by modern multimodal language models.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from vid2llm.exceptions import Vid2LLMError

try:
    __version__: str = version("vid2llm")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = [
    "Vid2LLMError",
    "__version__",
]
