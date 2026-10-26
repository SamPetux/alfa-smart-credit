"""В NEEDS_INFO PATCH принимает только поля из открытого info_request."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from backend.app.applications.errors import ApiError
from backend.app.applications.service import patch_draft
from backend.app.schemas.applications import DraftFields
from backend.app.schemas.enums import ApplicationStatus


def test_needs_info_rejects_unrequested_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    app = SimpleNamespace(
        id=uuid4(),
        status=ApplicationStatus.NEEDS_INFO.value,
        version=3,
        current_revision=1,
        draft_json={"monthly_revenue": "100000.00", "purpose": "working_capital"},
        product_id=uuid4(),
        updated_at=datetime.now(UTC),
    )
    session = MagicMock()
    info = SimpleNamespace(
        application_id=app.id,
        status="OPEN",
        fields_json=["declared_monthly_debt_payments"],
    )
    session.scalar.return_value = info

    monkeypatch.setattr(
        "backend.app.applications.service.get_product",
        lambda *_a, **_k: SimpleNamespace(code="WORKING_CAPITAL"),
    )
    monkeypatch.setattr(
        "backend.app.applications.service.to_client_application",
        lambda *_a, **_k: SimpleNamespace(id=app.id),
    )

    with pytest.raises(ApiError) as exc:
        patch_draft(
            session,
            app=app,
            actor_id=uuid4(),
            expected_version=3,
            draft_fields=DraftFields(monthly_revenue="200000.00"),
        )
    assert exc.value.status_code == 422
    assert exc.value.envelope.error.code == "VALIDATION_ERROR"


def test_needs_info_allows_requested_field(monkeypatch: pytest.MonkeyPatch) -> None:
    app = SimpleNamespace(
        id=uuid4(),
        status=ApplicationStatus.NEEDS_INFO.value,
        version=3,
        current_revision=1,
        draft_json={"declared_monthly_debt_payments": "100000.00"},
        product_id=uuid4(),
        updated_at=datetime.now(UTC),
    )
    session = MagicMock()
    info = SimpleNamespace(
        application_id=app.id,
        status="OPEN",
        fields_json=["declared_monthly_debt_payments"],
    )
    session.scalar.return_value = info
    monkeypatch.setattr(
        "backend.app.applications.service.get_product",
        lambda *_a, **_k: SimpleNamespace(code="WORKING_CAPITAL"),
    )
    monkeypatch.setattr(
        "backend.app.applications.service.to_client_application",
        lambda app, product: SimpleNamespace(
            id=app.id, draft_fields=app.draft_json, version=app.version
        ),
    )

    out = patch_draft(
        session,
        app=app,
        actor_id=uuid4(),
        expected_version=3,
        draft_fields=DraftFields(declared_monthly_debt_payments="150000.00"),
    )
    assert app.version == 4
    assert app.draft_json["declared_monthly_debt_payments"] == "150000.00"
    assert out.version == 4
