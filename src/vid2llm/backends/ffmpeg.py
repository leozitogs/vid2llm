"""FFmpeg subprocess based frame extraction backend.

The :class:`FFmpegBackend` shells out to the ``ffmpeg`` and ``ffprobe``
binaries that ship with FFmpeg. It has no Python dependency beyond
:mod:`numpy` and streams raw RGB frames through a stdout pipe, so no
temporary files are ever written to disk.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from typing import TYPE_CHECKING

import numpy as np

from vid2llm.core.types import Frame, VideoMetadata
from vid2llm.exceptions import InvalidVideoError

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from vid2llm.core.types import ExtractionConfig


def _parse_rational(rational: str) -> float:
    """Parse an ``"num/den"`` rational string into a float.

    Args:
        rational: A string such as ``"30/1"`` reported by ``ffprobe``.

    Returns:
        The numerical value, or ``0.0`` if the string is malformed or
        the denominator is zero.
    """
    if not rational or "/" not in rational:
        return 0.0
    num_str, _, den_str = rational.partition("/")
    try:
        num = float(num_str)
        den = float(den_str)
    except ValueError:
        return 0.0
    if den == 0:
        return 0.0
    return num / den


class FFmpegBackend:
    """Frame extraction backend backed by the FFmpeg binaries.

    Spawns one ``ffprobe`` invocation per :meth:`probe` and one
    ``ffmpeg`` invocation per :meth:`extract`. Frames are streamed as
    raw ``rgb24`` bytes through stdout.
    """

    name: str = "ffmpeg"

    @classmethod
    def is_available(cls) -> bool:
        """Report whether the ``ffmpeg`` and ``ffprobe`` binaries are on PATH.

        Returns:
            ``True`` if both binaries are discoverable, ``False`` otherwise.
        """
        return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None

    def probe(self, path: Path) -> VideoMetadata:
        """Read metadata from the source video by invoking ``ffprobe``.

        The ``-count_frames`` flag forces an exact frame count by reading
        every packet, at the cost of a full pass over the file.

        Args:
            path: Filesystem path to the source video.

        Returns:
            A populated :class:`VideoMetadata` describing the video.

        Raises:
            FileNotFoundError: The path does not exist on disk.
            InvalidVideoError: ``ffprobe`` returns a non-zero exit status
                or the output cannot be parsed.
        """
        if not path.exists():
            raise FileNotFoundError(f"Video file does not exist: {path}")

        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-count_frames",
                "-select_streams",
                "v:0",
                "-show_streams",
                "-show_format",
                "-print_format",
                "json",
                str(path),
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise InvalidVideoError(f"ffprobe failed for {path}: {result.stderr.strip()}")

        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise InvalidVideoError(f"ffprobe returned invalid JSON for {path}: {exc}") from exc

        streams = payload.get("streams") or []
        if not streams:
            raise InvalidVideoError(f"No video stream found in: {path}")
        stream = streams[0]
        format_section = payload.get("format") or {}

        try:
            width = int(stream["width"])
            height = int(stream["height"])
        except (KeyError, TypeError, ValueError) as exc:
            raise InvalidVideoError(
                f"ffprobe missing required stream dimensions for {path}: {exc}"
            ) from exc

        fps = _parse_rational(str(stream.get("r_frame_rate", "")))

        nb_read_frames = stream.get("nb_read_frames")
        try:
            frame_count = int(nb_read_frames) if nb_read_frames is not None else 0
        except (TypeError, ValueError):
            frame_count = 0

        codec = str(stream.get("codec_name", ""))

        duration_raw = format_section.get("duration")
        try:
            duration_seconds = float(duration_raw) if duration_raw is not None else 0.0
        except (TypeError, ValueError):
            duration_seconds = 0.0

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
        """Yield decoded frames by streaming raw RGB bytes from ``ffmpeg``.

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
            InvalidVideoError: ``ffprobe`` cannot describe the file.
        """
        if not path.exists():
            raise FileNotFoundError(f"Video file does not exist: {path}")

        metadata = self.probe(path)
        width = metadata.width
        height = metadata.height
        fps = metadata.fps
        bytes_per_frame = width * height * 3

        cmd: list[str] = ["ffmpeg", "-v", "error"]
        if config.start_time_seconds > 0:
            cmd.extend(["-ss", str(config.start_time_seconds)])
        # ``-to`` is placed as an input option (before ``-i``) so that the
        # end timestamp refers to the original input timeline rather than
        # the post-seek output timeline.
        if config.end_time_seconds is not None:
            cmd.extend(["-to", str(config.end_time_seconds)])
        cmd.extend(["-i", str(path)])

        filters: list[str] = []
        if config.every_n_frames > 1:
            filters.append(f"select=not(mod(n\\,{config.every_n_frames}))")
        if filters:
            cmd.extend(["-vf", ",".join(filters), "-vsync", "vfr"])

        cmd.extend(["-f", "rawvideo", "-pix_fmt", "rgb24"])
        if config.max_frames is not None:
            cmd.extend(["-frames:v", str(config.max_frames)])
        cmd.append("pipe:1")

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=10**7,
        )
        try:
            if process.stdout is None:
                raise InvalidVideoError(f"ffmpeg process did not expose a stdout pipe for {path}")

            stride = config.every_n_frames if config.every_n_frames > 1 else 1
            source_frame_index = round(config.start_time_seconds * fps) if fps > 0 else 0
            yielded_count = 0

            while True:
                frame_bytes = process.stdout.read(bytes_per_frame)
                if len(frame_bytes) < bytes_per_frame:
                    break

                rgb_array = (
                    np.frombuffer(frame_bytes, dtype=np.uint8).reshape((height, width, 3)).copy()
                )
                timestamp_seconds = source_frame_index / fps if fps > 0 else 0.0

                yield Frame(
                    index=source_frame_index,
                    timestamp_seconds=timestamp_seconds,
                    image=rgb_array,
                    color_space="rgb",
                    source_backend=self.name,
                )

                source_frame_index += stride
                yielded_count += 1
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            if process.stdout is not None:
                process.stdout.close()
            if process.stderr is not None:
                process.stderr.close()
