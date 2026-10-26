"""GET объяснение по заявке — шаблонный помощник без LLM."""

from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import select

from backend.app.applications import service as apps
from backend.app.applications.errors import ApiError
from backend.app.db.models import RiskAssessment
from backend.app.explanations.assistant import explain_application
from backend.app.identity.deps import DbSession, RequireAuth
from backend.app.schemas.enums import Role

router = APIRouter(tags=["explain"])


@router.get("/applications/{application_id}/explain")
def explain_for_application(
    application_id: UUID,
    db: DbSession,
    auth: RequireAuth,
    topic: Annotated[
        Literal["general", "why", "next", "amount"],
        Query(description="Фокус шаблонного ответа"),
    ] = "general",
) -> dict:
    if auth.user.role != Role.CLIENT.value or auth.company_id is None:
        raise ApiError(403, "FORBIDDEN", "Объяснение доступно владельцу-клиенту")
    app = apps.get_owned_application(db, application_id, company_id=auth.company_id)

    reason_codes: list[str] = []
    recommendation: str | None = None
    if app.active_run_id is not None:
        risk = db.scalar(
            select(RiskAssessment).where(RiskAssessment.run_id == app.active_run_id)
        )
        if risk is not None:
            recommendation = risk.recommendation
            raw = risk.reasons_json or []
            reason_codes = [str(x) for x in raw if x is not None]

    return explain_application(
        status=app.status,
        reason_codes=reason_codes,
        recommendation=recommendation,
        topic=topic,
    )
