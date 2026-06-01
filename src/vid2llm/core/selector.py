"""Runtime selection of the best available frame extraction backend.

The selector keeps the orchestrator decoupled from any concrete backend.
At runtime it inspects which optional dependencies are installed and
returns an instantiated backend that satisfies the
:class:`vid2llm.backends.base.FrameBackend` protocol.
"""

from __future__ import annotations

import importlib.util
import shutil
from typing import TYPE_CHECKING, Final

from vid2llm.exceptions import (
    BackendNotAvailableError,
    ConfigurationError,
    NoBackendAvailableError,
)

if TYPE_CHECKING:
    from vid2llm.backends.base import FrameBackend


BACKEND_PREFERENCE_ORDER: Final[tuple[str, ...]] = ("opencv", "pyav", "ffmpeg")
"""Order in which backends are tried when no explicit preference is given."""


def _check_python_dep(module_name: str) -> bool:
    """Return whether a Python module is importable in the current environment."""
    return importlib.util.find_spec(module_name) is not None


def _is_backend_available(name: str) -> bool:
    """Return whether the backend identified by ``name`` is usable.

    Args:
        name: One of the values in :data:`BACKEND_PREFERENCE_ORDER`.

    Returns:
        ``True`` if the backend's underlying dependency is present,
        ``False`` for unknown names or missing dependencies.
    """
    if name == "opencv":
        return _check_python_dep("cv2")
    if name == "pyav":
        return _check_python_dep("av")
    if name == "ffmpeg":
        return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None
    return False


def _import_backend(name: str) -> type[FrameBackend]:
    """Import and return the backend class identified by ``name``.

    Args:
        name: One of the values in :data:`BACKEND_PREFERENCE_ORDER`.

    Returns:
        The backend class, ready to instantiate.

    Raises:
        ConfigurationError: If ``name`` is not a known backend.
    """
    if name == "opencv":
        from vid2llm.backends.opencv import OpenCVBackend

        return OpenCVBackend
    if name == "pyav":
        from vid2llm.backends.pyav import PyAVBackend

        return PyAVBackend
    if name == "ffmpeg":
        from vid2llm.backends.ffmpeg import FFmpegBackend

        return FFmpegBackend
    raise ConfigurationError(f"Unknown backend name: {name!r}")


def _install_hint(name: str) -> str:
    """Return a human-readable installation hint for an unavailable backend."""
    hints = {
        "opencv": "Install with: pip install vid2llm[cv]",
        "pyav": "Install with: pip install vid2llm[pyav]",
        "ffmpeg": (
            "Install the ffmpeg binary system-wide (apt install ffmpeg, brew install ffmpeg, etc.)."
        ),
    }
    return hints[name]


def select_backend(preference: str | None = None) -> FrameBackend:
    """Return the best available backend, optionally honoring a preference.

    Args:
        preference: Backend name to try first. One of ``"opencv"``,
            ``"pyav"``, ``"ffmpeg"``, or ``None`` to use
            :data:`BACKEND_PREFERENCE_ORDER`.

    Returns:
        An instantiated backend that satisfies the
        :class:`vid2llm.backends.base.FrameBackend` protocol.

    Raises:
        ConfigurationError: If ``preference`` is an unknown backend name.
        BackendNotAvailableError: If ``preference`` is specified but the
            requested backend is unavailable.
        NoBackendAvailableError: If ``preference`` is ``None`` and no
            backend is available.
    """
    if preference is not None:
        if preference not in BACKEND_PREFERENCE_ORDER:
            raise ConfigurationError(
                f"Unknown backend: {preference!r}. Valid options: {list(BACKEND_PREFERENCE_ORDER)}."
            )
        if not _is_backend_available(preference):
            raise BackendNotAvailableError(
                f"Backend {preference!r} is not available. {_install_hint(preference)}"
            )
        return _import_backend(preference)()

    for name in BACKEND_PREFERENCE_ORDER:
        if _is_backend_available(name):
            return _import_backend(name)()

    raise NoBackendAvailableError(
        "No backend is available. Install one with: "
        "pip install vid2llm[cv] or pip install vid2llm[pyav] "
        "or install the ffmpeg binary system-wide."
    )


def list_available_backends() -> list[str]:
    """Return the names of all available backends, in preference order.

    Returns:
        A list of backend names whose availability checks succeed,
        ordered according to :data:`BACKEND_PREFERENCE_ORDER`.
    """
    return [name for name in BACKEND_PREFERENCE_ORDER if _is_backend_available(name)]
