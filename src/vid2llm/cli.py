"""Command-line interface entry point for vid2llm.

This module exposes a Typer application that is registered as the
``vid2llm`` console script in ``pyproject.toml``.
"""

from __future__ import annotations

import time
from pathlib import Path  # noqa: TC003 - typer inspects annotations at runtime via get_type_hints
from typing import TYPE_CHECKING, cast

import typer
from rich.console import Console
from rich.progress import BarColumn, MofNCompleteColumn, Progress, SpinnerColumn, TextColumn

from vid2llm import __version__
from vid2llm.core.extractor import extract_frames
from vid2llm.core.selector import select_backend
from vid2llm.core.types import ExtractionConfig
from vid2llm.exceptions import (
    BackendNotAvailableError,
    ConfigurationError,
    InvalidVideoError,
    NoBackendAvailableError,
)

if TYPE_CHECKING:
    from vid2llm.core.types import ImageFormat, VideoMetadata

app = typer.Typer(
    name="vid2llm",
    help="Turn any video into LLM-ready frames.",
    no_args_is_help=False,
    add_completion=False,
)

_console = Console()

_VALID_FORMATS = ("jpg", "png", "webp")


def _format_duration(seconds: float) -> str:
    """Return a human-readable duration string in M:SS.s format.

    Args:
        seconds: Duration in seconds.

    Returns:
        Formatted string such as ``"1:23.4"``.
    """
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes}:{secs:04.1f}"


def _format_size_mb(num_bytes: int) -> str:
    """Return a human-readable file size string in megabytes.

    Args:
        num_bytes: Size in bytes.

    Returns:
        Formatted string such as ``"142.3 MB"``.
    """
    return f"{num_bytes / (1024 * 1024):.1f} MB"


def _estimate_total(metadata: VideoMetadata, config: ExtractionConfig) -> int | None:
    """Estimate the post-filter frame count for a progress bar.

    Args:
        metadata: Video metadata from a probe call.
        config: The extraction configuration that will be applied.

    Returns:
        An estimated frame count, or None when the total is unknown.
    """
    if metadata.frame_count == 0:
        return None
    duration = metadata.duration_seconds
    start = min(config.start_time_seconds, duration)
    end = (
        min(config.end_time_seconds, duration) if config.end_time_seconds is not None else duration
    )
    window = max(0.0, end - start)
    if duration > 0 and window < duration:
        fraction = window / duration
        total = round(metadata.frame_count * fraction)
    else:
        total = metadata.frame_count
    total = max(1, (total + config.every_n_frames - 1) // config.every_n_frames)
    if config.max_frames is not None:
        total = min(total, config.max_frames)
    return total


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """Print the package banner when no subcommand is provided.

    Args:
        ctx: Typer context, used to detect whether a subcommand was invoked.
    """
    if ctx.invoked_subcommand is not None:
        return

    _console.print(f"[bold]vid2llm[/bold] [dim]v{__version__}[/dim]")
    _console.print("[yellow]no commands available yet, see ROADMAP[/yellow]")


@app.command()
def extract(
    video_path: Path = typer.Argument(..., help="Path to the source video."),
    output_dir: Path | None = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Directory to save extracted frames. Omit to count without saving.",
    ),
    every_n_frames: int = typer.Option(
        1, "--every-n-frames", "-n", help="Keep one frame every N decoded frames."
    ),
    max_frames: int | None = typer.Option(
        None, "--max-frames", help="Maximum number of frames to extract."
    ),
    image_format: str = typer.Option(
        "jpg", "--format", "-f", help="Output image format: jpg, png, or webp."
    ),
    start: float = typer.Option(0.0, "--start", help="Start time in seconds."),
    end: float | None = typer.Option(None, "--end", help="End time in seconds."),
    backend: str | None = typer.Option(
        None, "--backend", help="Force a backend: opencv, pyav, or ffmpeg."
    ),
) -> None:
    """Extract frames from a video, with optional smart sampling."""
    if image_format not in _VALID_FORMATS:
        _console.print(f"[red]Invalid format {image_format!r}. Choose from: jpg, png, webp.[/red]")
        raise typer.Exit(code=1)

    try:
        config = ExtractionConfig(
            every_n_frames=every_n_frames,
            max_frames=max_frames,
            start_time_seconds=start,
            end_time_seconds=end,
            image_format=cast("ImageFormat", image_format),
        )
    except ValueError as exc:
        _console.print(f"[red]Invalid configuration: {exc}[/red]")
        raise typer.Exit(code=1) from exc

    try:
        selected = select_backend(backend)
    except (NoBackendAvailableError, BackendNotAvailableError, ConfigurationError) as exc:
        _console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    # fast-probe optimization candidate: probe() triggers a full frame scan on opencv
    try:
        metadata = selected.probe(video_path)
    except FileNotFoundError:
        _console.print(f"[red]File not found: {video_path}[/red]")
        raise typer.Exit(code=1) from None
    except InvalidVideoError as exc:
        _console.print(f"[red]Invalid video: {exc}[/red]")
        raise typer.Exit(code=1) from exc

    total = _estimate_total(metadata, config)

    frame_count = 0
    start_ts = time.perf_counter()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        transient=True,
    ) as progress:
        task = progress.add_task("Extracting frames...", total=total)
        for _frame in extract_frames(video_path, config, backend, output_dir):
            frame_count += 1
            progress.advance(task)

    elapsed = time.perf_counter() - start_ts

    if output_dir is not None:
        ext = image_format
        written = sorted(output_dir.glob(f"frame_*.{ext}"))
        total_bytes = sum(f.stat().st_size for f in written)
        _console.print(
            f"Extracted [bold]{frame_count}[/bold] frame(s) to [cyan]{output_dir}[/cyan] "
            f"in {elapsed:.2f}s via [green]{selected.name}[/green]. "
            f"{len(written)} file(s), {_format_size_mb(total_bytes)}."
        )
    else:
        _console.print(
            f"Counted [bold]{frame_count}[/bold] frame(s) in {elapsed:.2f}s "
            f"via [green]{selected.name}[/green] (no files written)."
        )


@app.command()
def probe(
    video_path: Path = typer.Argument(..., help="Path to the source video."),
    backend: str | None = typer.Option(
        None, "--backend", help="Force a backend: opencv, pyav, or ffmpeg."
    ),
) -> None:
    """Show video metadata without extracting frames."""
    try:
        selected = select_backend(backend)
    except (NoBackendAvailableError, BackendNotAvailableError, ConfigurationError) as exc:
        _console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    try:
        metadata = selected.probe(video_path)
    except FileNotFoundError:
        _console.print(f"[red]File not found: {video_path}[/red]")
        raise typer.Exit(code=1) from None
    except InvalidVideoError as exc:
        _console.print(f"[red]Invalid video: {exc}[/red]")
        raise typer.Exit(code=1) from exc

    file_size = video_path.stat().st_size
    duration_str = _format_duration(metadata.duration_seconds)

    _console.print(f"{'File:':<12} {video_path}")
    _console.print(f"{'Duration:':<12} {duration_str} ({metadata.duration_seconds:.1f}s)")
    _console.print(f"{'Codec:':<12} {metadata.codec}")
    _console.print(f"{'FPS:':<12} {metadata.fps:.2f}")
    _console.print(f"{'Frames:':<12} {metadata.frame_count}")
    _console.print(f"{'Size:':<12} {_format_size_mb(file_size)}")
    _console.print(f"{'Backend:':<12} {selected.name}")
