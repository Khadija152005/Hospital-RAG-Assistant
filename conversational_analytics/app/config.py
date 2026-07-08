from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Self
from urllib.parse import quote_plus

import os
from dotenv import load_dotenv


load_dotenv()


class MissingConfigError(RuntimeError):
    """Raised when a required environment variable is missing."""


@dataclass(frozen=True, slots=True)
class AppSettings:
    pg_host: str
    pg_database: str
    pg_user: str
    pg_password: str
    pg_port: int = 5432
    pg_sslmode: str = "require"
    pg_channel_binding: str = ""
    google_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_fallback_models: tuple[str, ...] = ()
    max_result_rows: int = 50
    llm_max_retries: int = 3
    request_timeout_seconds: int = 30
    log_level: str = "INFO"
    enable_template_router: bool = True
    enable_llm_fallback: bool = True

    @classmethod
    def from_env(cls) -> Self:
        def require(name: str) -> str:
            value = os.getenv(name)
            if not value:
                raise MissingConfigError(f"Missing required environment variable: {name}")
            # strip optional surrounding single or double quotes
            if (value.startswith("'") and value.endswith("'")) or (
                value.startswith('"') and value.endswith('"')
            ):
                return value[1:-1]
            return value

        return cls(
            pg_host=require("PGHOST"),
            pg_database=require("PGDATABASE"),
            pg_user=require("PGUSER"),
            pg_password=require("PGPASSWORD"),
            pg_port=int(os.getenv("PGPORT", "5432")),
            pg_sslmode=os.getenv("PGSSLMODE", "require"),
            pg_channel_binding=os.getenv("PGCHANNELBINDING", ""),
            google_api_key=require("GOOGLE_API_KEY"),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            gemini_fallback_models=tuple(
                m.strip() for m in os.getenv("GEMINI_FALLBACK_MODELS", "").split(",") if m.strip()
            ),
            max_result_rows=int(os.getenv("MAX_RESULT_ROWS", "50")),
            llm_max_retries=int(os.getenv("LLM_MAX_RETRIES", "3")),
            request_timeout_seconds=int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            enable_template_router=os.getenv("ENABLE_TEMPLATE_ROUTER", "true").lower() in ("1", "true", "yes"),
            enable_llm_fallback=os.getenv("ENABLE_LLM_FALLBACK", "true").lower() in ("1", "true", "yes"),
        )

    @property
    def database_uri(self) -> str:
        password = quote_plus(self.pg_password)
        user = quote_plus(self.pg_user)
        host = self.pg_host
        database = self.pg_database
        return (
            f"postgresql+psycopg2://{user}:{password}@{host}:{self.pg_port}/{database}"
            f"?sslmode={self.pg_sslmode}"
        )

    def database_url_object(self):
        # Build a SQLAlchemy URL object to ensure safe encoding of components and query params
        from sqlalchemy.engine import URL

        query: dict[str, str] = {"sslmode": self.pg_sslmode}
        if getattr(self, "pg_channel_binding", ""):
            query["channel_binding"] = self.pg_channel_binding

        return URL.create(
            drivername="postgresql+psycopg2",
            username=self.pg_user,
            password=self.pg_password,
            host=self.pg_host,
            port=self.pg_port,
            database=self.pg_database,
            query=query,
        )


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings.from_env()
