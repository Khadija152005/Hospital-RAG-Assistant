from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from langchain_community.utilities import SQLDatabase

from .config import AppSettings


class DatabaseConnectionError(RuntimeError):
    """Raised when the PostgreSQL connection cannot be established."""


def create_engine_from_settings(settings: AppSettings) -> Engine:
    """
    Create a SQLAlchemy Engine using the validated settings.
    """

    url = settings.database_url_object()

    engine = create_engine(
        url,
        pool_pre_ping=True,
        future=True,
    )

    return engine


def create_sql_database(settings: AppSettings) -> tuple[Engine, SQLDatabase]:
    """
    Create both:
    1. SQLAlchemy Engine
    2. LangChain SQLDatabase

    Uses the SAME engine to avoid reconnecting with different credentials.
    """

    engine = create_engine_from_settings(settings)

    try:
        # Verify connection
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        # IMPORTANT:
        # Reuse the existing Engine instead of creating a new connection
        database = SQLDatabase(engine=engine)

    except SQLAlchemyError as exc:
        raise DatabaseConnectionError(
            "Database connection failed."
        ) from exc

    return engine, database
