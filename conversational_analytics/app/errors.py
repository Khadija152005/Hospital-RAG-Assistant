from __future__ import annotations


class GeminiRateLimitError(RuntimeError):
    """Raised when Gemini returns a rate-limit or quota exhaustion error."""


class InvalidSqlError(RuntimeError):
    """Raised when the model output cannot be converted into safe SQL."""
