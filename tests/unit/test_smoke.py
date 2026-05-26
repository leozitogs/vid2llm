"""Smoke tests that verify the vid2llm package is importable and well-formed.

These tests are intentionally minimal. They exist to guarantee that the
package metadata, public surface, and exception hierarchy are wired up
correctly. Real behavior tests arrive alongside feature implementations.
"""

from __future__ import annotations


def test_package_imports() -> None:
    """The vid2llm package can be imported without side effects."""
    import vid2llm  # noqa: F401


def test_version_is_non_empty_string() -> None:
    """The package exposes a non-empty version string."""
    import vid2llm

    assert isinstance(vid2llm.__version__, str)
    assert len(vid2llm.__version__) > 0


def test_base_exception_is_subclass_of_exception() -> None:
    """The Vid2LLMError base class inherits from the built-in Exception."""
    import vid2llm

    assert issubclass(vid2llm.Vid2LLMError, Exception)
