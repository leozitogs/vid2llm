from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from typer.testing import CliRunner

from vid2llm.cli import app
from vid2llm.core.selector import list_available_backends

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = pytest.mark.skipif(
    not list_available_backends(),
    reason="no backend available in this environment",
)

runner = CliRunner()


def test_probe_command_succeeds(synthetic_video_path: Path) -> None:
    result = runner.invoke(app, ["probe", str(synthetic_video_path)])
    assert result.exit_code == 0
    assert "Frames:" in result.stdout
    assert "Codec:" in result.stdout
    assert "FPS:" in result.stdout


def test_probe_command_missing_file(tmp_path: Path) -> None:
    result = runner.invoke(app, ["probe", str(tmp_path / "nope.mp4")])
    assert result.exit_code == 1


def test_extract_command_saves_frames(synthetic_video_path: Path, tmp_path: Path) -> None:
    out = tmp_path / "frames"
    result = runner.invoke(
        app,
        ["extract", str(synthetic_video_path), "-o", str(out), "--max-frames", "5"],
    )
    assert result.exit_code == 0
    assert len(list(out.glob("frame_*.jpg"))) == 5


def test_extract_command_every_n_frames(synthetic_video_path: Path, tmp_path: Path) -> None:
    out = tmp_path / "frames"
    result = runner.invoke(
        app,
        ["extract", str(synthetic_video_path), "-o", str(out), "-n", "30"],
    )
    assert result.exit_code == 0
    assert len(list(out.glob("frame_*.jpg"))) == 5


def test_extract_command_invalid_format(synthetic_video_path: Path, tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["extract", str(synthetic_video_path), "-o", str(tmp_path), "-f", "tiff"],
    )
    assert result.exit_code == 1


def test_extract_command_count_only_without_output(synthetic_video_path: Path) -> None:
    result = runner.invoke(
        app,
        ["extract", str(synthetic_video_path), "--max-frames", "10"],
    )
    assert result.exit_code == 0
    assert "10" in result.stdout


def test_version_callback_still_works() -> None:
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "vid2llm" in result.stdout
