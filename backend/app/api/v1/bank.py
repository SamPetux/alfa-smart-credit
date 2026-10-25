"""Банковский кабинет API (B06)."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, Query, Response, status

from backend.app.applications import officer as bank
from backend.app.applications.idempotency import body_hash, lookup_idempotency, store_idempotency
from backend.app.identity.deps import DbSession, RequireAuth, RequireOfficerCsrf
from backend.app.schemas.applications import (
    BankApplication,
    BankApplicationList,
    OfficerDecisionRequest,
    RequestInfoBody,
)
from backend.app.schemas.common import VersionedCommand
from backend.app.schemas.enums import ApplicationStatus, ProductCode, Role
from backend.app.applications.errors import ApiError

router = APIRouter(prefix="/bank/applications", tags=["bank"])

IdempotencyKey = Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)]


def _require_officer(auth: RequireAuth) -> None:
    if auth.user.role != Role.OFFICER.value:
        raise ApiError(403, "FORBIDDEN", "Доступно только сотруднику банка")


@router.get("", response_model=BankApplicationList)
def list_bank_applications(
    db: DbSession,
    auth: RequireAuth,
    status_filter: Annotated[ApplicationStatus | None, Query(alias="status")] = None,
    product_code: ProductCode | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> BankApplicationList:
    _require_officer(auth)
    items = bank.list_bank_applications(
        db, status=status_filter, product_code=product_code, limit=limit
    )
    return BankApplicationList(items=items, next_cursor=None)


@router.get("/{application_id}", response_model=BankApplication)
def get_bank_application(
    application_id: UUID,
    db: DbSession,
    auth: RequireAuth,
) -> BankApplication:
    _require_officer(auth)
    app = bank.get_application(db, application_id)
    return bank.build_bank_dossier(db, app)


@router.post("/{application_id}/request-info", response_model=BankApplication)
def request_info(
    application_id: UUID,
    body: RequestInfoBody,
    response: Response,
    db: DbSession,
    auth: RequireOfficerCsrf,
    idempotency_key: IdempotencyKey,
) -> BankApplication:
    scope = f"request_info:{application_id}"
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
        return BankApplication.model_validate(existing.response_json)

    app = bank.get_application(db, application_id)
    result = bank.request_info(
        db,
        app=app,
        officer_id=auth.user.id,
        expected_version=body.expected_version,
        body=body,
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


@router.post("/{application_id}/decision", response_model=BankApplication)
def decide_application(
    application_id: UUID,
    body: OfficerDecisionRequest,
    response: Response,
    db: DbSession,
    auth: RequireOfficerCsrf,
    idempotency_key: IdempotencyKey,
) -> BankApplication:
    scope = f"decision:{application_id}"
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
        return BankApplication.model_validate(existing.response_json)

    app = bank.get_application(db, application_id)
    result = bank.decide(
        db,
        app=app,
        officer_id=auth.user.id,
        expected_version=body.expected_version,
        run_id=body.run_id,
        decision_type=body.type,
        candidate_hash=body.candidate_hash,
        reason_code=body.reason_code,
        comment=body.comment,
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


@router.post(
    "/{application_id}/retry-checks",
    response_model=BankApplication,
    status_code=status.HTTP_202_ACCEPTED,
)
def retry_checks(
    application_id: UUID,
    body: VersionedCommand,
    response: Response,
    db: DbSession,
    auth: RequireOfficerCsrf,
    idempotency_key: IdempotencyKey,
) -> BankApplication:
    scope = f"retry_checks:{application_id}"
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
        return BankApplication.model_validate(existing.response_json)

    app = bank.get_application(db, application_id)
    result = bank.retry_checks(
        db,
        app=app,
        officer_id=auth.user.id,
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
