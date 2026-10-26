"""B07: принятие/отклонение офера, agreement и имитация подписи."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.applications.errors import ApiError
from backend.app.applications.projections import to_client_application
from backend.app.applications.service import get_product
from backend.app.core.config import get_settings
from backend.app.db.models import (
    Agreement,
    Application,
    AuditEvent,
    Job,
    Offer,
)
from backend.app.schemas.applications import (
    AgreementOut,
    ClientApplication,
    OfferOut,
)
from backend.app.schemas.enums import ApplicationStatus, Role, WorkflowCommand
from backend.app.workflow.transitions import IllegalTransitionError, next_status


def _active_offer(session: Session, application_id: UUID) -> Offer | None:
    return session.scalar(
        select(Offer)
        .where(
            Offer.application_id == application_id,
            Offer.status.in_(("ACTIVE", "ACCEPTED")),
        )
        .order_by(Offer.created_at.desc())
        .limit(1)
    )


def get_offer(session: Session, app: Application) -> OfferOut | None:
    offer = _active_offer(session, app.id)
    if offer is None:
        return None
    return OfferOut(
        id=offer.id,
        status=offer.status,
        revision_no=offer.revision_no,
        terms=dict(offer.terms_json or {}),
        created_at=offer.created_at,
    )


def get_agreement(session: Session, app: Application) -> AgreementOut | None:
    agreement = session.scalar(
        select(Agreement)
        .join(Offer, Offer.id == Agreement.offer_id)
        .where(Offer.application_id == app.id)
        .order_by(Agreement.accepted_at.desc())
        .limit(1)
    )
    if agreement is None:
        return None
    return AgreementOut(
        id=agreement.id,
        offer_id=agreement.offer_id,
        content_hash=agreement.content_hash,
        accepted_at=agreement.accepted_at,
        signed_at=agreement.signed_at,
        is_simulation=bool(agreement.is_simulation),
        document_text=_read_agreement_body(agreement.storage_key),
    )


def _build_agreement_document(*, app_id: UUID, offer: Offer) -> bytes:
    payload: dict[str, Any] = {
        "document_type": "credit_agreement_simulation",
        "is_simulation": True,
        "application_id": str(app_id),
        "offer_id": str(offer.id),
        "revision_no": offer.revision_no,
        "terms": offer.terms_json,
        "notice": (
            "Учебная имитация. Не является юридически значимым договором "
            "и не влечёт реальной выдачи средств."
        ),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode(
        "utf-8"
    )


def _store_agreement_bytes(*, application_id: UUID, data: bytes) -> tuple[str, str]:
    content_hash = hashlib.sha256(data).hexdigest()
    key = f"{application_id}/agreements/{content_hash[:16]}.json"
    root = get_settings().documents_dir
    from pathlib import Path

    path = Path(root) / key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return key, content_hash


def _read_agreement_body(storage_key: str) -> str:
    from pathlib import Path

    path = Path(get_settings().documents_dir) / storage_key
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def accept_offer(
    session: Session,
    *,
    app: Application,
    actor_id: UUID,
    expected_version: int,
    offer_id: UUID,
) -> ClientApplication:
    if app.version != expected_version:
        raise ApiError(
            409,
            "VERSION_CONFLICT",
            "Заявка уже изменилась. Обновите данные перед действием.",
        )

    offer = session.get(Offer, offer_id)
    if offer is None or offer.application_id != app.id or offer.status != "ACTIVE":
        raise ApiError(409, "INVALID_STATE", "Нет активного предложения для принятия")

    try:
        new_status = next_status(
            ApplicationStatus(app.status),
            WorkflowCommand.ACCEPT_OFFER,
            actor=Role.CLIENT,
        )
    except IllegalTransitionError as exc:
        raise ApiError(409, "INVALID_STATE", str(exc)) from exc

    existing = session.scalar(select(Agreement).where(Agreement.offer_id == offer.id))
    if existing is not None:
        raise ApiError(409, "INVALID_STATE", "Соглашение по этому предложению уже создано")

    doc_bytes = _build_agreement_document(app_id=app.id, offer=offer)
    storage_key, content_hash = _store_agreement_bytes(
        application_id=app.id, data=doc_bytes
    )
    now = datetime.now(UTC)
    agreement = Agreement(
        offer_id=offer.id,
        content_hash=content_hash,
        storage_key=storage_key,
        accepted_at=now,
        is_simulation=True,
    )
    session.add(agreement)
    offer.status = "ACCEPTED"

    from_status = app.status
    app.status = new_status.value
    app.version += 1
    app.updated_at = now
    session.add(
        AuditEvent(
            application_id=app.id,
            actor_id=actor_id,
            action="ACCEPT_OFFER",
            from_status=from_status,
            to_status=new_status.value,
            revision_no=app.current_revision,
            metadata_json={
                "offer_id": str(offer.id),
                "agreement_content_hash": content_hash,
            },
        )
    )
    session.flush()
    return to_client_application(app, get_product(session, app.product_id))


def decline_offer(
    session: Session,
    *,
    app: Application,
    actor_id: UUID,
    expected_version: int,
    offer_id: UUID,
) -> ClientApplication:
    if app.version != expected_version:
        raise ApiError(
            409,
            "VERSION_CONFLICT",
            "Заявка уже изменилась. Обновите данные перед действием.",
        )

    offer = session.get(Offer, offer_id)
    if offer is None or offer.application_id != app.id or offer.status != "ACTIVE":
        raise ApiError(409, "INVALID_STATE", "Нет активного предложения для отклонения")

    try:
        new_status = next_status(
            ApplicationStatus(app.status),
            WorkflowCommand.DECLINE_OFFER,
            actor=Role.CLIENT,
        )
    except IllegalTransitionError as exc:
        raise ApiError(409, "INVALID_STATE", str(exc)) from exc

    offer.status = "DECLINED"
    from_status = app.status
    app.status = new_status.value
    app.version += 1
    app.updated_at = datetime.now(UTC)
    session.add(
        AuditEvent(
            application_id=app.id,
            actor_id=actor_id,
            action="DECLINE_OFFER",
            from_status=from_status,
            to_status=new_status.value,
            revision_no=app.current_revision,
            metadata_json={"offer_id": str(offer.id)},
        )
    )
    session.flush()
    return to_client_application(app, get_product(session, app.product_id))


def simulate_sign(
    session: Session,
    *,
    app: Application,
    actor_id: UUID,
    expected_version: int,
    agreement_id: UUID,
    content_hash: str,
) -> ClientApplication:
    if app.version != expected_version:
        raise ApiError(
            409,
            "VERSION_CONFLICT",
            "Заявка уже изменилась. Обновите данные перед действием.",
        )

    agreement = session.get(Agreement, agreement_id)
    if agreement is None:
        raise ApiError(404, "NOT_FOUND", "Соглашение не найдено")

    offer = session.get(Offer, agreement.offer_id)
    if offer is None or offer.application_id != app.id:
        raise ApiError(409, "INVALID_STATE", "Соглашение не относится к этой заявке")

    if agreement.content_hash != content_hash:
        raise ApiError(
            409,
            "HASH_MISMATCH",
            "content_hash не совпадает с неизменяемым документом соглашения",
        )

    if agreement.signed_at is not None:
        raise ApiError(409, "INVALID_STATE", "Соглашение уже подписано")

    try:
        new_status = next_status(
            ApplicationStatus(app.status),
            WorkflowCommand.SIMULATE_SIGN,
            actor=Role.CLIENT,
        )
    except IllegalTransitionError as exc:
        raise ApiError(409, "INVALID_STATE", str(exc)) from exc

    now = datetime.now(UTC)
    agreement.signed_at = now
    agreement.signed_by = actor_id

    amount_raw = (offer.terms_json or {}).get("amount")
    if amount_raw is None:
        raise ApiError(409, "INVALID_STATE", "В условиях предложения нет amount")

    job = Job(
        kind="simulate_disbursement",
        application_id=app.id,
        run_id=None,
        payload_json={
            "agreement_id": str(agreement.id),
            "offer_id": str(offer.id),
            "amount": str(amount_raw),
        },
        state="pending",
        attempts=0,
        available_at=now,
    )
    session.add(job)

    from_status = app.status
    app.status = new_status.value
    app.version += 1
    app.updated_at = now
    session.add(
        AuditEvent(
            application_id=app.id,
            actor_id=actor_id,
            action="SIMULATE_SIGN",
            from_status=from_status,
            to_status=new_status.value,
            revision_no=app.current_revision,
            metadata_json={
                "agreement_id": str(agreement.id),
                "content_hash": content_hash,
                "job_id": str(job.id),
                "is_simulation": True,
            },
        )
    )
    session.flush()
    return to_client_application(app, get_product(session, app.product_id))
