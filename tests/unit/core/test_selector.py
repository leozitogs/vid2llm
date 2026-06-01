"""Tests for the runtime backend selector."""

from __future__ import annotations

import pytest

from vid2llm.core import selector
from vid2llm.core.selector import (
    BACKEND_PREFERENCE_ORDER,
    list_available_backends,
    select_backend,
)
from vid2llm.exceptions import (
    BackendNotAvailableError,
    ConfigurationError,
    NoBackendAvailableError,
)


def test_list_available_backends_returns_subset_of_known():
    result = list_available_backends()

    for name in result:
        assert name in BACKEND_PREFERENCE_ORDER
    assert len(result) == len(set(result))
    expected_order = [name for name in BACKEND_PREFERENCE_ORDER if name in result]
    assert result == expected_order


def test_select_backend_no_preference_returns_first_available(monkeypatch):
    availability = {"opencv": False, "pyav": True, "ffmpeg": True}
    monkeypatch.setattr(
        selector,
        "_is_backend_available",
        lambda name: availability.get(name, False),
    )

    backend = select_backend()

    assert backend.name == "pyav"


def test_select_backend_with_valid_preference(monkeypatch):
    availability = {"opencv": False, "pyav": True, "ffmpeg": False}
    monkeypatch.setattr(
        selector,
        "_is_backend_available",
        lambda name: availability.get(name, False),
    )

    backend = select_backend("pyav")

    assert backend.name == "pyav"


def test_select_backend_with_unavailable_preference_raises(monkeypatch):
    availability = {"opencv": False, "pyav": True, "ffmpeg": True}
    monkeypatch.setattr(
        selector,
        "_is_backend_available",
        lambda name: availability.get(name, False),
    )

    with pytest.raises(BackendNotAvailableError):
        select_backend("opencv")


def test_select_backend_with_unknown_name_raises_configuration_error():
    with pytest.raises(ConfigurationError):
        select_backend("ffmoog")


def test_select_backend_no_available_raises_no_backend(monkeypatch):
    monkeypatch.setattr(selector, "_is_backend_available", lambda name: False)

    with pytest.raises(NoBackendAvailableError):
        select_backend()
