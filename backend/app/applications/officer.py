"""Банковские действия B06: очередь, досье, уточнение, решение, retry."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.applications.errors import ApiError
from backend.app.applications.hashes import canonical_hash
from backend.app.applications.projections import (
    NEXT_ACTION,
    allowed_actions_for_officer,
    to_bank_application,
    to_client_application,
)
from backend.app.applications.service import (
    document_kinds_for_app,
    get_product,
    snapshot_hash,
)
from backend.app.db.models import (
    Application,
    ApplicationRevision,
    AuditEvent,
    Company,
    Decision,
    EvaluationRun,
    InfoRequest,
    IntegrationCheck,
    Job,
    Offer,
    RiskAssessment,
)
from backend.app.schemas.applications import BankApplication, ClientApplication, RequestInfoBody
from backend.app.schemas.enums import ApplicationStatus, ProductCode, Role, WorkflowCommand
from backend.app.workflow.transitions import IllegalTransitionError, next_status


def get_application(session: Session, application_id: UUID) -> Application:
    app = session.get(Application, application_id)
    if app is None:
        raise ApiError(404, "NOT_FOUND", "Заявка не найдена")
    return app


def list_bank_applications(
    session: Session,
    *,
    status: ApplicationStatus | None = None,
    product_code: ProductCode | None = None,
    limit: int = 50,
) -> list[BankApplication]:
    stmt = select(Application).order_by(Application.updated_at.desc()).limit(limit)
    if status is not None:
        stmt = stmt.where(Application.status == status.value)
    rows = session.scalars(stmt).all()
    items: list[BankApplication] = []
    for app in rows:
        product = get_product(session, app.product_id)
        if product_code is not None and product.code != product_code.value:
            continue
        items.append(build_bank_dossier(session, app))
    return items


def build_bank_dossier(session: Session, app: Application) -> BankApplication:
    product = get_product(session, app.product_id)
    company = session.get(Company, app.company_id)
    risk_summary = None
    checks: list[dict[str, Any]] = []
    if app.active_run_id is not None:
        risk = session.scalar(
            select(RiskAssessment).where(RiskAssessment.run_id == app.active_run_id)
        )
        if risk is not None:
            risk_summary = {
                "score": risk.score,
                "band": risk.band,
                "recommendation": risk.recommendation,
                "reasons": risk.reasons_json,
                "candidate": risk.candidate_json,
                "candidate_hash": canonical_hash(risk.candidate_json)
                if risk.candidate_json
                else None,
                "affordability": risk.affordability_json,
                "factors": risk.factors_json,
            }
        checks = [
            {
                "source": c.source,
                "outcome": c.outcome,
                "attempt_count": c.attempt_count,
                "observed_at": c.observed_at.isoformat() if c.observed_at else None,
            }
            for c in session.scalars(
                select(IntegrationCheck)
                .where(IntegrationCheck.run_id == app.active_run_id)
                .order_by(IntegrationCheck.attempt_count.asc())
            ).all()
        ]

    revisions = [
        {
            "revision_no": r.revision_no,
            "snapshot_hash": r.snapshot_hash,
            "submitted_at": r.submitted_at.isoformat(),
        }
        for r in session.scalars(
            select(ApplicationRevision)
            .where(ApplicationRevision.application_id == app.id)
            .order_by(ApplicationRevision.revision_no.asc())
        ).all()
    ]
    audit = [
        {
            "action": e.action,
            "from_status": e.from_status,
            "to_status": e.to_status,
            "revision_no": e.revision_no,
            "created_at": e.created_at.isoformat(),
        }
        for e in session.scalars(
            select(AuditEvent)
            .where(AuditEvent.application_id == app.id)
            .order_by(AuditEvent.created_at.asc())
        ).all()
    ]
    status = ApplicationStatus(app.status)
    return to_bank_application(
        app,
        product=product,
        company=company,
        risk_summary=risk_summary,
        checks=checks,
        revisions=revisions,
        audit=audit,
        allowed=allowed_actions_for_officer(status, risk_summary),
        next_action=NEXT_ACTION[status],
    )


def request_info(
    session: Session,
    *,
    app: Application,
    officer_id: UUID,
    expected_version: int,
    body: RequestInfoBody,
) -> BankApplication:
    if app.version != expected_version:
        raise ApiError(
            409,
            "VERSION_CONFLICT",
            "Заявка уже изменилась. Обновите данные перед действием.",
        )
    try:
        new_status = next_status(
            ApplicationStatus(app.status),
            WorkflowCommand.REQUEST_INFO,
            actor=Role.OFFICER,
        )
    except IllegalTransitionError as exc:
        raise ApiError(409, "INVALID_STATE", str(exc)) from exc

    # Закрыть предыдущие открытые запросы
    open_reqs = session.scalars(
        select(InfoRequest).where(
            InfoRequest.application_id == app.id,
            InfoRequest.status == "OPEN",
        )
    ).all()
    for req in open_reqs:
        req.status = "SUPERSEDED"
        req.closed_at = datetime.now(UTC)

    session.add(
        InfoRequest(
            application_id=app.id,
            based_on_run_id=app.active_run_id,
            fields_json=list(body.fields),
            document_kinds_json=list(body.document_kinds),
            message=body.message,
            status="OPEN",
            actor_id=officer_id,
        )
    )
    from_status = app.status
    app.status = new_status.value
    app.version += 1
    app.updated_at = datetime.now(UTC)
    session.add(
        AuditEvent(
            application_id=app.id,
            actor_id=officer_id,
            action="REQUEST_INFO",
            from_status=from_status,
            to_status=new_status.value,
            revision_no=app.current_revision,
            metadata_json={"fields": body.fields, "message": body.message},
        )
    )
    session.flush()
    return build_bank_dossier(session, app)


def decide(
    session: Session,
    *,
    app: Application,
    officer_id: UUID,
    expected_version: int,
    run_id: UUID,
    decision_type: str,
    candidate_hash: str | None,
    reason_code: str | None,
    comment: str | None,
) -> BankApplication:
    if app.version != expected_version:
        raise ApiError(
            409,
            "VERSION_CONFLICT",
            "Заявка уже изменилась. Обновите данные перед действием.",
        )
    if app.active_run_id != run_id:
        raise ApiError(409, "STALE_RUN", "run_id не совпадает с активным расчётом")

    risk = session.scalar(select(RiskAssessment).where(RiskAssessment.run_id == run_id))
    if risk is None:
        raise ApiError(409, "INVALID_STATE", "Нет результата risk для run")

    if decision_type == "APPROVE_OFFER":
        if risk.recommendation != "OFFER" or not risk.candidate_json:
            raise ApiError(
                409,
                "INVALID_STATE",
                "Подтверждение доступно только для рекомендации OFFER с candidate",
            )
        expected_hash = canonical_hash(risk.candidate_json)
        if not candidate_hash or candidate_hash != expected_hash:
            raise ApiError(
                409,
                "CANDIDATE_MISMATCH",
                "candidate_hash не совпадает с действующей рекомендацией",
            )
        command = WorkflowCommand.APPROVE_OFFER
    elif decision_type == "REJECT":
        if not reason_code or not comment:
            raise ApiError(422, "VALIDATION_ERROR", "Для отказа нужны reason_code и comment")
        command = WorkflowCommand.REJECT
    else:
        raise ApiError(422, "VALIDATION_ERROR", f"Неизвестный тип решения: {decision_type}")

    try:
        new_status = next_status(
            ApplicationStatus(app.status),
            command,
            actor=Role.OFFICER,
        )
    except IllegalTransitionError as exc:
        raise ApiError(409, "INVALID_STATE", str(exc)) from exc

    decision = Decision(
        application_id=app.id,
        run_id=run_id,
        type=decision_type,
        officer_id=officer_id,
        reason_code=reason_code,
        comment=comment,
    )
    session.add(decision)
    session.flush()

    if decision_type == "APPROVE_OFFER":
        session.add(
            Offer(
                application_id=app.id,
                decision_id=decision.id,
                revision_no=app.current_revision,
                terms_json=dict(risk.candidate_json),
                status="ACTIVE",
            )
        )

    from_status = app.status
    app.status = new_status.value
    app.version += 1
    app.updated_at = datetime.now(UTC)
    session.add(
        AuditEvent(
            application_id=app.id,
            actor_id=officer_id,
            action=decision_type,
            from_status=from_status,
            to_status=new_status.value,
            revision_no=app.current_revision,
            metadata_json={
                "run_id": str(run_id),
                "reason_code": reason_code,
                "candidate_hash": candidate_hash,
            },
        )
    )
    session.flush()
    return build_bank_dossier(session, app)


def retry_checks(
    session: Session,
    *,
    app: Application,
    officer_id: UUID,
    expected_version: int,
) -> BankApplication:
    if app.version != expected_version:
        raise ApiError(
            409,
            "VERSION_CONFLICT",
            "Заявка уже изменилась. Обновите данные перед действием.",
        )
    try:
        new_status = next_status(
            ApplicationStatus(app.status),
            WorkflowCommand.RETRY_CHECKS,
            actor=Role.OFFICER,
        )
    except IllegalTransitionError as exc:
        raise ApiError(409, "INVALID_STATE", str(exc)) from exc

    product = get_product(session, app.product_id)
    max_run = session.scalar(
        select(EvaluationRun.run_no)
        .where(
            EvaluationRun.application_id == app.id,
            EvaluationRun.revision_no == app.current_revision,
        )
        .order_by(EvaluationRun.run_no.desc())
        .limit(1)
    )
    run_no = int(max_run or 0) + 1
    run = EvaluationRun(
        application_id=app.id,
        revision_no=app.current_revision,
        run_no=run_no,
        status="PENDING",
        policy_version=product.policy_version,
        model_version="score-v1",
    )
    session.add(run)
    session.flush()

    revision = session.scalar(
        select(ApplicationRevision).where(
            ApplicationRevision.application_id == app.id,
            ApplicationRevision.revision_no == app.current_revision,
        )
    )
    snap_hash = revision.snapshot_hash if revision else ""

    job = Job(
        kind="evaluate_application",
        application_id=app.id,
        run_id=run.id,
        payload_json={"revision_no": app.current_revision, "snapshot_hash": snap_hash},
        state="pending",
        attempts=0,
        available_at=datetime.now(UTC),
    )
    session.add(job)

    from_status = app.status
    app.status = new_status.value
    app.active_run_id = run.id
    app.version += 1
    app.updated_at = datetime.now(UTC)
    session.add(
        AuditEvent(
            application_id=app.id,
            actor_id=officer_id,
            action="RETRY_CHECKS",
            from_status=from_status,
            to_status=new_status.value,
            revision_no=app.current_revision,
            metadata_json={"run_id": str(run.id), "job_id": str(job.id)},
        )
    )
    session.flush()
    return build_bank_dossier(session, app)


def resubmit_after_info(
    session: Session,
    *,
    app: Application,
    actor_id: UUID,
    expected_version: int,
    info_request_id: UUID,
) -> ClientApplication:
    if app.version != expected_version:
        raise ApiError(
            409,
            "VERSION_CONFLICT",
            "Заявка уже изменилась. Обновите данные перед действием.",
        )
    info = session.get(InfoRequest, info_request_id)
    if info is None or info.application_id != app.id or info.status != "OPEN":
        raise ApiError(409, "INVALID_STATE", "Нет активного info_request")

    try:
        new_status = next_status(
            ApplicationStatus(app.status),
            WorkflowCommand.RESUBMIT,
            actor=Role.CLIENT,
        )
    except IllegalTransitionError as exc:
        raise ApiError(409, "INVALID_STATE", str(exc)) from exc

    product = get_product(session, app.product_id)
    docs = document_kinds_for_app(session, app.id)
    from backend.app.applications.validation import validate_draft_for_submit
    from backend.app.schemas.enums import ProductCode

    errors = validate_draft_for_submit(
        app.draft_json or {}, ProductCode(product.code), docs
    )
    if errors:
        raise ApiError(
            422,
            "VALIDATION_ERROR",
            "Не хватает обязательных данных для повторной отправки",
            field_errors=errors,
        )

    revision_no = app.current_revision + 1
    snapshot = {
        "product_code": product.code,
        "draft": dict(app.draft_json or {}),
        "document_kinds": sorted(docs),
        "info_request_id": str(info_request_id),
    }
    snap_hash = snapshot_hash(snapshot)
    session.add(
        ApplicationRevision(
            application_id=app.id,
            revision_no=revision_no,
            snapshot_json=snapshot,
            snapshot_hash=snap_hash,
            submitted_at=datetime.now(UTC),
        )
    )
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

    job = Job(
        kind="evaluate_application",
        application_id=app.id,
        run_id=run.id,
        payload_json={"revision_no": revision_no, "snapshot_hash": snap_hash},
        state="pending",
        attempts=0,
        available_at=datetime.now(UTC),
    )
    session.add(job)

    info.status = "CLOSED"
    info.closed_at = datetime.now(UTC)

    from_status = app.status
    app.status = new_status.value
    app.current_revision = revision_no
    app.active_run_id = run.id
    app.version += 1
    app.updated_at = datetime.now(UTC)
    session.add(
        AuditEvent(
            application_id=app.id,
            actor_id=actor_id,
            action="RESUBMIT",
            from_status=from_status,
            to_status=new_status.value,
            revision_no=revision_no,
            metadata_json={"run_id": str(run.id), "info_request_id": str(info_request_id)},
        )
    )
    session.flush()
    return to_client_application(app, product)
