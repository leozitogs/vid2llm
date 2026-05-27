"""Tests for the public data contract in vid2llm.core.types."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from vid2llm.core.types import (
    ExtractionConfig,
    ExtractionResult,
    Frame,
    VideoMetadata,
)


def _make_image() -> np.ndarray:
    return np.zeros((4, 6, 3), dtype=np.uint8)


class TestFrame:
    def test_frame_is_immutable(self) -> None:
        frame = Frame(
            index=0,
            timestamp_seconds=0.0,
            image=_make_image(),
            color_space="bgr",
            source_backend="stub",
        )
        with pytest.raises(AttributeError):
            frame.index = 1  # type: ignore[misc]

    def test_frame_holds_image_with_expected_shape_and_dtype(self) -> None:
        image = _make_image()
        frame = Frame(
            index=2,
            timestamp_seconds=0.083,
            image=image,
            color_space="rgb",
            source_backend="stub",
        )
        assert frame.image.shape == (4, 6, 3)
        assert frame.image.dtype == np.uint8
        assert frame.image is image


class TestExtractionConfig:
    def test_default_config_constructs(self) -> None:
        config = ExtractionConfig()
        assert config.every_n_frames == 1
        assert config.max_frames is None
        assert config.start_time_seconds == 0.0
        assert config.end_time_seconds is None
        assert config.image_format == "jpg"

    def test_every_n_frames_zero_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="every_n_frames must be at least 1"):
            ExtractionConfig(every_n_frames=0)

    def test_every_n_frames_negative_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="every_n_frames must be at least 1"):
            ExtractionConfig(every_n_frames=-3)

    def test_max_frames_zero_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="max_frames must be at least 1"):
            ExtractionConfig(max_frames=0)

    def test_negative_start_time_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="must be non-negative"):
            ExtractionConfig(start_time_seconds=-0.5)

    def test_end_time_not_after_start_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="must be greater than"):
            ExtractionConfig(start_time_seconds=2.0, end_time_seconds=2.0)

    def test_valid_time_window_constructs(self) -> None:
        config = ExtractionConfig(start_time_seconds=1.0, end_time_seconds=3.5)
        assert config.start_time_seconds == 1.0
        assert config.end_time_seconds == 3.5


class TestVideoMetadata:
    def test_metadata_is_immutable(self) -> None:
        metadata = VideoMetadata(
            path=Path("video.mp4"),
            width=1920,
            height=1080,
            frame_count=300,
            fps=30.0,
            duration_seconds=10.0,
            codec="h264",
        )
        with pytest.raises(AttributeError):
            metadata.width = 0  # type: ignore[misc]


class TestExtractionResult:
    def test_empty_result_has_sensible_defaults(self) -> None:
        result = ExtractionResult()
        assert result.frames == []
        assert result.metadata is None
        assert result.backend_used == ""
        assert result.frames_yielded == 0
        assert result.frames_considered == 0
