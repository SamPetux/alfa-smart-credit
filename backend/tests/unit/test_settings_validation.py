"""B09: production не принимает DEMO_MODE и demo SESSION_SECRET."""

from __future__ import annotations

import pytest

from backend.app.core.config import (
    DEFAULT_SESSION_SECRET,
    Settings,
    SettingsError,
    validate_settings,
)


def _base(**overrides: object) -> Settings:
    data = {
        "database_url": "postgresql+psycopg://x",
        "demo_mode": False,
        "session_secret": "prod-secret-not-default",
        "session_ttl_seconds": 3600,
        "cookie_secure": True,
        "cookie_name": "asc_session",
        "csrf_header": "X-CSRF-Token",
        "app_env": "production",
        "documents_dir": "/data/documents",
        "job_max_attempts": 3,
        "job_lease_seconds": 60,
        "worker_poll_seconds": 2.0,
        "fixtures_root": "",
        "log_level": "INFO",
    }
    data.update(overrides)
    return Settings(**data)  # type: ignore[arg-type]


def test_production_ok() -> None:
    validate_settings(_base())


def test_production_rejects_demo_mode() -> None:
    with pytest.raises(SettingsError, match="DEMO_MODE"):
        validate_settings(_base(demo_mode=True))


def test_production_rejects_default_secret() -> None:
    with pytest.raises(SettingsError, match="SESSION_SECRET"):
        validate_settings(_base(session_secret=DEFAULT_SESSION_SECRET))


def test_production_rejects_insecure_cookie() -> None:
    with pytest.raises(SettingsError, match="COOKIE_SECURE"):
        validate_settings(_base(cookie_secure=False))


def test_local_allows_demo_defaults() -> None:
    validate_settings(_base(app_env="local", demo_mode=True, cookie_secure=False, session_secret=DEFAULT_SESSION_SECRET))
