"""Tests for the FrameBackend protocol contract."""

from __future__ import annotations

# Iterator and Path are used at runtime by the _StubBackend class methods,
# not only in type annotations. Keeping them as runtime imports.
from collections.abc import Iterator  # noqa: TC003
from pathlib import Path  # noqa: TC003

from vid2llm.backends.base import FrameBackend
from vid2llm.core.types import ExtractionConfig, Frame, VideoMetadata


class _StubBackend:
    name: str = "stub"

    @classmethod
    def is_available(cls) -> bool:
        return True

    def probe(self, path: Path) -> VideoMetadata:
        return VideoMetadata(
            path=path,
            width=0,
            height=0,
            frame_count=0,
            fps=0.0,
            duration_seconds=0.0,
            codec="",
        )

    def extract(self, path: Path, config: ExtractionConfig) -> Iterator[Frame]:
        return iter(())


class _IncompleteBackend:
    name: str = "incomplete"


def test_stub_backend_satisfies_protocol() -> None:
    backend = _StubBackend()
    assert isinstance(backend, FrameBackend)


def test_incomplete_backend_does_not_satisfy_protocol() -> None:
    backend = _IncompleteBackend()
    assert not isinstance(backend, FrameBackend)
