"""
database/db.py

Reusable SQLAlchemy connection module for the Smart Asset Re-routing &
Scheduling Optimizer (Module #6).

Responsibilities:
    - Load DB credentials from environment variables (.env)
    - Build a single, reusable SQLAlchemy Engine connected to Neon PostgreSQL
    - Provide a session factory + context-managed session helper
    - Fail loudly (with a clear message) if the connection cannot be
      established, rather than failing silently deep inside a tool call

This module intentionally does NOT hardcode credentials, table names, or
schema assumptions. Table/column discovery happens separately in
`schema_explorer.py` (Step 2).
"""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Generator, Optional

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

# --------------------------------------------------------------------------
# Logging setup
# --------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Load environment variables from .env (once, at import time)
# --------------------------------------------------------------------------
load_dotenv()

REQUIRED_ENV_VARS = [
    "PGHOST",
    "PGDATABASE",
    "PGUSER",
    "PGPASSWORD",
]

# SSL / channel binding are required by Neon; default sensibly if not set.
PGSSLMODE = os.getenv("PGSSLMODE", "require")
PGCHANNELBINDING = os.getenv("PGCHANNELBINDING", "require")


class DatabaseConfigError(RuntimeError):
    """Raised when required database configuration is missing or invalid."""


class DatabaseConnectionError(RuntimeError):
    """Raised when the engine cannot connect to the database."""


def _build_database_url() -> str:
    """
    Build a PostgreSQL connection URL (via psycopg2) from environment
    variables. Raises DatabaseConfigError if any required variable is
    missing.
    """
    missing = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    if missing:
        raise DatabaseConfigError(
            f"Missing required environment variable(s): {', '.join(missing)}. "
            "Make sure your .env file defines PGHOST, PGDATABASE, PGUSER, "
            "PGPASSWORD (and optionally PGSSLMODE, PGCHANNELBINDING)."
        )

    host = os.getenv("PGHOST")
    database = os.getenv("PGDATABASE")
    user = os.getenv("PGUSER")
    password = os.getenv("PGPASSWORD")

    # Neon requires SSL. channel_binding is passed as a query param.
    url = (
        f"postgresql+psycopg2://{user}:{password}@{host}/{database}"
        f"?sslmode={PGSSLMODE}&channel_binding={PGCHANNELBINDING}"
    )
    return url


class Database:
    """
    Thin wrapper around a single SQLAlchemy Engine + sessionmaker.

    Usage:
        db = Database()
        with db.session_scope() as session:
            session.execute(...)

    The engine is created once (lazily) and reused across the app to avoid
    exhausting Neon's connection limits.
    """

    _engine: Optional[Engine] = None
    _session_factory: Optional[sessionmaker] = None

    def __init__(self) -> None:
        self._ensure_engine()

    @classmethod
    def _ensure_engine(cls) -> Engine:
        """Create the engine once (singleton-style) and reuse it thereafter."""
        if cls._engine is not None:
            return cls._engine

        try:
            url = _build_database_url()
            logger.info("Creating SQLAlchemy engine for Neon PostgreSQL...")
            engine = create_engine(
                url,
                pool_pre_ping=True,   # detect stale/dropped connections
                pool_size=5,
                max_overflow=5,
                pool_recycle=1800,    # recycle connections every 30 min
                future=True,
            )
            # Verify the connection actually works before handing it back.
            with engine.connect() as conn:
                conn.exec_driver_sql("SELECT 1")

            logger.info("Successfully connected to Neon PostgreSQL.")
            cls._engine = engine
            cls._session_factory = sessionmaker(
                bind=engine, autoflush=False, autocommit=False, future=True
            )
            return engine

        except DatabaseConfigError:
            raise
        except SQLAlchemyError as exc:
            logger.error("Failed to connect to the database: %s", exc)
            raise DatabaseConnectionError(
                "Could not establish a connection to the Neon PostgreSQL "
                "database. Check your credentials, network access, and "
                "that the Neon project is not suspended."
            ) from exc

    @property
    def engine(self) -> Engine:
        return self._ensure_engine()

    def get_session(self) -> Session:
        """Return a new Session. Caller is responsible for closing it,
        or prefer `session_scope()` below."""
        self._ensure_engine()
        assert self._session_factory is not None
        return self._session_factory()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Context-managed session: commits on success, rolls back on
        exception, and always closes the session.

        Example:
            with db.session_scope() as session:
                session.execute(text("SELECT 1"))
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


# --------------------------------------------------------------------------
# Module-level singleton for convenient import elsewhere:
#   from database.db import db
# --------------------------------------------------------------------------
db = Database()


if __name__ == "__main__":
    # Simple manual smoke test: `python database/db.py`
    try:
        with db.session_scope() as session:
            result = session.execute_driver_sql if False else None  # noop guard
            from sqlalchemy import text

            row = session.execute(text("SELECT version();")).fetchone()
            print("Connected. PostgreSQL version:", row[0])
    except (DatabaseConfigError, DatabaseConnectionError) as e:
        print(f"[ERROR] {e}")
