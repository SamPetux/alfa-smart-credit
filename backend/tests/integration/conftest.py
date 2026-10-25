"""Общие fixtures для integration-тестов с PostgreSQL."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from backend.app.core.config import get_settings
from backend.app.db.session import get_engine, get_session_factory
from backend.app.identity.seed import run_seed
from backend.app.identity.seed_data import TEST_PASSWORD_CLIENT

BACKEND_DIR = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def client():
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL not set")

    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()

    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    command.upgrade(cfg, "head")
    run_seed()

    get_engine.cache_clear()
    get_session_factory.cache_clear()

    from backend.app.main import app

    with TestClient(app) as test_client:
        yield test_client

    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()


@pytest.fixture
def client_headers(client: TestClient) -> dict[str, str]:
    client.cookies.clear()
    res = client.post(
        "/api/v1/auth/login",
        json={"username": "client_romashka", "password": TEST_PASSWORD_CLIENT},
    )
    assert res.status_code == 200
    csrf = res.json()["csrf_token"]
    return {"X-CSRF-Token": csrf}
