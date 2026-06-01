"""OpenCV-based frame extraction backend.

Wraps the ``cv2`` Python bindings. The :class:`OpenCVBackend` is fast for
common containers, depends only on a single PyPI package, and produces
frames in OpenCV's native ``bgr`` color space.

The module imports :mod:`cv2` at the top level by design. The selector
only loads this module after confirming ``cv2`` is importable in the
environment, and the package ``__init__`` guards the symbol with a
``try``/``except ImportError`` so consumers without the ``cv`` extra can
still import :mod:`vid2llm`.
"""

from __future__ import annotations

import importlib.util
from typing import TYPE_CHECKING

import cv2
import numpy as np
from numpy.typing import NDArray

from vid2llm.core.types import Frame, VideoMetadata
from vid2llm.exceptions import InvalidVideoError

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from vid2llm.core.types import ExtractionConfig


def _fourcc_to_codec(fourcc_int: int) -> str:
    """Decode an OpenCV FOURCC integer into a 4-character codec string.

    Args:
        fourcc_int: Raw integer reported by ``cv2.CAP_PROP_FOURCC``.

    Returns:
        Lowercase 4-character codec identifier, or an empty string if the
        value is zero or unreadable.
    """
    if fourcc_int <= 0:
        return ""
    chars = [chr((fourcc_int >> (8 * i)) & 0xFF) for i in range(4)]
    return "".join(c for c in chars if c.isprintable()).strip().lower()


class OpenCVBackend:
    """Frame extraction backend backed by OpenCV.

    Produces frames in the ``bgr`` color space, matching OpenCV's native
    pixel ordering. Suitable for environments where ``opencv-python`` (or
    ``opencv-python-headless``) is installed.
    """

    name: str = "opencv"

    @classmethod
    def is_available(cls) -> bool:
        """Report whether the ``cv2`` Python bindings are importable.

        Returns:
            ``True`` if ``cv2`` can be found by the import system,
            ``False`` otherwise.
        """
        return importlib.util.find_spec("cv2") is not None

    def probe(self, path: Path) -> VideoMetadata:
        """Read metadata from the source video without decoding pixels.

        The frame count is computed exactly by iterating with
        ``cap.grab()`` rather than trusting ``CAP_PROP_FRAME_COUNT``,
        which is unreliable on variable-bitrate streams.

        Args:
            path: Filesystem path to the source video.

        Returns:
            A populated :class:`VideoMetadata` describing the video.

        Raises:
            FileNotFoundError: The path does not exist on disk.
            InvalidVideoError: OpenCV refuses to open the file.
        """
        if not path.exists():
            raise FileNotFoundError(f"Video file does not exist: {path}")

        cap = cv2.VideoCapture(str(path))
        try:
            if not cap.isOpened():
                raise InvalidVideoError(f"OpenCV could not open video: {path}")

            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = float(cap.get(cv2.CAP_PROP_FPS))
            fourcc_int = int(cap.get(cv2.CAP_PROP_FOURCC))
            codec = _fourcc_to_codec(fourcc_int)

            frame_count = 0
            while cap.grab():
                frame_count += 1

            duration_seconds = frame_count / fps if fps > 0 else 0.0
        finally:
            cap.release()

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
        produced in OpenCV's native ``bgr`` color space with ``uint8``
        pixel data.

        Args:
            path: Filesystem path to the source video.
            config: Extraction parameters.

        Yields:
            Decoded frames that satisfy the configuration filters.

        Raises:
            FileNotFoundError: The path does not exist on disk.
            InvalidVideoError: OpenCV refuses to open the file.
        """
        if not path.exists():
            raise FileNotFoundError(f"Video file does not exist: {path}")

        cap = cv2.VideoCapture(str(path))
        try:
            if not cap.isOpened():
                raise InvalidVideoError(f"OpenCV could not open video: {path}")

            if config.start_time_seconds > 0:
                cap.set(cv2.CAP_PROP_POS_MSEC, config.start_time_seconds * 1000.0)

            stride = config.every_n_frames
            candidate_counter = 0
            yielded_count = 0

            while True:
                ret, image = cap.read()
                if not ret:
                    break

                timestamp_seconds = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                # POS_FRAMES is advanced to the next frame after a successful read.
                frame_index = int(cap.get(cv2.CAP_PROP_POS_FRAMES)) - 1

                if (
                    config.end_time_seconds is not None
                    and timestamp_seconds >= config.end_time_seconds
                ):
                    break

                if candidate_counter % stride == 0:
                    if config.max_frames is not None and yielded_count >= config.max_frames:
                        break

                    image_array: NDArray[np.uint8] = np.ascontiguousarray(image, dtype=np.uint8)
                    yield Frame(
                        index=frame_index,
                        timestamp_seconds=timestamp_seconds,
                        image=image_array,
                        color_space="bgr",
                        source_backend=self.name,
                    )
                    yielded_count += 1

                candidate_counter += 1
        finally:
            cap.release()
