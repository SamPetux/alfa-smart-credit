"""Черновики и submit (B04)."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.applications.errors import ApiError
from backend.app.applications.projections import to_client_application
from backend.app.applications.validation import validate_draft_for_submit
from backend.app.db.models import (
    Application,
    ApplicationRevision,
    AuditEvent,
    Document,
    EvaluationRun,
    Job,
    Product,
)
from backend.app.schemas.applications import ClientApplication, DraftFields
from backend.app.schemas.enums import ApplicationStatus, ProductCode, Role, WorkflowCommand
from backend.app.workflow.transitions import IllegalTransitionError, next_status


def _money_to_str(value: Decimal | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    return str(value)


def draft_fields_to_json(fields: DraftFields) -> dict[str, Any]:
    data = fields.model_dump(mode="python", exclude_none=False)
    for key in (
        "requested_amount",
        "monthly_revenue",
        "monthly_operating_costs",
        "declared_monthly_debt_payments",
    ):
        data[key] = _money_to_str(data.get(key))
    # Убрать None, чтобы missing ≠ 0
    return {k: v for k, v in data.items() if v is not None}


def merge_draft(existing: dict[str, Any], patch: DraftFields) -> dict[str, Any]:
    merged = dict(existing or {})
    # Только явно переданные поля (exclude_unset)
    raw = patch.model_dump(exclude_unset=True)
    for key, value in raw.items():
        if value is None:
            merged.pop(key, None)
        elif key in (
            "requested_amount",
            "monthly_revenue",
            "monthly_operating_costs",
            "declared_monthly_debt_payments",
        ):
            merged[key] = _money_to_str(value)
        else:
            merged[key] = value
    return merged


def snapshot_hash(snapshot: dict[str, Any]) -> str:
    canonical = json.dumps(snapshot, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def get_product(session: Session, product_id: UUID) -> Product:
    product = session.get(Product, product_id)
    if product is None:
        raise ApiError(500, "INTERNAL_ERROR", "Product missing for application")
    return product


def get_owned_application(
    session: Session,
    application_id: UUID,
    *,
    company_id: UUID,
) -> Application:
    app = session.get(Application, application_id)
    if app is None or app.company_id != company_id:
        raise ApiError(404, "NOT_FOUND", "Заявка не найдена")
    return app


def create_draft(
    session: Session,
    *,
    company_id: UUID,
    creator_id: UUID,
    product_code: ProductCode,
) -> ClientApplication:
    product = session.scalar(
        select(Product).where(Product.code == product_code.value, Product.active.is_(True))
    )
    if product is None:
        raise ApiError(422, "VALIDATION_ERROR", f"Неизвестный продукт {product_code.value}")

    purpose = (
        "working_capital"
        if product_code == ProductCode.WORKING_CAPITAL
        else "equipment"
    )
    app = Application(
        company_id=company_id,
        creator_id=creator_id,
        product_id=product.id,
        status=ApplicationStatus.DRAFT.value,
        version=1,
        current_revision=0,
        draft_json={"purpose": purpose},
    )
    session.add(app)
    session.flush()
    session.add(
        AuditEvent(
            application_id=app.id,
            actor_id=creator_id,
            action="CREATE_DRAFT",
            from_status=None,
            to_status=ApplicationStatus.DRAFT.value,
            revision_no=0,
            metadata_json={"product_code": product_code.value},
        )
    )
    session.flush()
    return to_client_application(app, product)


def list_company_applications(
    session: Session,
    *,
    company_id: UUID,
    limit: int = 20,
) -> list[ClientApplication]:
    rows = session.scalars(
        select(Application)
        .where(Application.company_id == company_id)
        .order_by(Application.updated_at.desc())
        .limit(limit)
    ).all()
    result: list[ClientApplication] = []
    for app in rows:
        product = get_product(session, app.product_id)
        result.append(to_client_application(app, product))
    return result


def patch_draft(
    session: Session,
    *,
    app: Application,
    actor_id: UUID,
    expected_version: int,
    draft_fields: DraftFields,
) -> ClientApplication:
    if app.version != expected_version:
        raise ApiError(
            409,
            "VERSION_CONFLICT",
            "Заявка уже изменилась. Обновите данные перед действием.",
        )
    status = ApplicationStatus(app.status)
    if status == ApplicationStatus.DRAFT:
        command = WorkflowCommand.SAVE
        action = "SAVE_DRAFT"
    elif status == ApplicationStatus.NEEDS_INFO:
        command = WorkflowCommand.SAVE_SUPPLEMENT
        action = "SAVE_SUPPLEMENT"
    else:
        raise ApiError(409, "INVALID_STATE", "Редактирование недоступно в текущем статусе")
    try:
        next_status(status, command, actor=Role.CLIENT)
    except IllegalTransitionError as exc:
        raise ApiError(409, "INVALID_STATE", str(exc)) from exc

    app.draft_json = merge_draft(app.draft_json or {}, draft_fields)
    app.version += 1
    app.updated_at = datetime.now(UTC)
    session.add(
        AuditEvent(
            application_id=app.id,
            actor_id=actor_id,
            action=action,
            from_status=status.value,
            to_status=status.value,
            revision_no=app.current_revision,
            metadata_json={},
        )
    )
    session.flush()
    return to_client_application(app, get_product(session, app.product_id))


def document_kinds_for_app(session: Session, application_id: UUID) -> set[str]:
    rows = session.scalars(
        select(Document.kind).where(Document.application_id == application_id)
    ).all()
    return set(rows)


def submit_application(
    session: Session,
    *,
    app: Application,
    actor_id: UUID,
    expected_version: int,
) -> ClientApplication:
    if app.version != expected_version:
        raise ApiError(
            409,
            "VERSION_CONFLICT",
            "Заявка уже изменилась. Обновите данные перед действием.",
        )
    product = get_product(session, app.product_id)
    product_code = ProductCode(product.code)
    docs = document_kinds_for_app(session, app.id)
    field_errors = validate_draft_for_submit(app.draft_json or {}, product_code, docs)
    if field_errors:
        raise ApiError(
            422,
            "VALIDATION_ERROR",
            "Не хватает обязательных данных для отправки",
            field_errors=field_errors,
        )

    try:
        new_status = next_status(
            ApplicationStatus(app.status),
            WorkflowCommand.SUBMIT,
            actor=Role.CLIENT,
        )
    except IllegalTransitionError as exc:
        raise ApiError(409, "INVALID_STATE", str(exc)) from exc

    revision_no = app.current_revision + 1
    snapshot = {
        "product_code": product.code,
        "draft": dict(app.draft_json or {}),
        "document_kinds": sorted(docs),
    }
    snap_hash = snapshot_hash(snapshot)
    revision = ApplicationRevision(
        application_id=app.id,
        revision_no=revision_no,
        snapshot_json=snapshot,
        snapshot_hash=snap_hash,
        submitted_at=datetime.now(UTC),
    )
    session.add(revision)
    session.flush()

    run = EvaluationRun(
        application_id=app.id,
        revision_no=revision_no,
        run_no=1,
        status="PENDING",
        policy_version=product.policy_version,
        model_version="score-v1",
    )
    session.add(run)
    session.flush()

    from_status = app.status
    app.status = new_status.value
    app.current_revision = revision_no
    app.active_run_id = run.id
    app.version += 1
    app.updated_at = datetime.now(UTC)

    job = Job(
        kind="evaluate_application",
        application_id=app.id,
        run_id=run.id,
        payload_json={
            "revision_no": revision_no,
            "snapshot_hash": snap_hash,
        },
        state="pending",
        attempts=0,
        available_at=datetime.now(UTC),
    )
    session.add(job)
    session.flush()
    session.add(
        AuditEvent(
            application_id=app.id,
            actor_id=actor_id,
            action="SUBMIT",
            from_status=from_status,
            to_status=new_status.value,
            revision_no=revision_no,
            metadata_json={"run_id": str(run.id), "job_id": str(job.id)},
        )
    )
    session.flush()
    return to_client_application(app, product)


def add_document(
    session: Session,
    *,
    app: Application,
    actor_id: UUID,
    kind: str,
    storage_key: str,
    content_hash: str,
    mime: str,
    size_bytes: int,
    expected_version: int,
) -> Document:
    if app.status not in {ApplicationStatus.DRAFT.value, ApplicationStatus.NEEDS_INFO.value}:
        raise ApiError(409, "INVALID_STATE", "Загрузка документов недоступна в текущем статусе")
    if app.version != expected_version:
        raise ApiError(
            409,
            "VERSION_CONFLICT",
            "Заявка уже изменилась. Обновите данные перед действием.",
        )
    allowed = {"FINANCIAL_SUMMARY", "EQUIPMENT_QUOTE"}
    if kind not in allowed:
        raise ApiError(422, "VALIDATION_ERROR", f"Недопустимый kind: {kind}")

    doc = Document(
        application_id=app.id,
        revision_no=app.current_revision,
        kind=kind,
        storage_key=storage_key,
        content_hash=content_hash,
        mime=mime,
        size_bytes=size_bytes,
        created_by=actor_id,
    )
    session.add(doc)
    app.version += 1
    app.updated_at = datetime.now(UTC)
    session.add(
        AuditEvent(
            application_id=app.id,
            actor_id=actor_id,
            action="UPLOAD_DOCUMENT",
            from_status=app.status,
            to_status=app.status,
            revision_no=app.current_revision,
            metadata_json={"kind": kind, "content_hash": content_hash},
        )
    )
    session.flush()
    return doc
