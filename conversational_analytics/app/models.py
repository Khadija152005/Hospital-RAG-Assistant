from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)


class AskResponse(BaseModel):
    question: str
    answer: str
    status: Literal["success", "error"]
    sql_query: str | None = None
    rows: list[dict[str, Any]] = Field(default_factory=list)
    detail: str | None = None


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
