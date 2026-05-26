"""Tests for the vid2llm exception hierarchy."""

from __future__ import annotations

import pytest

from vid2llm.exceptions import (
    BackendError,
    BackendNotAvailableError,
    ConfigurationError,
    ExtractionError,
    InvalidVideoError,
    NoBackendAvailableError,
    UnsupportedFormatError,
    Vid2LLMError,
)

ALL_EXCEPTIONS = [
    BackendError,
    BackendNotAvailableError,
    NoBackendAvailableError,
    ExtractionError,
    UnsupportedFormatError,
    InvalidVideoError,
    ConfigurationError,
]


@pytest.mark.parametrize("exc_cls", ALL_EXCEPTIONS)
def test_every_exception_inherits_from_base(exc_cls: type[Exception]) -> None:
    assert issubclass(exc_cls, Vid2LLMError)


def test_backend_subclasses_inherit_from_backend_error() -> None:
    assert issubclass(BackendNotAvailableError, BackendError)
    assert issubclass(NoBackendAvailableError, BackendError)


def test_backend_not_available_is_catchable_as_base() -> None:
    with pytest.raises(Vid2LLMError):
        raise BackendNotAvailableError("opencv")


def test_extraction_error_is_not_a_backend_error() -> None:
    assert not issubclass(ExtractionError, BackendError)
