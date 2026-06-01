"""Tests for the PyAV-backed frame extraction backend."""

from __future__ import annotations

import pytest

pytest.importorskip("av")

import numpy as np

from vid2llm.backends.pyav import PyAVBackend
from vid2llm.core.types import ExtractionConfig
from vid2llm.exceptions import InvalidVideoError


def test_is_available_returns_true_in_this_environment() -> None:
    assert PyAVBackend.is_available() is True


def test_probe_returns_video_metadata(synthetic_video_path):
    backend = PyAVBackend()
    metadata = backend.probe(synthetic_video_path)

    assert metadata.width == 640
    assert metadata.height == 480
    assert abs(metadata.fps - 30.0) < 0.1
    assert metadata.frame_count == 150
    assert abs(metadata.duration_seconds - 5.0) < 0.1
    assert isinstance(metadata.codec, str)
    assert len(metadata.codec) > 0


def test_extract_yields_all_frames_with_default_config(synthetic_video_path):
    backend = PyAVBackend()
    frames = list(backend.extract(synthetic_video_path, ExtractionConfig()))

    assert len(frames) == 150


def test_extract_respects_every_n_frames(synthetic_video_path):
    backend = PyAVBackend()
    frames = list(backend.extract(synthetic_video_path, ExtractionConfig(every_n_frames=3)))

    assert len(frames) == 50


def test_extract_respects_max_frames(synthetic_video_path):
    backend = PyAVBackend()
    frames = list(backend.extract(synthetic_video_path, ExtractionConfig(max_frames=5)))

    assert len(frames) == 5


def test_extract_respects_start_and_end_time(synthetic_video_path):
    backend = PyAVBackend()
    frames = list(
        backend.extract(
            synthetic_video_path,
            ExtractionConfig(start_time_seconds=1.0, end_time_seconds=2.0),
        )
    )

    assert 25 <= len(frames) <= 35
    for frame in frames:
        assert 0.95 <= frame.timestamp_seconds <= 2.05


def test_frame_shape_and_dtype(synthetic_video_path):
    backend = PyAVBackend()
    first = next(iter(backend.extract(synthetic_video_path, ExtractionConfig())))

    assert first.image.shape == (480, 640, 3)
    assert first.image.dtype == np.uint8
    assert first.color_space == "rgb"
    assert first.source_backend == "pyav"


def test_invalid_path_raises_probe(tmp_path):
    backend = PyAVBackend()
    fake = tmp_path / "does_not_exist.mp4"

    with pytest.raises((FileNotFoundError, InvalidVideoError)):
        backend.probe(fake)


def test_invalid_path_raises_extract(tmp_path):
    backend = PyAVBackend()
    fake = tmp_path / "does_not_exist.mp4"

    with pytest.raises((FileNotFoundError, InvalidVideoError)):
        list(backend.extract(fake, ExtractionConfig()))


def test_corrupt_file_raises_invalid_video_error(tmp_path):
    backend = PyAVBackend()
    fake = tmp_path / "corrupt.mp4"
    fake.write_bytes(b"not a real video file at all" * 100)

    with pytest.raises(InvalidVideoError):
        backend.probe(fake)
