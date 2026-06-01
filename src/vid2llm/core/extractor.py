"""High-level frame extraction orchestrator.

Provides the primary public API for extracting frames from videos.
The orchestrator decouples callers from backend selection and disk I/O,
offering both a lazy streaming interface and a collecting convenience
wrapper.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from vid2llm.core.encoder import save_frame
from vid2llm.core.selector import select_backend
from vid2llm.core.types import ExtractionConfig, ExtractionResult, Frame
from vid2llm.exceptions import ExtractionError, Vid2LLMError

if TYPE_CHECKING:
    from collections.abc import Iterator


def extract_frames(
    video_path: str | Path,
    config: ExtractionConfig | None = None,
    backend: str | None = None,
    output_dir: str | Path | None = None,
) -> Iterator[Frame]:
    """Stream frames from a video, optionally saving them to disk.

    This is the core public streaming API. Frames are yielded lazily.
    When output_dir is provided, each frame is written to disk immediately
    before being yielded.

    Args:
        video_path: Path to the source video.
        config: Extraction configuration. Defaults to ExtractionConfig().
        backend: Backend name to force, or None to auto-select.
        output_dir: Directory to write frames to, or None for pure streaming.

    Yields:
        Frame objects in source order after filtering.

    Raises:
        FileNotFoundError: If video_path does not exist.
        InvalidVideoError: If the video cannot be opened or decoded.
        NoBackendAvailableError: If no backend is available.
        BackendNotAvailableError: If the requested backend is unavailable.
        ExtractionError: If decoding fails unexpectedly mid-stream.
    """
    resolved_config = config if config is not None else ExtractionConfig()
    path = Path(video_path)
    selected = select_backend(backend)
    out = Path(output_dir) if output_dir is not None else None

    try:
        for frame in selected.extract(path, resolved_config):
            if out is not None:
                save_frame(frame, out, resolved_config.image_format)
            yield frame
    except (FileNotFoundError, Vid2LLMError):
        raise
    except Exception as exc:
        raise ExtractionError(f"Unexpected error during frame extraction: {exc}") from exc


def extract_to_list(
    video_path: str | Path,
    config: ExtractionConfig | None = None,
    backend: str | None = None,
) -> ExtractionResult:
    """Collect all frames into memory and return an ExtractionResult.

    Convenience wrapper over extract_frames for callers that want the full
    result rather than a stream. Runs probe() to populate metadata.

    The backend is selected once and reused for both probe and extract, so
    metadata and frames always come from the same backend.

    frames_considered is set to metadata.frame_count, which is the total
    number of frames reported by the backend. Because backends apply
    filtering internally, the orchestrator cannot observe discarded frames
    directly; metadata.frame_count serves as an approximation of the
    number of frames considered before filtering.

    Args:
        video_path: Path to the source video.
        config: Extraction configuration. Defaults to ExtractionConfig().
        backend: Backend name to force, or None to auto-select.

    Returns:
        An ExtractionResult with frames, metadata, backend_used,
        frames_considered, and frames_yielded populated.

    Raises:
        FileNotFoundError: If video_path does not exist.
        InvalidVideoError: If the video cannot be opened or decoded.
        NoBackendAvailableError: If no backend is available.
        BackendNotAvailableError: If the requested backend is unavailable.
        ExtractionError: If decoding fails unexpectedly mid-stream.
    """
    resolved_config = config if config is not None else ExtractionConfig()
    path = Path(video_path)
    selected = select_backend(backend)
    metadata = selected.probe(path)
    frames = list(selected.extract(path, resolved_config))
    return ExtractionResult(
        frames=frames,
        metadata=metadata,
        backend_used=selected.name,
        frames_considered=metadata.frame_count,
        frames_yielded=len(frames),
    )
