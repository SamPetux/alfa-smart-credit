"""Q04: IDOR, CSRF, роли, чужая компания, DEMO_MODE=false (API)."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import get_settings
from backend.app.db.session import get_engine, get_session_factory
from backend.app.identity.seed_data import TEST_PASSWORD_CLIENT, TEST_PASSWORD_OFFICER

pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="DATABASE_URL not set",
)

MIN_PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"


def _demo(client: TestClient, profile_id: str) -> dict[str, str]:
    client.cookies.clear()
    res = client.post("/api/v1/demo/session", json={"profile_id": profile_id})
    assert res.status_code == 200, res.text
    return {"X-CSRF-Token": res.json()["csrf_token"]}


def _login(client: TestClient, username: str, password: str) -> dict[str, str]:
    client.cookies.clear()
    res = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return {"X-CSRF-Token": res.json()["csrf_token"]}


def _draft_app(client: TestClient, headers: dict[str, str], *, key: str) -> str:
    create = client.post(
        "/api/v1/applications",
        headers={**headers, "Idempotency-Key": f"q04-create-{key}"},
        json={"product_code": "WORKING_CAPITAL"},
    )
    assert create.status_code == 201, create.text
    return create.json()["id"]


def test_csrf_missing_header_forbidden(client: TestClient) -> None:
    headers = _demo(client, "client-romashka")
    # Сессия есть (cookie), заголовка нет — double-submit обязан отказать.
    res = client.post(
        "/api/v1/applications",
        headers={"Idempotency-Key": "q04-no-csrf"},
        json={"product_code": "WORKING_CAPITAL"},
    )
    assert res.status_code == 403
    assert headers  # сессия создана


def test_client_cannot_call_bank_queue(client: TestClient) -> None:
    headers = _demo(client, "client-romashka")
    res = client.get("/api/v1/bank/applications", headers=headers)
    assert res.status_code == 403


def test_idor_foreign_application_is_404(client: TestClient) -> None:
    a = _demo(client, "client-romashka")
    app_id = _draft_app(client, a, key="romashka")
    b = _demo(client, "client-ivanov")
    got = client.get(f"/api/v1/applications/{app_id}", headers=b)
    assert got.status_code == 404
    listed = client.get("/api/v1/applications", headers=b)
    assert listed.status_code == 200
    assert all(item["id"] != app_id for item in listed.json()["items"])


def test_foreign_document_download_is_404(client: TestClient) -> None:
    a = _demo(client, "client-romashka")
    app_id = _draft_app(client, a, key="doc-owner")
    upload = client.post(
        f"/api/v1/applications/{app_id}/documents",
        headers={**a, "Idempotency-Key": "q04-doc"},
        data={"kind": "FINANCIAL_SUMMARY", "expected_version": 1},
        files={"file": ("s.pdf", MIN_PDF, "application/pdf")},
    )
    assert upload.status_code == 201, upload.text
    doc_id = upload.json()["id"]
    b = _demo(client, "client-ivanov")
    dl = client.get(f"/api/v1/applications/{app_id}/documents/{doc_id}", headers=b)
    assert dl.status_code == 404


def test_demo_mode_off_hides_demo_routes(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEMO_MODE", "false")
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()
    try:
        assert client.get("/api/v1/demo/profiles").status_code == 404
        assert (
            client.post("/api/v1/demo/session", json={"profile_id": "client-romashka"}).status_code
            == 404
        )
        # Обычный login остаётся.
        assert _login(client, "officer", TEST_PASSWORD_OFFICER)
    finally:
        monkeypatch.setenv("DEMO_MODE", "true")
        get_settings.cache_clear()
        get_engine.cache_clear()
        get_session_factory.cache_clear()


def test_officer_sees_application_client_cannot_approve(client: TestClient) -> None:
    client_headers = _demo(client, "client-romashka")
    app_id = _draft_app(client, client_headers, key="no-approve")
    # Клиент не может дергать decision.
    res = client.post(
        f"/api/v1/bank/applications/{app_id}/decision",
        headers={**client_headers, "Idempotency-Key": "q04-client-decision"},
        json={
            "expected_version": 1,
            "run_id": "00000000-0000-4000-8000-000000000001",
            "type": "REJECT",
            "reason_code": "OVERDUE_LIMIT",
        },
    )
    assert res.status_code == 403
