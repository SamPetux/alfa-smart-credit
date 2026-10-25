"""B06: officer request-info / approve / reject + client resubmit."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

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


def _submit_to_manual_review(client: TestClient, *, key: str) -> str:
    headers = _login(client, "client_romashka", TEST_PASSWORD_CLIENT)
    create = client.post(
        "/api/v1/applications",
        headers={**headers, "Idempotency-Key": f"off-create-{key}"},
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
        headers={**headers, "Idempotency-Key": f"off-doc-{key}"},
        data={"kind": "FINANCIAL_SUMMARY", "expected_version": 2},
        files={"file": ("s.pdf", MIN_PDF, "application/pdf")},
    )
    client.post(
        f"/api/v1/applications/{app_id}/submit",
        headers={**headers, "Idempotency-Key": f"off-submit-{key}"},
        json={"expected_version": upload.json()["version"]},
    )
    drain(max_jobs=5)
    return app_id


def test_officer_approve_offer(client: TestClient) -> None:
    app_id = _submit_to_manual_review(client, key="approve")
    officer = _login(client, "officer", TEST_PASSWORD_OFFICER)

    dossier = client.get(f"/api/v1/bank/applications/{app_id}", headers=officer)
    assert dossier.status_code == 200, dossier.text
    body = dossier.json()
    assert body["status"] == "MANUAL_REVIEW"
    assert "APPROVE_OFFER" in body["allowed_actions"]
    run_id = body["active_run_id"]
    candidate_hash = body["risk_summary"]["candidate_hash"]
    version = body["version"]

    decision = client.post(
        f"/api/v1/bank/applications/{app_id}/decision",
        headers={**officer, "Idempotency-Key": "approve-1"},
        json={
            "expected_version": version,
            "run_id": run_id,
            "type": "APPROVE_OFFER",
            "candidate_hash": candidate_hash,
        },
    )
    assert decision.status_code == 200, decision.text
    assert decision.json()["status"] == "OFFERED"


def test_officer_request_info_and_client_resubmit(client: TestClient) -> None:
    app_id = _submit_to_manual_review(client, key="info")
    officer = _login(client, "officer", TEST_PASSWORD_OFFICER)
    dossier = client.get(f"/api/v1/bank/applications/{app_id}", headers=officer).json()

    req = client.post(
        f"/api/v1/bank/applications/{app_id}/request-info",
        headers={**officer, "Idempotency-Key": "info-1"},
        json={
            "expected_version": dossier["version"],
            "fields": ["monthly_revenue"],
            "document_kinds": [],
            "message": "Уточните выручку",
        },
    )
    assert req.status_code == 200, req.text
    assert req.json()["status"] == "NEEDS_INFO"

    client_h = _login(client, "client_romashka", TEST_PASSWORD_CLIENT)
    info = client.get(f"/api/v1/applications/{app_id}/info-request", headers=client_h)
    assert info.status_code == 200
    info_id = info.json()["id"]

    app = client.get(f"/api/v1/applications/{app_id}", headers=client_h).json()
    patch = client.patch(
        f"/api/v1/applications/{app_id}",
        headers=client_h,
        json={
            "expected_version": app["version"],
            "draft_fields": {"monthly_revenue": "1600000.00"},
        },
    )
    assert patch.status_code == 200, patch.text

    resubmit = client.post(
        f"/api/v1/applications/{app_id}/resubmit",
        headers={**client_h, "Idempotency-Key": "resub-1"},
        json={"expected_version": patch.json()["version"], "info_request_id": info_id},
    )
    assert resubmit.status_code == 202, resubmit.text
    assert resubmit.json()["status"] == "SUBMITTED"
    assert resubmit.json()["current_revision"] == 2

    drain(max_jobs=5)
    after = client.get(f"/api/v1/applications/{app_id}", headers=client_h).json()
    assert after["status"] == "MANUAL_REVIEW"


def test_officer_reject(client: TestClient) -> None:
    app_id = _submit_to_manual_review(client, key="reject")
    officer = _login(client, "officer", TEST_PASSWORD_OFFICER)
    dossier = client.get(f"/api/v1/bank/applications/{app_id}", headers=officer).json()
    decision = client.post(
        f"/api/v1/bank/applications/{app_id}/decision",
        headers={**officer, "Idempotency-Key": "reject-1"},
        json={
            "expected_version": dossier["version"],
            "run_id": dossier["active_run_id"],
            "type": "REJECT",
            "reason_code": "POLICY_REJECT",
            "comment": "Отказ по решению сотрудника (демо)",
        },
    )
    assert decision.status_code == 200, decision.text
    assert decision.json()["status"] == "REJECTED"
