"""Auth/demo API на реальном PostgreSQL (DATABASE_URL)."""

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
from backend.app.identity.seed_data import TEST_PASSWORD_CLIENT, TEST_PASSWORD_OFFICER

pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="DATABASE_URL not set",
)

BACKEND_DIR = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def client():
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()

    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    command.upgrade(cfg, "head")
    run_seed()

    # Пересоздать engine после migrate (чистый pool)
    get_engine.cache_clear()
    get_session_factory.cache_clear()

    from backend.app.main import app

    with TestClient(app) as test_client:
        yield test_client

    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()


def test_demo_profiles_and_session(client: TestClient) -> None:
    profiles = client.get("/api/v1/demo/profiles")
    assert profiles.status_code == 200
    ids = {p["id"] for p in profiles.json()["profiles"]}
    assert ids == {"client-romashka", "client-ivanov", "officer"}

    res = client.post("/api/v1/demo/session", json={"profile_id": "client-romashka"})
    assert res.status_code == 200
    body = res.json()
    assert body["user"]["role"] == "CLIENT"
    assert body["user"]["company"]["demo_registration_id"] == "DEMO-001"
    assert body["csrf_token"]
    assert body["demo_mode"] is True
    assert client.cookies.get("asc_session")

    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["user"]["username"] == "client_romashka"


def test_demo_unknown_profile(client: TestClient) -> None:
    res = client.post("/api/v1/demo/session", json={"profile_id": "hacker"})
    assert res.status_code == 404


def test_login_officer_and_products(client: TestClient) -> None:
    client.cookies.clear()
    res = client.post(
        "/api/v1/auth/login",
        json={"username": "officer", "password": TEST_PASSWORD_OFFICER},
    )
    assert res.status_code == 200
    assert res.json()["user"]["role"] == "OFFICER"
    assert res.json()["user"]["company"] is None

    products = client.get("/api/v1/products")
    assert products.status_code == 200
    codes = {p["code"] for p in products.json()["products"]}
    assert codes == {"WORKING_CAPITAL", "EQUIPMENT"}


def test_login_wrong_password(client: TestClient) -> None:
    client.cookies.clear()
    res = client.post(
        "/api/v1/auth/login",
        json={"username": "client_romashka", "password": "wrong"},
    )
    assert res.status_code == 401


def test_logout(client: TestClient) -> None:
    client.cookies.clear()
    client.post(
        "/api/v1/auth/login",
        json={"username": "client_ivanov", "password": TEST_PASSWORD_CLIENT},
    )
    out = client.post("/api/v1/auth/logout")
    assert out.status_code == 204
    me = client.get("/api/v1/auth/me")
    assert me.status_code == 401


def test_ready_after_migrate(client: TestClient) -> None:
    res = client.get("/api/v1/health/ready")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
