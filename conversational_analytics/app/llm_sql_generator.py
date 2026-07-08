from __future__ import annotations

import logging
import re
import time
from typing import Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from .config import AppSettings
from .errors import GeminiRateLimitError, InvalidSqlError

logger = logging.getLogger("conversational_analytics.llm_sql_generator")


class LLMSQLGenerator:
    """Wrapper for LLM-based SQL generation with model fallback and quota handling.

    This class makes a single LLM attempt per request (with optional fallback model),
    and deliberately avoids multi-step agent loops that would consume multiple calls.
    """

    SQL_PROMPT = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a SQL generator for a PostgreSQL database. Produce exactly one SELECT statement.
Rules:
- Only return a single valid SELECT statement.
- Do not include code fences, commentary, or semicolons.
- Use the provided schema context.
""",
            ),
            ("human", "Schema: {schema_context}\nQuestion: {question}\nSQL:"),
        ]
    )

    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.logger = logger

    @staticmethod
    def _is_rate_limit_error(exc: Exception) -> bool:
        message = str(exc).lower()
        return any(k in message for k in ("resource_exhausted", "429", "quota", "rate limit", "too many requests"))

    def generate_sql(self, question: str, schema_context: str) -> str:
        # Build model list: primary then fallbacks
        models = [self.settings.gemini_model] + list(self.settings.gemini_fallback_models)
        last_exc: Exception | None = None

        for model in models:
            try:
                llm = ChatGoogleGenerativeAI(model=model, temperature=0, google_api_key=self.settings.google_api_key, max_retries=1)
                sql_raw = (self.SQL_PROMPT | llm | StrOutputParser()).invoke({"question": question, "schema_context": schema_context})
                # basic extraction
                sql = self._extract_sql(sql_raw)
                if not sql:
                    raise InvalidSqlError("Invalid SQL produced by LLM")
                return sql
            except Exception as exc:
                last_exc = exc
                if self._is_rate_limit_error(exc):
                    self.logger.warning("Model %s rate-limited: %s", model, exc)
                    # try next model once
                    continue
                # other LLM errors should not be retried here
                raise

        # If we get here, all models exhausted or rate-limited
        raise GeminiRateLimitError("The analytics service is temporarily rate-limited. Please retry shortly.") from last_exc

    @staticmethod
    def _extract_sql(candidate: str) -> str:
        text = candidate.strip()
        # strip code fences
        match = re.search(r"```(?:sql)?\s*(.*?)\s*```", text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            text = match.group(1).strip()

        select_match = re.search(r"(?is)(select\b.*)", text)
        if select_match:
            return select_match.group(1).strip().rstrip(";")
        return ""
