"""B07: accept/decline → agreement → simulate-sign → disbursement → COMPLETED."""

from __future__ import annotations

import os
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.app.db.models import Job
from backend.app.db.session import get_session_factory
from backend.app.identity.seed_data import TEST_PASSWORD_CLIENT, TEST_PASSWORD_OFFICER
from backend.app.jobs.worker import drain

pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="DATABASE_URL not set",
)

MIN_PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"


def _login(client: TestClient, username: str, password: str) -> dict[str, str]:
    client.cookies.clear()
    res = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return {"X-CSRF-Token": res.json()["csrf_token"]}


def _offer_application(client: TestClient, *, key: str) -> tuple[str, dict[str, str]]:
    headers = _login(client, "client_romashka", TEST_PASSWORD_CLIENT)
    create = client.post(
        "/api/v1/applications",
        headers={**headers, "Idempotency-Key": f"b07-create-{key}"},
        json={"product_code": "WORKING_CAPITAL"},
    )
    app_id = create.json()["id"]
    client.patch(
        f"/api/v1/applications/{app_id}",
        headers=headers,
        json={
            "expected_version": 1,
            "draft_fields": {
                "purpose": "working_capital",
                "requested_amount": "1000000.00",
                "term_months": 12,
                "company_form": "LLC",
                "monthly_revenue": "1500000.00",
                "monthly_operating_costs": "1000000.00",
                "declared_monthly_debt_payments": "100000.00",
            },
        },
    )
    upload = client.post(
        f"/api/v1/applications/{app_id}/documents",
        headers={**headers, "Idempotency-Key": f"b07-doc-{key}"},
        data={"kind": "FINANCIAL_SUMMARY", "expected_version": 2},
        files={"file": ("s.pdf", MIN_PDF, "application/pdf")},
    )
    client.post(
        f"/api/v1/applications/{app_id}/submit",
        headers={**headers, "Idempotency-Key": f"b07-submit-{key}"},
        json={"expected_version": upload.json()["version"]},
    )
    drain(max_jobs=5)

    officer = _login(client, "officer", TEST_PASSWORD_OFFICER)
    dossier = client.get(f"/api/v1/bank/applications/{app_id}", headers=officer).json()
    decision = client.post(
        f"/api/v1/bank/applications/{app_id}/decision",
        headers={**officer, "Idempotency-Key": f"b07-approve-{key}"},
        json={
            "expected_version": dossier["version"],
            "run_id": dossier["active_run_id"],
            "type": "APPROVE_OFFER",
            "candidate_hash": dossier["risk_summary"]["candidate_hash"],
        },
    )
    assert decision.status_code == 200, decision.text
    assert decision.json()["status"] == "OFFERED"
    return app_id, _login(client, "client_romashka", TEST_PASSWORD_CLIENT)


def test_accept_sign_completes(client: TestClient) -> None:
    app_id, headers = _offer_application(client, key="happy")

    offer = client.get(f"/api/v1/applications/{app_id}/offer", headers=headers)
    assert offer.status_code == 200, offer.text
    offer_body = offer.json()
    assert offer_body["status"] == "ACTIVE"
    assert "amount" in offer_body["terms"]

    app = client.get(f"/api/v1/applications/{app_id}", headers=headers).json()
    accept = client.post(
        f"/api/v1/applications/{app_id}/offer/accept",
        headers={**headers, "Idempotency-Key": "b07-accept-1"},
        json={"expected_version": app["version"], "offer_id": offer_body["id"]},
    )
    assert accept.status_code == 200, accept.text
    assert accept.json()["status"] == "ACCEPTED"
    assert "SIMULATE_SIGN" in accept.json()["allowed_actions"]

    # Идемпотентный повтор
    again = client.post(
        f"/api/v1/applications/{app_id}/offer/accept",
        headers={**headers, "Idempotency-Key": "b07-accept-1"},
        json={"expected_version": app["version"], "offer_id": offer_body["id"]},
    )
    assert again.status_code == 200
    assert again.json()["status"] == "ACCEPTED"

    agreement = client.get(f"/api/v1/applications/{app_id}/agreement", headers=headers)
    assert agreement.status_code == 200, agreement.text
    agr = agreement.json()
    assert agr["is_simulation"] is True
    assert agr["content_hash"]
    assert "credit_agreement_simulation" in agr["document_text"]

    sign = client.post(
        f"/api/v1/applications/{app_id}/agreement/simulate-sign",
        headers={**headers, "Idempotency-Key": "b07-sign-1"},
        json={
            "expected_version": accept.json()["version"],
            "agreement_id": agr["id"],
            "content_hash": agr["content_hash"],
            "consent": True,
        },
    )
    assert sign.status_code == 202, sign.text
    assert sign.json()["status"] == "SIGNED"

    outcomes = drain(max_jobs=5)
    assert "completed" in outcomes

    done = client.get(f"/api/v1/applications/{app_id}", headers=headers).json()
    assert done["status"] == "COMPLETED"


def test_decline_offer(client: TestClient) -> None:
    app_id, headers = _offer_application(client, key="decline")
    offer = client.get(f"/api/v1/applications/{app_id}/offer", headers=headers).json()
    app = client.get(f"/api/v1/applications/{app_id}", headers=headers).json()
    decline = client.post(
        f"/api/v1/applications/{app_id}/offer/decline",
        headers={**headers, "Idempotency-Key": "b07-decline-1"},
        json={"expected_version": app["version"], "offer_id": offer["id"]},
    )
    assert decline.status_code == 200, decline.text
    assert decline.json()["status"] == "DECLINED_BY_CLIENT"


def test_hash_mismatch_blocks_sign(client: TestClient) -> None:
    app_id, headers = _offer_application(client, key="hash")
    offer = client.get(f"/api/v1/applications/{app_id}/offer", headers=headers).json()
    app = client.get(f"/api/v1/applications/{app_id}", headers=headers).json()
    accept = client.post(
        f"/api/v1/applications/{app_id}/offer/accept",
        headers={**headers, "Idempotency-Key": "b07-accept-hash"},
        json={"expected_version": app["version"], "offer_id": offer["id"]},
    )
    agr = client.get(f"/api/v1/applications/{app_id}/agreement", headers=headers).json()
    bad = client.post(
        f"/api/v1/applications/{app_id}/agreement/simulate-sign",
        headers={**headers, "Idempotency-Key": "b07-sign-bad"},
        json={
            "expected_version": accept.json()["version"],
            "agreement_id": agr["id"],
            "content_hash": "0" * 64,
            "consent": True,
        },
    )
    assert bad.status_code == 409
    assert bad.json()["error"]["code"] == "HASH_MISMATCH"


def test_retry_disbursement_after_failed_job(client: TestClient) -> None:
    app_id, headers = _offer_application(client, key="retry")
    offer = client.get(f"/api/v1/applications/{app_id}/offer", headers=headers).json()
    app = client.get(f"/api/v1/applications/{app_id}", headers=headers).json()
    accept = client.post(
        f"/api/v1/applications/{app_id}/offer/accept",
        headers={**headers, "Idempotency-Key": "b07-accept-retry"},
        json={"expected_version": app["version"], "offer_id": offer["id"]},
    )
    agr = client.get(f"/api/v1/applications/{app_id}/agreement", headers=headers).json()
    sign = client.post(
        f"/api/v1/applications/{app_id}/agreement/simulate-sign",
        headers={**headers, "Idempotency-Key": "b07-sign-retry"},
        json={
            "expected_version": accept.json()["version"],
            "agreement_id": agr["id"],
            "content_hash": agr["content_hash"],
            "consent": True,
        },
    )
    assert sign.json()["status"] == "SIGNED"

    # Сломаем job до claim
    session = get_session_factory()()
    try:
        job = session.scalar(
            select(Job).where(
                Job.application_id == app_id,
                Job.kind == "simulate_disbursement",
                Job.state == "pending",
            )
        )
        assert job is not None
        job.state = "failed"
        job.last_error = "injected_failure"
        job.updated_at = datetime.now(UTC)
        session.commit()
    finally:
        session.close()

    officer = _login(client, "officer", TEST_PASSWORD_OFFICER)
    dossier = client.get(f"/api/v1/bank/applications/{app_id}", headers=officer).json()
    assert dossier["status"] == "SIGNED"
    assert "RETRY_DISBURSEMENT" in dossier["allowed_actions"]

    retry = client.post(
        f"/api/v1/bank/applications/{app_id}/retry-disbursement",
        headers={**officer, "Idempotency-Key": "b07-retry-1"},
        json={"expected_version": dossier["version"]},
    )
    assert retry.status_code == 202, retry.text
    assert retry.json()["status"] == "SIGNED"

    drain(max_jobs=5)
    client_h = _login(client, "client_romashka", TEST_PASSWORD_CLIENT)
    done = client.get(f"/api/v1/applications/{app_id}", headers=client_h)
    assert done.status_code == 200, done.text
    assert done.json()["status"] == "COMPLETED"
