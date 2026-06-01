"""PyAV-based frame extraction backend.

Uses the :mod:`av` package, which exposes the FFmpeg C libraries through a
Pythonic API. The :class:`PyAVBackend` provides precise presentation
timestamps and works directly with container metadata without spawning a
subprocess.

The :mod:`av` import lives at the top of this module by design. The
selector only imports the module after confirming the dependency is
available, and the package ``__init__`` guards the symbol with a
``try``/``except ImportError``.
"""

from __future__ import annotations

import importlib.util
from typing import TYPE_CHECKING, Any

import av
import numpy as np
from numpy.typing import NDArray

from vid2llm.core.types import Frame, VideoMetadata
from vid2llm.exceptions import InvalidVideoError

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from vid2llm.core.types import ExtractionConfig


def _av_error_types() -> tuple[type[BaseException], ...]:
    """Return the tuple of exception types to catch around ``av.open``.

    PyAV renamed its base error class between major versions. This helper
    discovers whichever symbol is exposed by the installed version and
    pairs it with the standard library exceptions raised on bad input.
    """
    for attribute in ("FFmpegError", "AVError"):
        exc: type[BaseException] | None = getattr(av, attribute, None)
        if exc is not None:
            return (exc, OSError, ValueError)
    return (OSError, ValueError)


_AV_OPEN_ERRORS = _av_error_types()


class PyAVBackend:
    """Frame extraction backend backed by PyAV.

    Produces frames in the ``rgb`` color space, matching the convention
    used by most LLM image inputs. Suitable for environments where the
    :mod:`av` package is installed.
    """

    name: str = "pyav"

    @classmethod
    def is_available(cls) -> bool:
        """Report whether the ``av`` Python package is importable.

        Returns:
            ``True`` if :mod:`av` can be found by the import system,
            ``False`` otherwise.
        """
        return importlib.util.find_spec("av") is not None

    def probe(self, path: Path) -> VideoMetadata:
        """Read metadata from the source video without retaining frames.

        Performs a full decode pass to compute an exact frame count.
        ``stream.frames`` is unreliable on containers without an index,
        so the count is derived from the actual decoded frame sequence.

        Args:
            path: Filesystem path to the source video.

        Returns:
            A populated :class:`VideoMetadata` describing the video.

        Raises:
            FileNotFoundError: The path does not exist on disk.
            InvalidVideoError: PyAV refuses to open the file or the file
                contains no video stream.
        """
        if not path.exists():
            raise FileNotFoundError(f"Video file does not exist: {path}")

        try:
            container = av.open(str(path))
        except _AV_OPEN_ERRORS as exc:
            raise InvalidVideoError(f"PyAV could not open video {path}: {exc}") from exc

        try:
            if not container.streams.video:
                raise InvalidVideoError(f"No video stream found in: {path}")
            stream = container.streams.video[0]
            codec_context: Any = stream.codec_context
            width = int(codec_context.width)
            height = int(codec_context.height)
            codec = str(codec_context.name or "")

            average_rate = stream.average_rate
            fps = float(average_rate) if average_rate else 0.0

            frame_count = 0
            try:
                for _ in container.decode(video=0):
                    frame_count += 1
            except _AV_OPEN_ERRORS as exc:
                raise InvalidVideoError(f"PyAV failed to decode {path}: {exc}") from exc

            if stream.duration is not None and stream.time_base is not None:
                duration_seconds = float(stream.duration * stream.time_base)
            elif fps > 0:
                duration_seconds = frame_count / fps
            else:
                duration_seconds = 0.0
        finally:
            container.close()

        return VideoMetadata(
            path=path,
            width=width,
            height=height,
            frame_count=frame_count,
            fps=fps,
            duration_seconds=duration_seconds,
            codec=codec,
        )

    def extract(self, path: Path, config: ExtractionConfig) -> Iterator[Frame]:
        """Yield decoded frames from a video lazily.

        Honors ``start_time_seconds``, ``end_time_seconds``,
        ``every_n_frames`` and ``max_frames`` from ``config``. Frames are
        produced in the ``rgb`` color space with ``uint8`` pixel data.

        Args:
            path: Filesystem path to the source video.
            config: Extraction parameters.

        Yields:
            Decoded frames that satisfy the configuration filters.

        Raises:
            FileNotFoundError: The path does not exist on disk.
            InvalidVideoError: PyAV refuses to open the file.
        """
        if not path.exists():
            raise FileNotFoundError(f"Video file does not exist: {path}")

        try:
            container = av.open(str(path))
        except _AV_OPEN_ERRORS as exc:
            raise InvalidVideoError(f"PyAV could not open video {path}: {exc}") from exc

        try:
            stream = container.streams.video[0]
            average_rate = stream.average_rate
            fps = float(average_rate) if average_rate else 0.0
            time_base = stream.time_base

            if config.start_time_seconds > 0 and time_base is not None:
                seek_target_pts = int(config.start_time_seconds / float(time_base))
                container.seek(seek_target_pts, stream=stream)

            stride = config.every_n_frames
            candidate_counter = 0
            yielded_count = 0
            frame_counter = 0

            for frame in container.decode(video=0):
                if frame.pts is not None and time_base is not None:
                    pts_seconds = float(frame.pts * time_base)
                elif fps > 0:
                    pts_seconds = frame_counter / fps
                else:
                    pts_seconds = 0.0

                frame_counter += 1

                if pts_seconds < config.start_time_seconds:
                    continue

                if config.end_time_seconds is not None and pts_seconds >= config.end_time_seconds:
                    break

                if candidate_counter % stride == 0:
                    if config.max_frames is not None and yielded_count >= config.max_frames:
                        break

                    raw_array = frame.to_ndarray(format="rgb24")
                    rgb_array: NDArray[np.uint8] = np.ascontiguousarray(raw_array, dtype=np.uint8)
                    frame_index_attr = getattr(frame, "index", None)
                    frame_index = (
                        frame_index_attr if frame_index_attr is not None else frame_counter - 1
                    )

                    yield Frame(
                        index=int(frame_index),
                        timestamp_seconds=pts_seconds,
                        image=rgb_array,
                        color_space="rgb",
                        source_backend=self.name,
                    )
                    yielded_count += 1

                candidate_counter += 1
        finally:
            container.close()
