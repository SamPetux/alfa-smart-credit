"""B05: после submit worker доводит заявку до MANUAL_REVIEW / PROCESSING_ERROR."""

from __future__ import annotations

import os
import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from backend.app.core.config import get_settings
from backend.app.db.session import get_engine, get_session_factory
from backend.app.jobs.worker import drain, process_once

pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="DATABASE_URL not set",
)

MIN_PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"


def _create_submitted(
    client: TestClient,
    headers: dict[str, str],
    *,
    key: str,
    demo_scenario: str | None = None,
) -> str:
    create = client.post(
        "/api/v1/applications",
        headers={**headers, "Idempotency-Key": f"w-create-{key}"},
        json={"product_code": "WORKING_CAPITAL"},
    )
    assert create.status_code == 201, create.text
    app_id = create.json()["id"]
    draft_fields: dict = {
        "purpose": "working_capital",
        "requested_amount": "1000000.00",
        "term_months": 12,
        "company_form": "LLC",
        "monthly_revenue": "1500000.00",
        "monthly_operating_costs": "1000000.00",
        "declared_monthly_debt_payments": "100000.00",
    }
    if demo_scenario:
        draft_fields["demo_scenario"] = demo_scenario

    patch = client.patch(
        f"/api/v1/applications/{app_id}",
        headers=headers,
        json={"expected_version": 1, "draft_fields": draft_fields},
    )
    assert patch.status_code == 200, patch.text
    version = patch.json()["version"]

    upload = client.post(
        f"/api/v1/applications/{app_id}/documents",
        headers={**headers, "Idempotency-Key": f"w-doc-{key}"},
        data={"kind": "FINANCIAL_SUMMARY", "expected_version": version},
        files={"file": ("summary.pdf", MIN_PDF, "application/pdf")},
    )
    assert upload.status_code == 201, upload.text
    version = upload.json()["version"]

    submit = client.post(
        f"/api/v1/applications/{app_id}/submit",
        headers={**headers, "Idempotency-Key": f"w-submit-{key}"},
        json={"expected_version": version},
    )
    assert submit.status_code == 202, submit.text
    return app_id


def test_worker_g01_to_manual_review(client: TestClient, client_headers: dict[str, str]) -> None:
    app_id = _create_submitted(client, client_headers, key="g01")
    outcomes = drain(max_jobs=5)
    assert "completed" in outcomes

    got = client.get(f"/api/v1/applications/{app_id}", headers=client_headers)
    assert got.status_code == 200
    assert got.json()["status"] == "MANUAL_REVIEW"

    engine = create_engine(os.environ["DATABASE_URL"], future=True)
    with engine.connect() as conn:
        rec = conn.execute(
            text(
                "SELECT recommendation, score, band FROM risk_assessments ra "
                "JOIN evaluation_runs er ON er.id = ra.run_id "
                "JOIN applications a ON a.active_run_id = er.id "
                "WHERE a.id = :id"
            ),
            {"id": app_id},
        ).one()
    assert rec.recommendation == "OFFER"
    assert rec.score == 100
    assert rec.band == "A"


def test_worker_timeout_to_processing_error(
    client: TestClient, client_headers: dict[str, str]
) -> None:
    os.environ["JOB_MAX_ATTEMPTS"] = "2"
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()

    try:
        app_id = _create_submitted(
            client, client_headers, key="timeout", demo_scenario="timeout"
        )
        assert process_once() == "requeued"
        time.sleep(1.2)
        assert process_once() == "failed"

        got = client.get(f"/api/v1/applications/{app_id}", headers=client_headers)
        assert got.json()["status"] == "PROCESSING_ERROR"
    finally:
        os.environ.pop("JOB_MAX_ATTEMPTS", None)
        get_settings.cache_clear()
        get_engine.cache_clear()
        get_session_factory.cache_clear()
