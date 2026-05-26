"""Exception hierarchy for the vid2llm package.

All custom exceptions inherit from :class:`Vid2LLMError`. This allows callers
to catch any error raised by the library with a single ``except`` clause.
"""

from __future__ import annotations


class Vid2LLMError(Exception):
    """Base exception for all errors raised by vid2llm.

    Subclasses represent specific failure modes (backend unavailability,
    unsupported formats, extraction failures, provider errors). Callers
    that want to catch any vid2llm error should catch this base class.
    """
