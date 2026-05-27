"""Public data contract for the frame extraction system.

This module defines the immutable value types that flow between the
orchestrator, the backends, and the public API. Every type here is part of
the public surface of :mod:`vid2llm` and follows semantic versioning.

The types are deliberately framework agnostic: a backend produces
:class:`Frame` and :class:`VideoMetadata` instances, the orchestrator wraps
them in an :class:`ExtractionResult`, and the caller consumes them without
needing to know which backend produced them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from pathlib import Path

    import numpy as np
    from numpy.typing import NDArray


ImageFormat = Literal["jpg", "png", "webp"]
"""Supported output formats for serialized frames."""

ColorSpace = Literal["bgr", "rgb"]
"""Channel ordering of a frame's pixel array.

``bgr`` matches OpenCV's native ordering. ``rgb`` matches the convention used
by most LLM providers and image libraries. Backends declare which color space
they produce; the orchestrator converts when necessary.
"""


@dataclass(frozen=True, slots=True)
class Frame:
    """A single decoded video frame.

    Frames are immutable value objects. The pixel data is held by reference,
    not copied, so that streaming pipelines can produce and consume frames
    without unnecessary allocations. Consumers that need to keep a frame
    beyond the current iteration should copy ``image`` explicitly.

    Attributes:
        index: Zero based index of the frame in the source video.
        timestamp_seconds: Presentation timestamp of the frame in seconds.
        image: Pixel data as a uint8 numpy array with shape ``(H, W, 3)``.
        color_space: Channel ordering of ``image``.
        source_backend: Stable identifier of the backend that produced this
            frame (for example ``"opencv"``, ``"pyav"``, ``"ffmpeg"``).
    """

    index: int
    timestamp_seconds: float
    image: NDArray[np.uint8]
    color_space: ColorSpace
    source_backend: str


@dataclass(frozen=True, slots=True)
class VideoMetadata:
    """Static metadata describing a video file.

    Returned by :meth:`FrameBackend.probe` without decoding any frames.

    Attributes:
        path: Filesystem path to the source video.
        width: Frame width in pixels.
        height: Frame height in pixels.
        frame_count: Total number of frames. May be approximate or zero for
            streams or containers without a known length.
        fps: Average frames per second.
        duration_seconds: Total duration in seconds.
        codec: Lowercase codec identifier (for example ``"h264"``).
    """

    path: Path
    width: int
    height: int
    frame_count: int
    fps: float
    duration_seconds: float
    codec: str


@dataclass(frozen=True, slots=True)
class ExtractionConfig:
    """User facing configuration for a frame extraction run.

    All fields have sensible defaults so that ``ExtractionConfig()`` yields a
    valid configuration that extracts every frame of the input.

    Attributes:
        every_n_frames: Keep one frame every ``N`` decoded frames. Must be at
            least 1.
        max_frames: Optional cap on the number of frames returned after
            filtering. ``None`` means no cap.
        start_time_seconds: Skip frames before this timestamp.
        end_time_seconds: Stop after this timestamp. ``None`` means run to
            the end of the video.
        image_format: Output format used when the orchestrator serializes
            frames to disk.

    Raises:
        ValueError: If any field violates its documented constraint.
    """

    every_n_frames: int = 1
    max_frames: int | None = None
    start_time_seconds: float = 0.0
    end_time_seconds: float | None = None
    image_format: ImageFormat = "jpg"

    def __post_init__(self) -> None:
        """Validate field invariants after construction."""
        if self.every_n_frames < 1:
            raise ValueError(f"every_n_frames must be at least 1, got {self.every_n_frames}")
        if self.max_frames is not None and self.max_frames < 1:
            raise ValueError(f"max_frames must be at least 1, got {self.max_frames}")
        if self.start_time_seconds < 0:
            raise ValueError(
                f"start_time_seconds must be non-negative, got {self.start_time_seconds}"
            )
        if self.end_time_seconds is not None and self.end_time_seconds <= self.start_time_seconds:
            raise ValueError(
                "end_time_seconds must be greater than start_time_seconds, got "
                f"end_time_seconds={self.end_time_seconds}, "
                f"start_time_seconds={self.start_time_seconds}"
            )


@dataclass(frozen=True, slots=True)
class ExtractionResult:
    """Aggregate result of a frame extraction run.

    Attributes:
        frames: The list of frames returned to the caller after filtering.
        metadata: Metadata of the source video, when available.
        backend_used: Stable identifier of the backend that performed the
            extraction.
        frames_considered: Total number of frames inspected by the backend
            before filtering.
        frames_yielded: Number of frames returned after filtering. Equal to
            ``len(frames)`` for in memory results, but distinct from
            ``frames_considered`` and useful for streaming pipelines that do
            not retain frames.
    """

    frames: list[Frame] = field(default_factory=list)
    metadata: VideoMetadata | None = None
    backend_used: str = ""
    frames_considered: int = 0
    frames_yielded: int = 0
