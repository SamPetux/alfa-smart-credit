"""B04: create → patch → document → submit (+ idempotency / 409)."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="DATABASE_URL not set",
)

MIN_PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"


def test_create_patch_submit_flow(client: TestClient, client_headers: dict[str, str]) -> None:
    create = client.post(
        "/api/v1/applications",
        headers={**client_headers, "Idempotency-Key": "create-1"},
        json={"product_code": "WORKING_CAPITAL"},
    )
    assert create.status_code == 201, create.text
    app = create.json()
    assert app["status"] == "DRAFT"
    assert app["version"] == 1
    assert "SAVE" in app["allowed_actions"]
    app_id = app["id"]

    # idempotent recreate
    again = client.post(
        "/api/v1/applications",
        headers={**client_headers, "Idempotency-Key": "create-1"},
        json={"product_code": "WORKING_CAPITAL"},
    )
    assert again.status_code == 201
    assert again.json()["id"] == app_id

    patch = client.patch(
        f"/api/v1/applications/{app_id}",
        headers=client_headers,
        json={
            "expected_version": 1,
            "draft_fields": {
                "purpose": "working_capital",
                "requested_amount": "1000000.00",
                "term_months": 12,
                "company_form": "LLC",
                "monthly_revenue": "600000.00",
                "monthly_operating_costs": "400000.00",
                "declared_monthly_debt_payments": "100000.00",
            },
        },
    )
    assert patch.status_code == 200, patch.text
    assert patch.json()["version"] == 2

    stale = client.patch(
        f"/api/v1/applications/{app_id}",
        headers=client_headers,
        json={"expected_version": 1, "draft_fields": {"term_months": 6}},
    )
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "VERSION_CONFLICT"

    upload = client.post(
        f"/api/v1/applications/{app_id}/documents",
        headers={**client_headers, "Idempotency-Key": "doc-1"},
        data={"kind": "FINANCIAL_SUMMARY", "expected_version": 2},
        files={"file": ("summary.pdf", MIN_PDF, "application/pdf")},
    )
    assert upload.status_code == 201, upload.text
    version = upload.json()["version"]

    submit = client.post(
        f"/api/v1/applications/{app_id}/submit",
        headers={**client_headers, "Idempotency-Key": "submit-1"},
        json={"expected_version": version},
    )
    assert submit.status_code == 202, submit.text
    body = submit.json()
    assert body["status"] == "SUBMITTED"
    assert body["current_revision"] == 1
    assert body["allowed_actions"] == []

    # повтор submit с тем же ключом
    submit2 = client.post(
        f"/api/v1/applications/{app_id}/submit",
        headers={**client_headers, "Idempotency-Key": "submit-1"},
        json={"expected_version": version},
    )
    assert submit2.status_code == 202
    assert submit2.json()["id"] == app_id

    engine = create_engine(os.environ["DATABASE_URL"], future=True)
    with engine.connect() as conn:
        rev_count = conn.execute(
            text("SELECT count(*) FROM application_revisions WHERE application_id = :id"),
            {"id": app_id},
        ).scalar()
        job_count = conn.execute(
            text(
                "SELECT count(*) FROM jobs WHERE application_id = :id AND kind = 'evaluate_application'"
            ),
            {"id": app_id},
        ).scalar()
        audit = conn.execute(
            text(
                "SELECT count(*) FROM audit_events WHERE application_id = :id AND action = 'SUBMIT'"
            ),
            {"id": app_id},
        ).scalar()
    assert rev_count == 1
    assert job_count == 1
    assert audit == 1


def test_submit_without_docs_fails(client: TestClient, client_headers: dict[str, str]) -> None:
    create = client.post(
        "/api/v1/applications",
        headers={**client_headers, "Idempotency-Key": "create-nodoc"},
        json={"product_code": "WORKING_CAPITAL"},
    )
    app_id = create.json()["id"]
    client.patch(
        f"/api/v1/applications/{app_id}",
        headers=client_headers,
        json={
            "expected_version": 1,
            "draft_fields": {
                "purpose": "working_capital",
                "requested_amount": "500000.00",
                "term_months": 12,
                "company_form": "LLC",
                "monthly_revenue": "600000.00",
                "monthly_operating_costs": "400000.00",
                "declared_monthly_debt_payments": "50000.00",
            },
        },
    )
    submit = client.post(
        f"/api/v1/applications/{app_id}/submit",
        headers={**client_headers, "Idempotency-Key": "submit-nodoc"},
        json={"expected_version": 2},
    )
    assert submit.status_code == 422
    assert submit.json()["error"]["code"] == "VALIDATION_ERROR"
