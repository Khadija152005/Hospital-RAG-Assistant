from __future__ import annotations

import logging
import os
from functools import lru_cache

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import JSONResponse

from .analytics_service import (
    ConversationalAnalyticsService,
    DatabaseConnectionError,
    GeminiRateLimitError,
    InvalidSqlError,
)
from .config import get_settings
from .logging_config import setup_logging
from .models import AskRequest, AskResponse, HealthResponse
from .sql_safety import UnsafeSqlError

setup_logging(os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("conversational_analytics.api")


@lru_cache(maxsize=1)
def get_analytics_service() -> ConversationalAnalyticsService:
    settings = get_settings()
    return ConversationalAnalyticsService(settings)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Conversational Analytics Module",
        version="1.0.0",
        description="Natural-language analytics over structured hospital data in PostgreSQL.",
    )

    @app.exception_handler(UnsafeSqlError)
    async def handle_unsafe_sql(_, exc: UnsafeSqlError) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)})

    @app.exception_handler(GeminiRateLimitError)
    async def handle_rate_limit(_, exc: GeminiRateLimitError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "The analytics service is temporarily rate-limited. Please retry shortly."},
        )

    @app.exception_handler(DatabaseConnectionError)
    async def handle_database_error(_, exc: DatabaseConnectionError) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content={"detail": str(exc)})

    @app.exception_handler(InvalidSqlError)
    async def handle_invalid_sql(_, exc: InvalidSqlError) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)})

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok", service="conversational-analytics")

    @app.post("/ask", response_model=AskResponse)
    def ask(
        payload: AskRequest,
        service: ConversationalAnalyticsService = Depends(get_analytics_service),
    ) -> AskResponse:
        logger.info("Received /ask request", extra={"question": payload.question, "status": "received"})
        response = service.ask_question(payload.question)
        return AskResponse.model_validate(response)

    return app


app = create_app()
