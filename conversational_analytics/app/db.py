from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from langchain_community.utilities import SQLDatabase

from .config import AppSettings


class DatabaseConnectionError(RuntimeError):
    """Raised when the PostgreSQL connection cannot be established."""


def create_engine_from_settings(settings: AppSettings) -> Engine:
    # Use SQLAlchemy URL object to correctly encode credentials and query params (sslmode, channel_binding)
    url = settings.database_url_object()
    engine = create_engine(url, pool_pre_ping=True, future=True)
    return engine


def create_sql_database(settings: AppSettings) -> tuple[Engine, SQLDatabase]:
    engine = create_engine_from_settings(settings)
    try:
        with engine.connect() as connection:
            # quick smoke test
            connection.execute(text("SELECT 1"))
        # LangChain SQLDatabase expects a URI string; use the textual form of the URL
        query: dict[str, str] = {"sslmode": settings.pg_sslmode}
        if getattr(settings, "pg_channel_binding", ""):
            query["channel_binding"] = settings.pg_channel_binding
        database = SQLDatabase.from_uri(str(settings.database_url_object()))
    except SQLAlchemyError as exc:
        raise DatabaseConnectionError("Database connection failed.") from exc

    return engine, database
