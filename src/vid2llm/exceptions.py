"""Exception hierarchy for the vid2llm package.

All custom exceptions inherit from :class:`Vid2LLMError`. This allows callers
to catch any error raised by the library with a single ``except`` clause.

The hierarchy is intentionally shallow (no more than two levels deep). Backend
related failures share a common :class:`BackendError` base so consumers can
distinguish problems originating in the extraction backend from problems with
the input video or the requested configuration.
"""

from __future__ import annotations


class Vid2LLMError(Exception):
    """Base exception for all errors raised by vid2llm.

    Subclasses represent specific failure modes. Callers that want to catch
    any vid2llm error should catch this base class.
    """


class BackendError(Vid2LLMError):
    """Base class for failures related to frame extraction backends.

    Raised by code that selects, probes, or operates a backend before frame
    extraction begins. Failures that occur mid extraction are reported as
    :class:`ExtractionError` instead.
    """


class BackendNotAvailableError(BackendError):
    """Raised when a specifically requested backend cannot be used.

    The backend is known to the library but its underlying dependency is not
    installed, not importable, or otherwise not usable in the current
    environment.
    """


class NoBackendAvailableError(BackendError):
    """Raised when no backend at all can be used in the current environment.

    Returned by the selector when every registered backend reports itself as
    unavailable. The user must install at least one supported backend.
    """


class ExtractionError(Vid2LLMError):
    """Raised when frame extraction fails after it has started.

    Represents a mid process failure such as a backend error while decoding
    frames, an unexpected end of stream, or an I/O failure during reading.
    Distinct from :class:`BackendError`, which covers problems detected
    before extraction begins.
    """


class UnsupportedFormatError(Vid2LLMError):
    """Raised when the input file's container or codec is not recognized.

    The file is readable but no available backend can decode it.
    """


class InvalidVideoError(Vid2LLMError):
    """Raised when the input file exists but is not a valid video.

    Covers corrupted files, empty files, and files whose headers cannot be
    parsed by any available backend.
    """


class ConfigurationError(Vid2LLMError):
    """Raised when an :class:`ExtractionConfig` or related setting is invalid.

    Raised early, before any backend is invoked, to surface user errors with
    clear messages instead of letting them surface as backend failures.
    """
