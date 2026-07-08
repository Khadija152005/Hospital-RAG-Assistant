from __future__ import annotations

import re


class UnsafeSqlError(ValueError):
    """Raised when generated SQL violates safety rules."""


_FORBIDDEN_KEYWORDS = ("insert", "update", "delete", "drop", "alter", "create", "truncate", "grant", "revoke")
_CODE_FENCE_RE = re.compile(r"^```(?:sql)?\s*(.*?)\s*```$", re.IGNORECASE | re.DOTALL)


def _normalize_sql(sql: str) -> str:
    candidate = sql.strip()
    code_fence_match = _CODE_FENCE_RE.match(candidate)
    if code_fence_match:
        candidate = code_fence_match.group(1).strip()
    return candidate


def validate_sql(sql: str) -> str:
    candidate = _normalize_sql(sql)
    if not candidate:
        raise UnsafeSqlError("Unsafe SQL operation detected and blocked.")

    if ";" in candidate:
        raise UnsafeSqlError("Unsafe SQL operation detected and blocked.")

    lowered = candidate.lower().lstrip()
    if not lowered.startswith("select"):
        raise UnsafeSqlError("Unsafe SQL operation detected and blocked.")

    for keyword in _FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{keyword}\b", lowered, flags=re.IGNORECASE):
            raise UnsafeSqlError("Unsafe SQL operation detected and blocked.")

    return candidate
