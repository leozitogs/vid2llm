# vid2llm

Extract frames from any video and feed them to multimodal language models.

[![PyPI](https://img.shields.io/pypi/v/vid2llm.svg)](https://pypi.org/project/vid2llm/) [![Python](https://img.shields.io/pypi/pyversions/vid2llm.svg)](https://pypi.org/project/vid2llm/) [![CI](https://github.com/leozitogs/vid2llm/actions/workflows/ci.yml/badge.svg)](https://github.com/leozitogs/vid2llm/actions/workflows/ci.yml) [![codecov](https://codecov.io/gh/leozitogs/vid2llm/graph/badge.svg?token=VPD6WVUCEM)](https://codecov.io/gh/leozitogs/vid2llm) [![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

Multimodal language models consume images, not video. Getting the right frames out of a video - without writing decoder boilerplate or dealing with color space surprises - is the friction vid2llm removes. It provides a small, typed toolkit that picks the best available decode backend automatically, streams frames lazily, and saves them to disk in formats that providers can consume directly.

The package is early but functional. v0.1.0 covers frame extraction across three backends with a streaming Python API and a CLI. Smart sampling strategies and provider adapters come in later releases.

> **v0.1.0 - alpha.** The frame extraction core, CLI, and three backends are stable and tested. Scene detection, OCR, and provider adapters are on the roadmap and not yet available.

## Features

- **Three decode backends** - OpenCV, PyAV, and the ffmpeg binary - with automatic selection by availability.
- **Flexible sampling** - keep every Nth frame, cap the total count, restrict to a time window, or combine all three.
- **Streaming Python API** - `extract_frames` yields frames lazily with no full-video memory load; `extract_to_list` collects them when convenient.
- **Disk serialization** - save frames as JPEG, PNG, or WebP; BGR output from OpenCV is converted to RGB automatically before encoding.
- **Fully typed** - ships `py.typed`, passes `mypy --strict`, tested on Linux and Windows across Python 3.11, 3.12, and 3.13.

## Installation

Install the base package:

```bash
pip install vid2llm
```

A backend is required to decode video. Install at least one:

```bash
pip install vid2llm[cv]    # OpenCV - fastest seek on most formats
pip install vid2llm[pyav]  # PyAV - accurate timestamps
pip install vid2llm[all]   # both OpenCV and PyAV
```

The ffmpeg backend has no Python extra - install the `ffmpeg` binary system-wide
(`apt install ffmpeg`, `brew install ffmpeg`, `winget install Gyan.FFmpeg`, etc.)
and it is detected automatically.

If no backend is available, vid2llm raises `NoBackendAvailableError` with clear
instructions on what to install.

## Quick start: CLI

Inspect a video without decoding any frames:

```bash
vid2llm probe sample.mp4
```

```
File:        sample.mp4
Duration:    0:10.6 (10.6s)
Codec:       h264
FPS:         25.00
Frames:      266
Size:        0.7 MB
Backend:     opencv
```

Extract one frame every 30 to a directory:

```bash
vid2llm extract sample.mp4 --output-dir frames/ --every-n-frames 30
```

```
Extracted 5 frame(s) to frames in 0.12s via opencv. 5 file(s), 0.2 MB.
```

More options:

```bash
# Keep at most 10 frames from the entire video.
vid2llm extract sample.mp4 -o frames/ --max-frames 10

# Extract only the 2-second to 6-second window and save as PNG.
vid2llm extract sample.mp4 -o frames/ --start 2.0 --end 6.0 --format png

# Force a specific backend.
vid2llm extract sample.mp4 -o frames/ --backend pyav
```

Output files are named `frame_000000.jpg` through `frame_NNNNNN.jpg`, where the
number is the source frame index zero-padded to six digits.

## Quick start: Python API

**Stream frames** (memory-efficient for long videos):

```python
from vid2llm import ExtractionConfig, extract_frames

config = ExtractionConfig(every_n_frames=30, max_frames=50)

for frame in extract_frames("video.mp4", config):
    # frame.image: numpy uint8 array, shape (H, W, 3)
    # frame.color_space: "bgr" or "rgb" depending on the backend
    # frame.index: source frame index (zero-based)
    # frame.timestamp_seconds: presentation timestamp
    print(frame.index, frame.timestamp_seconds, frame.image.shape)
```

**Save frames to disk** while streaming:

```python
from vid2llm import ExtractionConfig, extract_frames

config = ExtractionConfig(every_n_frames=5, image_format="png")

for frame in extract_frames("video.mp4", config, output_dir="frames/"):
    # frames/frame_000000.png, frames/frame_000005.png, ...
    # BGR frames from OpenCV are converted to RGB before saving.
    pass
```

**Collect all frames** and inspect metadata:

```python
from vid2llm import ExtractionConfig, ExtractionResult, extract_to_list

config = ExtractionConfig(every_n_frames=30)
result: ExtractionResult = extract_to_list("video.mp4", config)

print(result.backend_used)           # "opencv"
print(result.frames_yielded)         # number of frames returned
print(result.metadata.fps)           # 25.0
print(result.metadata.frame_count)   # 266
print(result.metadata.codec)         # "h264"
print(result.metadata.width, result.metadata.height)

for frame in result.frames:
    arr = frame.image  # numpy uint8 array, shape (H, W, 3)
```

**Probe metadata directly** or force a backend:

```python
from pathlib import Path
from vid2llm import list_available_backends, select_backend

print(list_available_backends())  # e.g. ["opencv", "pyav"]

backend = select_backend("pyav")  # or None to auto-select
meta = backend.probe(Path("video.mp4"))
print(meta.fps, meta.duration_seconds, meta.codec)
```

## Backends

| Backend | Install extra | Color space | Notes |
|---------|---------------|-------------|-------|
| OpenCV | `vid2llm[cv]` | BGR | Fastest seek on most formats |
| PyAV | `vid2llm[pyav]` | RGB | Accurate timestamps |
| ffmpeg | (none) | RGB | Universal fallback; needs `ffmpeg` binary on PATH |

vid2llm tries backends in order: OpenCV, PyAV, ffmpeg. Pass `backend="opencv"`
(Python) or `--backend opencv` (CLI) to force a specific one.

The `frame.color_space` field tells you which channel ordering the backend used
(`"bgr"` or `"rgb"`). When saving to disk, the encoder converts BGR to RGB
automatically so output files are always correct regardless of backend.

## Configuration reference

`ExtractionConfig` is a frozen dataclass. All fields have defaults, so
`ExtractionConfig()` is always valid and extracts every frame.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `every_n_frames` | `int` | `1` | Keep one frame per N decoded. Must be >= 1. |
| `max_frames` | `int \| None` | `None` | Hard cap on frames returned. |
| `start_time_seconds` | `float` | `0.0` | Skip frames before this timestamp (seconds). |
| `end_time_seconds` | `float \| None` | `None` | Stop after this timestamp. `None` runs to end. |
| `image_format` | `"jpg" \| "png" \| "webp"` | `"jpg"` | Output format when saving frames to disk. |

## Roadmap

The following capabilities are **planned and not yet implemented**:

- Scene-aware sampling - detect scene changes to extract representative key frames.
- Motion-based sampling - skip redundant frames based on inter-frame difference.
- OCR extraction - read text from frames and attach it to `Frame` objects.
- Object detection - annotate frames with detected bounding boxes and labels.
- Provider SDK adapters - format frames for direct use in multimodal API calls.
- Token and cost estimation - estimate provider token counts before sending a request.

These are intentions, not commitments with delivery dates.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full development workflow. The
short version: install with `uv`, run `ruff`, `mypy --strict`, and `pytest`
before every PR. Coverage must stay at or above 80 percent.

## License

Apache License 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
