from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError
from langchain_community.utilities import SQLDatabase

from .config import AppSettings
from .db import DatabaseConnectionError, create_engine_from_settings
from .logging_config import setup_logging
from .sql_safety import UnsafeSqlError, validate_sql
from .errors import GeminiRateLimitError, InvalidSqlError
from .template_router import route_question
from .llm_sql_generator import LLMSQLGenerator




class ConversationalAnalyticsService:
    """Production-shaped conversational analytics service for structured hospital data.

    The LangChain SQL agent is initialized for compatibility with the current prototype,
    but the execution path uses controlled SQL generation, validation, and direct query
    execution so the raw SQL can be validated before it touches PostgreSQL.
    """

    def __init__(self, settings: AppSettings | None = None) -> None:
        self.settings = settings or AppSettings.from_env()
        setup_logging(self.settings.log_level)
        self.logger = logging.getLogger("conversational_analytics.service")

        self.engine = self._initialize_engine(self.settings)
        self._schema_context: str | None = None
        # LLM generator is used only as fallback and implemented to minimize calls
        self.llm_generator = LLMSQLGenerator(self.settings)

    @staticmethod
    def _initialize_engine(settings: AppSettings) -> Engine:
        engine = create_engine_from_settings(settings)
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
        except SQLAlchemyError as exc:
            raise DatabaseConnectionError("Database connection failed.") from exc
        return engine

    @staticmethod
    def _build_schema_context(database: SQLDatabase) -> str:
        table_info = database.get_table_info()
        usable_tables = ", ".join(database.get_usable_table_names())
        return f"Usable tables: {usable_tables}\n\nTable details:\n{table_info}"

    def _get_schema_context(self) -> str:
        if self._schema_context is not None:
            return self._schema_context

        try:
            database = SQLDatabase.from_uri(str(self.settings.database_url_object()))
            self._schema_context = self._build_schema_context(database)
            return self._schema_context
        except SQLAlchemyError as exc:
            self.logger.warning("Schema reflection failed; continuing with minimal context.", exc_info=exc)
            self._schema_context = "Schema context unavailable. Generate a simple PostgreSQL SELECT query against the available public tables."
            return self._schema_context

    @staticmethod
    def _extract_sql(candidate: str) -> str:
        text = candidate.strip()
        code_fence_match = re.search(r"```(?:sql)?\s*(.*?)\s*```", text, flags=re.IGNORECASE | re.DOTALL)
        if code_fence_match:
            text = code_fence_match.group(1).strip()

        select_match = re.search(r"(?is)(select\b.*)", text)
        if select_match:
            text = select_match.group(1).strip()

        return text.rstrip(";").strip()

    @staticmethod
    def _is_rate_limit_error(exc: Exception) -> bool:
        message = str(exc).lower()
        return any(
            marker in message
            for marker in (
                "resource_exhausted",
                "429",
                "quota",
                "rate limit",
                "too many requests",
            )
        )

    def _invoke_with_retry(self, chain: Any, payload: dict[str, Any], operation: str) -> str:
        last_error: Exception | None = None
        for attempt in range(1, self.settings.llm_max_retries + 1):
            try:
                return chain.invoke(payload)
            except Exception as exc:  # noqa: BLE001 - external SDK exceptions are normalized here.
                last_error = exc
                if self._is_rate_limit_error(exc) and attempt < self.settings.llm_max_retries:
                    time.sleep(2 ** (attempt - 1))
                    continue
                if self._is_rate_limit_error(exc):
                    raise GeminiRateLimitError(
                        "The analytics service is temporarily rate-limited. Please retry shortly."
                    ) from exc
                raise
        if last_error is not None:
            raise last_error
        raise RuntimeError(f"{operation} failed without an explicit error.")

    def _generate_sql(self, question: str, schema_context: str) -> str:
        # Use the LLM SQL generator wrapper to ensure single-call behavior and fallback handling
        sql = self.llm_generator.generate_sql(question, schema_context)
        if not sql:
            raise InvalidSqlError("Invalid SQL generated by the analytics service.")
        return validate_sql(sql)

    def _execute_sql(self, sql_query: str) -> list[dict[str, Any]]:
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text(sql_query))
                rows = [dict(row) for row in result.mappings().fetchmany(self.settings.max_result_rows)]
                return rows
        except SQLAlchemyError as exc:
            raise DatabaseConnectionError("Database connection failed.") from exc

    @staticmethod
    def _fallback_answer(rows: list[dict[str, Any]]) -> str:
        if not rows:
            return "No matching records were found for this question."
        if len(rows) == 1:
            items = ", ".join(f"{key}={value}" for key, value in rows[0].items())
            return f"The query returned one matching record: {items}."
        return f"The query returned {len(rows)} matching records."

    def _summarize_answer(self, question: str, sql_query: str, rows: list[dict[str, Any]]) -> str:
        if not rows:
            return "No matching records were found for this question."
        # Return a deterministic fallback summary to avoid extra LLM calls and simplify behavior.
        return self._fallback_answer(rows)

    def ask_question(self, question: str) -> dict[str, Any]:
        self.logger.info("Incoming analytics question", extra={"question": question, "status": "received"})
        # First, attempt deterministic template routing if enabled
        if self.settings.enable_template_router:
            template = route_question(question)
            if template is not None:
                self.logger.info("Routed question to template", extra={"question": question, "route": "template"})
                sql_query = validate_sql(template.sql)
                rows = self._execute_sql(sql_query)
                # Summarize deterministically for simple templates
                if not rows:
                    answer = "No matching records were found for this question."
                else:
                    # simple human-readable answer: if single row, show values; else count
                    if len(rows) == 1:
                        vals = ", ".join(f"{k}={v}" for k, v in rows[0].items())
                        answer = f"{template.detail or 'Result'}: {vals}."
                    else:
                        answer = template.detail or f"Returned {len(rows)} rows."
                status = "success"

                self.logger.info(
                    "Analytics question completed (template)",
                    extra={"question": question, "status": status, "sql_query": sql_query, "rows_count": len(rows)},
                )
                return {"question": question, "answer": answer, "status": status, "sql_query": sql_query, "rows": rows}

        # Fallback to LLM if allowed
        if not self.settings.enable_llm_fallback:
            raise InvalidSqlError("Question not supported by deterministic templates and LLM fallback is disabled.")

        try:
            schema_context = self._get_schema_context()
            sql_query = self._generate_sql(question, schema_context)
        except GeminiRateLimitError:
            raise
        rows = self._execute_sql(sql_query)
        answer = self._summarize_answer(question, sql_query, rows)
        status = "success"

        self.logger.info(
            "Analytics question completed",
            extra={
                "question": question,
                "status": status,
                "sql_query": sql_query,
                "rows_count": len(rows),
            },
        )
        return {
            "question": question,
            "answer": answer,
            "status": status,
            "sql_query": sql_query,
            "rows": rows,
        }
