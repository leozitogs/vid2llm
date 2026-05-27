"""vid2llm: turn any video into LLM-ready frames.

This package provides a focused toolkit for extracting frames from videos
and preparing them for consumption by modern multimodal language models.

The public surface consists of the data contract types (:class:`Frame`,
:class:`VideoMetadata`, :class:`ExtractionConfig`, :class:`ExtractionResult`
and their associated literal aliases), the :class:`FrameBackend` protocol
that backend implementations satisfy, and the exception hierarchy rooted at
:class:`Vid2LLMError`.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from vid2llm.backends.base import FrameBackend
from vid2llm.core.types import (
    ColorSpace,
    ExtractionConfig,
    ExtractionResult,
    Frame,
    ImageFormat,
    VideoMetadata,
)
from vid2llm.exceptions import (
    BackendError,
    BackendNotAvailableError,
    ConfigurationError,
    ExtractionError,
    InvalidVideoError,
    NoBackendAvailableError,
    UnsupportedFormatError,
    Vid2LLMError,
)

try:
    __version__: str = version("vid2llm")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = [
    "BackendError",
    "BackendNotAvailableError",
    "ColorSpace",
    "ConfigurationError",
    "ExtractionConfig",
    "ExtractionError",
    "ExtractionResult",
    "Frame",
    "FrameBackend",
    "ImageFormat",
    "InvalidVideoError",
    "NoBackendAvailableError",
    "UnsupportedFormatError",
    "Vid2LLMError",
    "VideoMetadata",
    "__version__",
]
