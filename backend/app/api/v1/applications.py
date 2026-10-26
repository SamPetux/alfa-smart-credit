"""Клиентские заявки: CRUD черновика, документы, submit (B04)."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, Form, Header, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select

from backend.app.applications import accept as offer_actions
from backend.app.applications import officer as bank_actions
from backend.app.applications import service as apps
from backend.app.applications.errors import ApiError
from backend.app.applications.idempotency import body_hash, lookup_idempotency, store_idempotency
from backend.app.applications.projections import to_client_application
from backend.app.core.config import get_settings
from backend.app.db.models import AuditEvent, Document, InfoRequest
from backend.app.documents.storage import store_upload
from backend.app.identity.deps import DbSession, RequireAuth, RequireClientCsrf
from backend.app.schemas.applications import (
    AgreementOut,
    ApplicationList,
    ClientApplication,
    CreateApplicationRequest,
    DraftPatch,
    InfoRequestOut,
    OfferCommand,
    OfferOut,
    ResubmitRequest,
    SimulateSignRequest,
)
from backend.app.schemas.common import VersionedCommand
from backend.app.schemas.enums import Role

router = APIRouter(prefix="/applications", tags=["applications"])

IdempotencyKey = Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)]


def _require_client_company(auth: RequireAuth) -> UUID:
    if auth.user.role != Role.CLIENT.value or auth.company_id is None:
        raise ApiError(403, "FORBIDDEN", "Доступно только клиенту с компанией")
    return auth.company_id


@router.get("", response_model=ApplicationList)
def list_applications(db: DbSession, auth: RequireAuth) -> ApplicationList:
    company_id = _require_client_company(auth)
    items = apps.list_company_applications(db, company_id=company_id)
    return ApplicationList(items=items, next_cursor=None)


@router.post("", response_model=ClientApplication, status_code=status.HTTP_201_CREATED)
def create_application(
    body: CreateApplicationRequest,
    response: Response,
    db: DbSession,
    auth: RequireClientCsrf,
    idempotency_key: IdempotencyKey,
) -> ClientApplication:
    assert auth.company_id is not None
    scope = f"create_application:{auth.company_id}"
    digest = body_hash(body.model_dump(mode="json"))
    existing = lookup_idempotency(
        db,
        actor_id=auth.user.id,
        command_scope=scope,
        key=idempotency_key,
        expected_body_hash=digest,
    )
    if existing is not None:
        response.status_code = existing.response_status
        return ClientApplication.model_validate(existing.response_json)

    result = apps.create_draft(
        db,
        company_id=auth.company_id,
        creator_id=auth.user.id,
        product_code=body.product_code,
    )
    payload = result.model_dump(mode="json")
    store_idempotency(
        db,
        actor_id=auth.user.id,
        command_scope=scope,
        key=idempotency_key,
        expected_body_hash=digest,
        response_status=201,
        response_json=payload,
    )
    return result


@router.get("/{application_id}", response_model=ClientApplication)
def get_application(
    application_id: UUID,
    db: DbSession,
    auth: RequireAuth,
) -> ClientApplication:
    company_id = _require_client_company(auth)
    app = apps.get_owned_application(db, application_id, company_id=company_id)
    return to_client_application(app, apps.get_product(db, app.product_id))


@router.patch("/{application_id}", response_model=ClientApplication)
def patch_application(
    application_id: UUID,
    body: DraftPatch,
    db: DbSession,
    auth: RequireClientCsrf,
) -> ClientApplication:
    assert auth.company_id is not None
    app = apps.get_owned_application(db, application_id, company_id=auth.company_id)
    return apps.patch_draft(
        db,
        app=app,
        actor_id=auth.user.id,
        expected_version=body.expected_version,
        draft_fields=body.draft_fields,
    )


@router.post(
    "/{application_id}/documents",
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    application_id: UUID,
    db: DbSession,
    auth: RequireClientCsrf,
    idempotency_key: IdempotencyKey,
    kind: Annotated[str, Form()],
    expected_version: Annotated[int, Form(ge=1)],
    file: Annotated[UploadFile, File()],
) -> dict:
    assert auth.company_id is not None
    data = await file.read()
    mime = file.content_type or "application/octet-stream"
    scope = f"upload_document:{application_id}"
    digest = body_hash(
        {
            "kind": kind,
            "expected_version": expected_version,
            "content_sha256": hashlib.sha256(data).hexdigest(),
        }
    )
    existing = lookup_idempotency(
        db,
        actor_id=auth.user.id,
        command_scope=scope,
        key=idempotency_key,
        expected_body_hash=digest,
    )
    if existing is not None:
        return existing.response_json

    app = apps.get_owned_application(db, application_id, company_id=auth.company_id)
    storage_key, content_hash, size_bytes = store_upload(
        data=data,
        mime=mime,
        application_id=str(application_id),
    )
    doc = apps.add_document(
        db,
        app=app,
        actor_id=auth.user.id,
        kind=kind,
        storage_key=storage_key,
        content_hash=content_hash,
        mime=mime,
        size_bytes=size_bytes,
        expected_version=expected_version,
    )
    payload = {
        "id": str(doc.id),
        "kind": doc.kind,
        "content_hash": doc.content_hash,
        "version": app.version,
    }
    store_idempotency(
        db,
        actor_id=auth.user.id,
        command_scope=scope,
        key=idempotency_key,
        expected_body_hash=digest,
        response_status=201,
        response_json=payload,
    )
    return payload


@router.post(
    "/{application_id}/submit",
    response_model=ClientApplication,
    status_code=status.HTTP_202_ACCEPTED,
)
def submit_application(
    application_id: UUID,
    body: VersionedCommand,
    response: Response,
    db: DbSession,
    auth: RequireClientCsrf,
    idempotency_key: IdempotencyKey,
) -> ClientApplication:
    assert auth.company_id is not None
    scope = f"submit:{application_id}"
    digest = body_hash(body.model_dump(mode="json"))
    existing = lookup_idempotency(
        db,
        actor_id=auth.user.id,
        command_scope=scope,
        key=idempotency_key,
        expected_body_hash=digest,
    )
    if existing is not None:
        response.status_code = existing.response_status
        return ClientApplication.model_validate(existing.response_json)

    app = apps.get_owned_application(db, application_id, company_id=auth.company_id)
    result = apps.submit_application(
        db,
        app=app,
        actor_id=auth.user.id,
        expected_version=body.expected_version,
    )
    payload = result.model_dump(mode="json")
    store_idempotency(
        db,
        actor_id=auth.user.id,
        command_scope=scope,
        key=idempotency_key,
        expected_body_hash=digest,
        response_status=202,
        response_json=payload,
    )
    return result


@router.get("/{application_id}/documents/{doc_id}")
def download_document(
    application_id: UUID,
    doc_id: UUID,
    db: DbSession,
    auth: RequireAuth,
) -> FileResponse:
    """Скачивание своего документа (attachment). Каталог upload не публичный static."""
    company_id = _require_client_company(auth)
    apps.get_owned_application(db, application_id, company_id=company_id)
    doc = db.get(Document, doc_id)
    if doc is None or doc.application_id != application_id:
        raise ApiError(404, "NOT_FOUND", "Документ не найден")
    path = Path(get_settings().documents_dir) / doc.storage_key
    if not path.is_file():
        raise ApiError(404, "NOT_FOUND", "Файл документа отсутствует в хранилище")
    return FileResponse(
        path,
        media_type=doc.mime,
        filename=f"{doc.kind.lower()}-{doc.id}.bin",
        content_disposition_type="attachment",
        headers={"X-Content-Type-Options": "nosniff"},
    )


@router.get("/{application_id}/history")
def get_application_history(
    application_id: UUID,
    db: DbSession,
    auth: RequireAuth,
) -> dict:
    """Безопасная клиентская история: без токенов и содержимого документов."""
    company_id = _require_client_company(auth)
    apps.get_owned_application(db, application_id, company_id=company_id)
    rows = db.scalars(
        select(AuditEvent)
        .where(AuditEvent.application_id == application_id)
        .order_by(AuditEvent.created_at.asc())
    ).all()
    events = [
        {
            "action": e.action,
            "from_status": e.from_status,
            "to_status": e.to_status,
            "revision_no": e.revision_no,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in rows
    ]
    return {"events": events}


@router.get("/{application_id}/info-request")
def get_info_request(
    application_id: UUID,
    db: DbSession,
    auth: RequireAuth,
) -> InfoRequestOut | None:
    company_id = _require_client_company(auth)
    apps.get_owned_application(db, application_id, company_id=company_id)
    row = db.scalar(
        select(InfoRequest).where(
            InfoRequest.application_id == application_id,
            InfoRequest.status == "OPEN",
        )
    )
    if row is None:
        return None
    return InfoRequestOut(
        id=row.id,
        fields=list(row.fields_json or []),
        document_kinds=list(row.document_kinds_json or []),
        message=row.message,
        status=row.status,
    )


@router.get("/{application_id}/offer", response_model=OfferOut | None)
def get_offer(
    application_id: UUID,
    db: DbSession,
    auth: RequireAuth,
) -> OfferOut | None:
    company_id = _require_client_company(auth)
    app = apps.get_owned_application(db, application_id, company_id=company_id)
    return offer_actions.get_offer(db, app)


@router.post("/{application_id}/offer/accept", response_model=ClientApplication)
def accept_offer(
    application_id: UUID,
    body: OfferCommand,
    response: Response,
    db: DbSession,
    auth: RequireClientCsrf,
    idempotency_key: IdempotencyKey,
) -> ClientApplication:
    assert auth.company_id is not None
    scope = f"accept_offer:{application_id}"
    digest = body_hash(body.model_dump(mode="json"))
    existing = lookup_idempotency(
        db,
        actor_id=auth.user.id,
        command_scope=scope,
        key=idempotency_key,
        expected_body_hash=digest,
    )
    if existing is not None:
        response.status_code = existing.response_status
        return ClientApplication.model_validate(existing.response_json)

    app = apps.get_owned_application(db, application_id, company_id=auth.company_id)
    result = offer_actions.accept_offer(
        db,
        app=app,
        actor_id=auth.user.id,
        expected_version=body.expected_version,
        offer_id=body.offer_id,
    )
    payload = result.model_dump(mode="json")
    store_idempotency(
        db,
        actor_id=auth.user.id,
        command_scope=scope,
        key=idempotency_key,
        expected_body_hash=digest,
        response_status=200,
        response_json=payload,
    )
    return result


@router.post("/{application_id}/offer/decline", response_model=ClientApplication)
def decline_offer(
    application_id: UUID,
    body: OfferCommand,
    response: Response,
    db: DbSession,
    auth: RequireClientCsrf,
    idempotency_key: IdempotencyKey,
) -> ClientApplication:
    assert auth.company_id is not None
    scope = f"decline_offer:{application_id}"
    digest = body_hash(body.model_dump(mode="json"))
    existing = lookup_idempotency(
        db,
        actor_id=auth.user.id,
        command_scope=scope,
        key=idempotency_key,
        expected_body_hash=digest,
    )
    if existing is not None:
        response.status_code = existing.response_status
        return ClientApplication.model_validate(existing.response_json)

    app = apps.get_owned_application(db, application_id, company_id=auth.company_id)
    result = offer_actions.decline_offer(
        db,
        app=app,
        actor_id=auth.user.id,
        expected_version=body.expected_version,
        offer_id=body.offer_id,
    )
    payload = result.model_dump(mode="json")
    store_idempotency(
        db,
        actor_id=auth.user.id,
        command_scope=scope,
        key=idempotency_key,
        expected_body_hash=digest,
        response_status=200,
        response_json=payload,
    )
    return result


@router.get("/{application_id}/agreement", response_model=AgreementOut | None)
def get_agreement(
    application_id: UUID,
    db: DbSession,
    auth: RequireAuth,
) -> AgreementOut | None:
    company_id = _require_client_company(auth)
    app = apps.get_owned_application(db, application_id, company_id=company_id)
    return offer_actions.get_agreement(db, app)


@router.post(
    "/{application_id}/agreement/simulate-sign",
    response_model=ClientApplication,
    status_code=status.HTTP_202_ACCEPTED,
)
def simulate_sign(
    application_id: UUID,
    body: SimulateSignRequest,
    response: Response,
    db: DbSession,
    auth: RequireClientCsrf,
    idempotency_key: IdempotencyKey,
) -> ClientApplication:
    assert auth.company_id is not None
    scope = f"simulate_sign:{application_id}"
    digest = body_hash(body.model_dump(mode="json"))
    existing = lookup_idempotency(
        db,
        actor_id=auth.user.id,
        command_scope=scope,
        key=idempotency_key,
        expected_body_hash=digest,
    )
    if existing is not None:
        response.status_code = existing.response_status
        return ClientApplication.model_validate(existing.response_json)

    app = apps.get_owned_application(db, application_id, company_id=auth.company_id)
    result = offer_actions.simulate_sign(
        db,
        app=app,
        actor_id=auth.user.id,
        expected_version=body.expected_version,
        agreement_id=body.agreement_id,
        content_hash=body.content_hash,
    )
    payload = result.model_dump(mode="json")
    store_idempotency(
        db,
        actor_id=auth.user.id,
        command_scope=scope,
        key=idempotency_key,
        expected_body_hash=digest,
        response_status=202,
        response_json=payload,
    )
    return result


@router.post(
    "/{application_id}/resubmit",
    response_model=ClientApplication,
    status_code=status.HTTP_202_ACCEPTED,
)
def resubmit_application(
    application_id: UUID,
    body: ResubmitRequest,
    response: Response,
    db: DbSession,
    auth: RequireClientCsrf,
    idempotency_key: IdempotencyKey,
) -> ClientApplication:
    assert auth.company_id is not None
    scope = f"resubmit:{application_id}"
    digest = body_hash(body.model_dump(mode="json"))
    existing = lookup_idempotency(
        db,
        actor_id=auth.user.id,
        command_scope=scope,
        key=idempotency_key,
        expected_body_hash=digest,
    )
    if existing is not None:
        response.status_code = existing.response_status
        return ClientApplication.model_validate(existing.response_json)

    app = apps.get_owned_application(db, application_id, company_id=auth.company_id)
    result = bank_actions.resubmit_after_info(
        db,
        app=app,
        actor_id=auth.user.id,
        expected_version=body.expected_version,
        info_request_id=body.info_request_id,
    )
    payload = result.model_dump(mode="json")
    store_idempotency(
        db,
        actor_id=auth.user.id,
        command_scope=scope,
        key=idempotency_key,
        expected_body_hash=digest,
        response_status=202,
        response_json=payload,
    )
    return result
