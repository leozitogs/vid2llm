from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import PIL.Image
import pytest

from vid2llm.core.encoder import save_frame
from vid2llm.core.types import Frame
from vid2llm.exceptions import UnsupportedFormatError

if TYPE_CHECKING:
    from pathlib import Path


def _make_frame(
    index: int = 0,
    color_space: str = "rgb",
    pixel: tuple[int, int, int] = (100, 150, 200),
) -> Frame:
    image = np.zeros((4, 4, 3), dtype=np.uint8)
    image[0, 0] = pixel
    return Frame(
        index=index,
        timestamp_seconds=float(index) * 0.033,
        image=image,
        color_space=color_space,  # type: ignore[arg-type]
        source_backend="test",
    )


def test_save_frame_writes_jpg(tmp_path: Path) -> None:
    frame = _make_frame(index=7)
    path = save_frame(frame, tmp_path, "jpg")
    assert path.name == "frame_000007.jpg"
    assert path.exists()
    with PIL.Image.open(path):
        pass


def test_save_frame_writes_png(tmp_path: Path) -> None:
    frame = _make_frame(index=0)
    path = save_frame(frame, tmp_path, "png")
    assert path.name == "frame_000000.png"
    assert path.exists()
    with PIL.Image.open(path):
        pass


def test_save_frame_writes_webp(tmp_path: Path) -> None:
    frame = _make_frame(index=1)
    path = save_frame(frame, tmp_path, "webp")
    assert path.name == "frame_000001.webp"
    assert path.exists()
    with PIL.Image.open(path):
        pass


def test_save_frame_creates_output_dir(tmp_path: Path) -> None:
    nested = tmp_path / "a" / "b"
    frame = _make_frame(index=0)
    path = save_frame(frame, nested, "png")
    assert path.exists()
    assert path.name == "frame_000000.png"


def test_save_frame_bgr_is_converted(tmp_path: Path) -> None:
    # BGR (255, 0, 0) is pure blue; after channel reversal it becomes RGB (0, 0, 255).
    frame = _make_frame(index=0, color_space="bgr", pixel=(255, 0, 0))
    path = save_frame(frame, tmp_path, "png")
    with PIL.Image.open(path) as img:
        pixel = img.convert("RGB").getpixel((0, 0))
    assert pixel == (0, 0, 255)


def test_save_frame_rgb_is_not_swapped(tmp_path: Path) -> None:
    frame = _make_frame(index=0, color_space="rgb", pixel=(255, 0, 0))
    path = save_frame(frame, tmp_path, "png")
    with PIL.Image.open(path) as img:
        pixel = img.convert("RGB").getpixel((0, 0))
    assert pixel == (255, 0, 0)


def test_save_frame_unsupported_format_raises(tmp_path: Path) -> None:
    frame = _make_frame()
    with pytest.raises(UnsupportedFormatError):
        save_frame(frame, tmp_path, "tiff")  # type: ignore[arg-type]
