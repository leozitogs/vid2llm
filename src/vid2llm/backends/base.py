"""Protocol that every frame extraction backend must satisfy.

vid2llm uses :class:`typing.Protocol` rather than an abstract base class for
its backend contract. The structural typing approach decouples the
orchestrator from any specific inheritance hierarchy: a backend is anything
that exposes the right attributes and methods, regardless of where it lives
or what it inherits from. This makes it straightforward for third parties to
ship their own backends as separate distributions.

The orchestrator (:mod:`vid2llm.core`) consumes backends through this
protocol exclusively. It never imports a concrete backend module directly;
instead a selector resolves the best available backend at runtime and hands
it to the orchestrator.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from vid2llm.core.types import ExtractionConfig, Frame, VideoMetadata


@runtime_checkable
class FrameBackend(Protocol):
    """Structural contract for a frame extraction backend.

    Attributes:
        name: Stable identifier of the backend. Lowercase, no spaces. Used in
            error messages, logs, and the ``source_backend`` field of
            produced frames.
    """

    name: str

    @classmethod
    def is_available(cls) -> bool:
        """Report whether the backend can be used in the current environment.

        For backends that wrap a Python library this typically attempts to
        import the dependency. For the ffmpeg backend this checks whether
        the ``ffmpeg`` binary is discoverable on ``PATH``.

        Returns:
            ``True`` if the backend is usable, ``False`` otherwise.
        """
        ...

    def probe(self, path: Path) -> VideoMetadata:
        """Read static metadata from a video without decoding frames.

        Args:
            path: Filesystem path to the source video.

        Returns:
            Metadata describing the video.

        Raises:
            UnsupportedFormatError: The file format is not recognized.
            InvalidVideoError: The file exists but is corrupted or empty.
        """
        ...

    def extract(self, path: Path, config: ExtractionConfig) -> Iterator[Frame]:
        """Yield frames from a video lazily according to ``config``.

        Implementations must stream frames rather than building the full list
        in memory, so that long videos can be processed without exhausting
        system memory.

        Args:
            path: Filesystem path to the source video.
            config: Extraction parameters.

        Yields:
            Frames decoded from the source, already filtered by the config's
            time window and sampling rate.

        Raises:
            ExtractionError: A failure occurred after extraction started.
        """
        ...
