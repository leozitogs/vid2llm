from __future__ import annotations

from typing import TYPE_CHECKING

import PIL.Image
import pytest

from vid2llm.core.extractor import extract_frames, extract_to_list
from vid2llm.core.selector import list_available_backends
from vid2llm.core.types import ExtractionConfig
from vid2llm.exceptions import InvalidVideoError

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = pytest.mark.skipif(
    not list_available_backends(),
    reason="no backend available in this environment",
)


def test_extract_to_list_populates_result(synthetic_video_path: Path) -> None:
    result = extract_to_list(synthetic_video_path)
    assert result.frames_yielded == 150
    assert len(result.frames) == 150
    assert result.backend_used in ("opencv", "pyav", "ffmpeg")
    assert result.metadata is not None
    assert result.metadata.frame_count == 150
    assert result.frames_considered == 150


def test_extract_frames_streams_without_saving(synthetic_video_path: Path) -> None:
    count = sum(1 for _ in extract_frames(synthetic_video_path))
    assert count == 150


def test_extract_frames_saves_to_output_dir(synthetic_video_path: Path, tmp_path: Path) -> None:
    out = tmp_path / "frames"
    frames = list(
        extract_frames(synthetic_video_path, ExtractionConfig(max_frames=5), output_dir=out)
    )
    assert len(frames) == 5
    written = sorted(out.glob("frame_*.jpg"))
    assert len(written) == 5
    for f in written:
        with PIL.Image.open(f):
            pass


def test_extract_frames_respects_every_n_frames(synthetic_video_path: Path) -> None:
    count = sum(1 for _ in extract_frames(synthetic_video_path, ExtractionConfig(every_n_frames=3)))
    assert count == 50


def test_extract_frames_filename_uses_source_index(
    synthetic_video_path: Path, tmp_path: Path
) -> None:
    out = tmp_path / "frames"
    frames = list(
        extract_frames(synthetic_video_path, ExtractionConfig(every_n_frames=30), output_dir=out)
    )
    for frame in frames:
        expected = out / f"frame_{frame.index:06d}.jpg"
        assert expected.exists(), f"Expected file {expected} does not exist"


def test_extract_frames_png_format(synthetic_video_path: Path, tmp_path: Path) -> None:
    out = tmp_path / "frames"
    list(
        extract_frames(
            synthetic_video_path,
            ExtractionConfig(max_frames=3, image_format="png"),
            output_dir=out,
        )
    )
    assert len(list(out.glob("frame_*.png"))) == 3


def test_invalid_path_raises(tmp_path: Path) -> None:
    with pytest.raises((FileNotFoundError, InvalidVideoError)):
        list(extract_frames(tmp_path / "nope.mp4"))
