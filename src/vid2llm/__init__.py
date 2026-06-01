"""vid2llm: turn any video into LLM-ready frames.

This package provides a focused toolkit for extracting frames from videos
and preparing them for consumption by modern multimodal language models.

The public surface consists of the data contract types (:class:`Frame`,
:class:`VideoMetadata`, :class:`ExtractionConfig`, :class:`ExtractionResult`
and their associated literal aliases), the :class:`FrameBackend` protocol
that backend implementations satisfy, the concrete backend classes, the
backend selector, and the exception hierarchy rooted at
:class:`Vid2LLMError`.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from vid2llm.backends.base import FrameBackend
from vid2llm.backends.ffmpeg import FFmpegBackend
from vid2llm.core.extractor import extract_frames, extract_to_list
from vid2llm.core.selector import list_available_backends, select_backend
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
    from vid2llm.backends.opencv import OpenCVBackend
except ImportError:
    OpenCVBackend = None  # type: ignore[assignment, misc]

try:
    from vid2llm.backends.pyav import PyAVBackend
except ImportError:
    PyAVBackend = None  # type: ignore[assignment, misc]

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
    "FFmpegBackend",
    "Frame",
    "FrameBackend",
    "ImageFormat",
    "InvalidVideoError",
    "NoBackendAvailableError",
    "OpenCVBackend",
    "PyAVBackend",
    "UnsupportedFormatError",
    "Vid2LLMError",
    "VideoMetadata",
    "__version__",
    "extract_frames",
    "extract_to_list",
    "list_available_backends",
    "select_backend",
]
