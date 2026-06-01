"""Frame serialization to disk using Pillow.

Converts raw numpy pixel arrays from any backend into image files. BGR
frames are converted to RGB before encoding so the output is correct
regardless of which backend produced the frame.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import PIL.Image

from vid2llm.exceptions import UnsupportedFormatError

if TYPE_CHECKING:
    from pathlib import Path

    from numpy.typing import NDArray

    from vid2llm.core.types import Frame, ImageFormat

_FORMAT_MAP: dict[str, tuple[str, str]] = {
    "jpg": ("JPEG", "jpg"),
    "png": ("PNG", "png"),
    "webp": ("WEBP", "webp"),
}


def extension_for(image_format: ImageFormat) -> str:
    """Return the file extension for an image format.

    Args:
        image_format: One of the supported ImageFormat literals.

    Returns:
        The corresponding file extension string without a leading dot.
    """
    return _FORMAT_MAP[image_format][1]


def save_frame(frame: Frame, output_dir: Path, image_format: ImageFormat) -> Path:
    """Serialize a single frame to disk and return the written path.

    Converts BGR frames to RGB before encoding so colors are correct
    regardless of which backend produced the frame.

    Args:
        frame: The frame to serialize.
        output_dir: Destination directory. Created if missing.
        image_format: One of the supported ImageFormat literals.

    Returns:
        The path of the written image file.

    Raises:
        UnsupportedFormatError: If image_format is not a recognized format.
    """
    if image_format not in _FORMAT_MAP:
        raise UnsupportedFormatError(f"Unsupported image format: {image_format!r}")
    pillow_format, ext = _FORMAT_MAP[image_format]

    output_dir.mkdir(parents=True, exist_ok=True)

    if frame.color_space == "bgr":
        rgb: NDArray[np.uint8] = np.ascontiguousarray(frame.image[:, :, ::-1])
    else:
        rgb = frame.image

    image = PIL.Image.fromarray(rgb)
    filename = f"frame_{frame.index:06d}.{ext}"
    path = output_dir / filename
    image.save(path, format=pillow_format)
    return path
