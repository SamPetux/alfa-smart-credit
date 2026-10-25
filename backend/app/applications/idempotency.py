"""Idempotency-Key: actor + scope + key → сохранённый ответ."""

from __future__ import annotations

import hashlib
import json
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.applications.errors import ApiError
from backend.app.db.models import IdempotencyRecord


def body_hash(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def lookup_idempotency(
    session: Session,
    *,
    actor_id: UUID,
    command_scope: str,
    key: str,
    expected_body_hash: str,
) -> IdempotencyRecord | None:
    row = session.scalar(
        select(IdempotencyRecord).where(
            IdempotencyRecord.actor_id == actor_id,
            IdempotencyRecord.command_scope == command_scope,
            IdempotencyRecord.idempotency_key == key,
        )
    )
    if row is None:
        return None
    if row.body_hash != expected_body_hash:
        raise ApiError(
            409,
            "IDEMPOTENCY_CONFLICT",
            "Idempotency-Key уже использован с другим телом запроса.",
        )
    return row


def store_idempotency(
    session: Session,
    *,
    actor_id: UUID,
    command_scope: str,
    key: str,
    expected_body_hash: str,
    response_status: int,
    response_json: dict[str, Any],
) -> None:
    session.add(
        IdempotencyRecord(
            actor_id=actor_id,
            command_scope=command_scope,
            idempotency_key=key,
            body_hash=expected_body_hash,
            response_status=response_status,
            response_json=response_json,
        )
    )
