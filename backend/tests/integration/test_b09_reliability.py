"""B09: request_id, meta privacy, demo off, lease reclaim."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.app.core.config import DEMO_PRIVACY_NOTICE, get_settings
from backend.app.db.models import Application, Job, Membership, Product, User
from backend.app.db.session import get_session_factory
from backend.app.jobs.claim import reclaim_expired_leases

pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="DATABASE_URL not set",
)


def test_request_id_header_and_meta_privacy(client: TestClient) -> None:
    res = client.get("/api/v1/health/live", headers={"X-Request-Id": "req-custom-abc"})
    assert res.status_code == 200
    assert res.headers.get("X-Request-Id") == "req-custom-abc"

    meta = client.get("/api/v1/meta")
    assert meta.status_code == 200
    body = meta.json()
    assert body["demo_mode"] is True
    assert body["privacy_notice"] == DEMO_PRIVACY_NOTICE
    assert body["is_simulation"] is True


def test_demo_disabled_returns_404(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.setenv("APP_ENV", "local")
    get_settings.cache_clear()
    from backend.app.db.session import get_engine, get_session_factory

    get_engine.cache_clear()
    get_session_factory.cache_clear()

    # Переимпорт app с новым settings
    import importlib

    import backend.app.main as main_mod

    importlib.reload(main_mod)
    with TestClient(main_mod.app) as c:
        profiles = c.get("/api/v1/demo/profiles")
        assert profiles.status_code == 404
        session = c.post("/api/v1/demo/session", json={"profile_id": "client-romashka"})
        assert session.status_code == 404
        meta = c.get("/api/v1/meta").json()
        assert meta["demo_mode"] is False
        assert "privacy_notice" not in meta

    monkeypatch.setenv("DEMO_MODE", "true")
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()
    importlib.reload(main_mod)


def test_reclaim_expired_lease_to_failed_when_max_attempts(client: TestClient) -> None:
    settings = get_settings()
    session = get_session_factory()()
    try:
        product = session.scalar(select(Product).limit(1))
        user = session.scalar(select(User).where(User.username == "client_romashka"))
        membership = session.scalar(select(Membership).where(Membership.user_id == user.id))
        assert product and user and membership
        app = Application(
            company_id=membership.company_id,
            product_id=product.id,
            creator_id=user.id,
            status="SIGNED",
            version=1,
            current_revision=1,
            draft_json={},
        )
        session.add(app)
        session.flush()
        job = Job(
            kind="simulate_disbursement",
            application_id=app.id,
            payload_json={},
            state="running",
            attempts=settings.job_max_attempts,
            available_at=datetime.now(UTC) - timedelta(minutes=5),
            lease_until=datetime.now(UTC) - timedelta(seconds=1),
            lease_token=uuid4(),
            last_error="stale",
        )
        session.add(job)
        session.commit()
        job_id = job.id
    finally:
        session.close()

    session = get_session_factory()()
    try:
        n = reclaim_expired_leases(session, settings=settings)
        session.commit()
        assert n >= 1
        row = session.get(Job, job_id)
        assert row is not None
        assert row.state == "failed"
        assert row.lease_token is None
        assert row.last_error == "lease_expired_max_attempts"
    finally:
        session.close()
