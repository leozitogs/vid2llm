"""Backend implementations and the protocol they satisfy.

The concrete backends are re-exported from this package for convenience.
Backends that rely on optional third-party dependencies are guarded with
a ``try``/``except ImportError`` so that consumers without those extras
installed can still import :mod:`vid2llm.backends`.
"""

from __future__ import annotations

from vid2llm.backends.base import FrameBackend
from vid2llm.backends.ffmpeg import FFmpegBackend

try:
    from vid2llm.backends.opencv import OpenCVBackend
except ImportError:
    OpenCVBackend = None  # type: ignore[assignment, misc]

try:
    from vid2llm.backends.pyav import PyAVBackend
except ImportError:
    PyAVBackend = None  # type: ignore[assignment, misc]

__all__ = [
    "FFmpegBackend",
    "FrameBackend",
    "OpenCVBackend",
    "PyAVBackend",
]
