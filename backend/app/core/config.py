"""Конфигурация из окружения. Секреты только через env, не в коде."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    return int(raw)


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str
    demo_mode: bool
    session_secret: str
    session_ttl_seconds: int
    cookie_secure: bool
    cookie_name: str
    csrf_header: str
    app_env: str
    documents_dir: str
    job_max_attempts: int
    job_lease_seconds: int
    worker_poll_seconds: float
    fixtures_root: str


@lru_cache
def get_settings() -> Settings:
    return Settings(
        database_url=os.environ.get(
            "DATABASE_URL",
            "postgresql+psycopg://alfa:alfa@127.0.0.1:5432/alfa_credit",
        ),
        demo_mode=_env_bool("DEMO_MODE", True),
        session_secret=os.environ.get("SESSION_SECRET", "change-me-demo-only"),
        session_ttl_seconds=_env_int("SESSION_TTL_SECONDS", 60 * 60 * 8),
        cookie_secure=_env_bool("COOKIE_SECURE", False),
        cookie_name=os.environ.get("SESSION_COOKIE_NAME", "asc_session"),
        csrf_header=os.environ.get("CSRF_HEADER", "X-CSRF-Token"),
        app_env=os.environ.get("APP_ENV", "local"),
        documents_dir=os.environ.get("DOCUMENTS_DIR", "data/documents"),
        job_max_attempts=_env_int("JOB_MAX_ATTEMPTS", 3),
        job_lease_seconds=_env_int("JOB_LEASE_SECONDS", 60),
        worker_poll_seconds=float(os.environ.get("WORKER_POLL_SECONDS", "2")),
        fixtures_root=os.environ.get("FIXTURES_ROOT", ""),
    )
