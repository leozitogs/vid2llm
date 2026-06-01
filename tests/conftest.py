"""Shared pytest fixtures and configuration for the vid2llm test suite.

Fixtures defined here are automatically discovered by pytest and made
available to every test module in the suite. This module is intentionally
minimal during Phase 0 and grows as the package gains features.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Final

import pytest

REAL_VIDEO_DIR: Final[Path] = Path(__file__).parent / "fixtures" / "videos"
"""Directory where real (non-synthetic) video fixtures are expected to live.

Tests marked with ``real_video`` opt into reading from this directory and
should skip themselves when the expected files are not present.
"""


def pytest_configure(config: pytest.Config) -> None:
    """Register custom pytest markers used by the suite."""
    config.addinivalue_line(
        "markers",
        "real_video: tests that require real video files in tests/fixtures/videos/",
    )


@pytest.fixture(scope="session")
def synthetic_video_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Generate a deterministic synthetic H264 MP4 fixture via ffmpeg.

    Produces a 5-second, 30fps, 640x480 ``testsrc`` pattern encoded with
    ``libx264`` in ``yuv420p``. The file lives in a session-scoped temp
    directory and is cleaned up after the test session.

    Returns:
        Path to the generated MP4 file.
    """
    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg binary is required to generate the synthetic fixture")
    output_path = tmp_path_factory.mktemp("vid2llm_fixtures") / "synthetic.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "testsrc=duration=5:size=640x480:rate=30",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-y",
            str(output_path),
        ],
        check=True,
    )
    return output_path
