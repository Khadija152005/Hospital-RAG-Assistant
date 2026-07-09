from __future__ import annotations

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
    """
    Conversational Analytics Service
    """

    def __init__(self, settings: AppSettings | None = None) -> None:
        self.settings = settings or AppSettings.from_env()

        setup_logging(self.settings.log_level)

        self.logger = logging.getLogger(
            "conversational_analytics.service"
        )

        self.engine = self._initialize_engine(self.settings)

        self._schema_context: str | None = None

        self.llm_generator = LLMSQLGenerator(self.settings)

    @staticmethod
    def _initialize_engine(settings: AppSettings) -> Engine:

        engine = create_engine_from_settings(settings)

        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except SQLAlchemyError as exc:
            raise DatabaseConnectionError(
                "Database connection failed."
            ) from exc

        return engine

    @staticmethod
    def _build_schema_context(database: SQLDatabase) -> str:

        table_info = database.get_table_info()

        usable_tables = ", ".join(database.get_usable_table_names())

        return (
            f"Usable tables: {usable_tables}\n\n"
            f"Table details:\n{table_info}"
        )

    def _get_schema_context(self) -> str:

        if self._schema_context is not None:
            return self._schema_context

        try:

            # استخدم الـ Engine الحالي بدل from_uri
            database = SQLDatabase(engine=self.engine)

            self._schema_context = self._build_schema_context(database)

            return self._schema_context

        except Exception as exc:

            self.logger.warning(
                "Schema reflection failed.",
                exc_info=exc,
            )

            self._schema_context = (
                "Schema context unavailable. "
                "Generate a PostgreSQL SELECT query."
            )

            return self._schema_context

    @staticmethod
    def _extract_sql(candidate: str) -> str:

        candidate = candidate.strip()

        match = re.search(
            r"```(?:sql)?\s*(.*?)\s*```",
            candidate,
            re.S | re.I,
        )

        if match:
            candidate = match.group(1).strip()

        match = re.search(
            r"(?is)(select\b.*)",
            candidate,
        )

        if match:
            candidate = match.group(1)

        return candidate.rstrip(";").strip()

    @staticmethod
    def _is_rate_limit_error(exc: Exception) -> bool:

        message = str(exc).lower()

        return any(
            x in message
            for x in (
                "429",
                "quota",
                "rate limit",
                "resource_exhausted",
                "too many requests",
            )
        )

    def _generate_sql(
        self,
        question: str,
        schema_context: str,
    ) -> str:

        sql = self.llm_generator.generate_sql(
            question,
            schema_context,
        )

        if not sql:
            raise InvalidSqlError(
                "LLM generated empty SQL."
            )

        return validate_sql(sql)

    def _execute_sql(
        self,
        sql_query: str,
    ) -> list[dict[str, Any]]:

        try:

            with self.engine.connect() as conn:

                result = conn.execute(text(sql_query))

                return [
                    dict(row)
                    for row in result.mappings().fetchmany(
                        self.settings.max_result_rows
                    )
                ]

        except SQLAlchemyError as exc:

            raise DatabaseConnectionError(
                "Database connection failed."
            ) from exc

    @staticmethod
    def _fallback_answer(
        rows: list[dict[str, Any]]
    ) -> str:

        if not rows:
            return "No matching records were found."

        if len(rows) == 1:
            return ", ".join(
                f"{k}={v}"
                for k, v in rows[0].items()
            )

        return f"{len(rows)} rows returned."

    def _summarize_answer(
        self,
        question: str,
        sql_query: str,
        rows: list[dict[str, Any]],
    ) -> str:

        return self._fallback_answer(rows)

    def ask_question(
        self,
        question: str,
    ) -> dict[str, Any]:

        self.logger.info(
            "Incoming analytics question",
            extra={
                "question": question,
            },
        )

        if self.settings.enable_template_router:

            template = route_question(question)

            if template is not None:

                sql = validate_sql(template.sql)

                rows = self._execute_sql(sql)

                if rows:

                    if len(rows) == 1:

                        answer = ", ".join(
                            f"{k}={v}"
                            for k, v in rows[0].items()
                        )

                    else:

                        answer = (
                            template.detail
                            or f"{len(rows)} rows returned."
                        )

                else:

                    answer = (
                        "No matching records."
                    )

                return {
                    "question": question,
                    "answer": answer,
                    "status": "success",
                    "sql_query": sql,
                    "rows": rows,
                }

        if not self.settings.enable_llm_fallback:

            raise InvalidSqlError(
                "LLM fallback disabled."
            )

        schema = self._get_schema_context()

        sql = self._generate_sql(
            question,
            schema,
        )

        rows = self._execute_sql(sql)

        answer = self._summarize_answer(
            question,
            sql,
            rows,
        )

        return {
            "question": question,
            "answer": answer,
            "status": "success",
            "sql_query": sql,
            "rows": rows,
        }
