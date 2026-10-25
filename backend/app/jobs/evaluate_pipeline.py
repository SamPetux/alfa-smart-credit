"""Обработка job evaluate_application: симуляторы → risk → статусы."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import Settings, get_settings
from backend.app.db.models import (
    Application,
    ApplicationRevision,
    AuditEvent,
    Company,
    EvaluationRun,
    InfoRequest,
    IntegrationCheck,
    Job,
    RiskAssessment,
)
from backend.app.integrations.fixtures import resolve_scenario
from backend.app.integrations.simulators import fetch_bureau, fetch_registry
from backend.app.jobs.claim import mark_job_done, requeue_job
from backend.app.risk import (
    FeatureBuildError,
    RiskContractError,
    build_risk_input,
    evaluate,
)
from backend.app.schemas.enums import ApplicationStatus, RiskRecommendation, WorkflowCommand
from backend.app.schemas.risk import RiskResult
from backend.app.workflow.transitions import next_status

log = logging.getLogger("worker.evaluate")

_RETRY_DELAYS = (1, 3, 3)


def _retry_delay(attempts: int) -> int:
    idx = max(0, min(attempts - 1, len(_RETRY_DELAYS) - 1))
    return _RETRY_DELAYS[idx]


def _serialize_result(result: RiskResult) -> dict[str, Any]:
    return result.model_dump(mode="json")


def _append_audit(
    session: Session,
    *,
    application_id: UUID,
    action: str,
    from_status: str | None,
    to_status: str | None,
    revision_no: int | None,
    metadata: dict[str, Any],
) -> None:
    session.add(
        AuditEvent(
            application_id=application_id,
            actor_id=None,
            action=action,
            from_status=from_status,
            to_status=to_status,
            revision_no=revision_no,
            metadata_json=metadata,
        )
    )


def process_evaluate_job(
    session: Session,
    job: Job,
    *,
    settings: Settings | None = None,
) -> str:
    """Вернуть итог: completed|requeued|obsolete|failed."""
    settings = settings or get_settings()
    lease_token = job.lease_token
    if lease_token is None or job.run_id is None:
        job.state = "failed"
        job.last_error = "invalid_job"
        job.lease_token = None
        job.lease_until = None
        return "failed"

    app = session.get(Application, job.application_id)
    run = session.get(EvaluationRun, job.run_id)
    if app is None or run is None:
        mark_job_done(session, job, lease_token=lease_token, state="failed", last_error="missing_app_or_run")
        return "failed"

    # Устаревшая ревизия/run не перезаписывает актуальную заявку
    if app.active_run_id != run.id:
        mark_job_done(session, job, lease_token=lease_token, state="obsolete", last_error="stale_run")
        return "obsolete"

    revision = session.scalar(
        select(ApplicationRevision).where(
            ApplicationRevision.application_id == app.id,
            ApplicationRevision.revision_no == run.revision_no,
        )
    )
    if revision is None:
        mark_job_done(session, job, lease_token=lease_token, state="failed", last_error="missing_revision")
        return "failed"

    # Уже есть результат по run — идемпотентное завершение
    existing_risk = session.scalar(
        select(RiskAssessment).where(RiskAssessment.run_id == run.id)
    )
    if existing_risk is not None:
        mark_job_done(session, job, lease_token=lease_token, state="completed")
        return "completed"

    # SUBMITTED → CHECKING
    if app.status == ApplicationStatus.SUBMITTED.value:
        new_status = next_status(
            ApplicationStatus.SUBMITTED, WorkflowCommand.START, actor="WORKER"
        )
        _append_audit(
            session,
            application_id=app.id,
            action="START_CHECKS",
            from_status=app.status,
            to_status=new_status.value,
            revision_no=run.revision_no,
            metadata={"run_id": str(run.id)},
        )
        app.status = new_status.value
        app.version += 1
        app.updated_at = datetime.now(UTC)
        run.status = "RUNNING"
        run.started_at = datetime.now(UTC)

    company = session.get(Company, app.company_id)
    draft = dict((revision.snapshot_json or {}).get("draft") or app.draft_json or {})
    scenario = resolve_scenario(
        demo_registration_id=company.demo_registration_id if company else None,
        draft=draft,
    )

    registry = fetch_registry(scenario)
    bureau = fetch_bureau(scenario)

    session.add(
        IntegrationCheck(
            run_id=run.id,
            source=registry.source,
            outcome=registry.outcome,
            payload_json=registry.payload,
            observed_at=registry.observed_at,
            attempt_count=job.attempts,
        )
    )
    session.add(
        IntegrationCheck(
            run_id=run.id,
            source=bureau.source,
            outcome=bureau.outcome,
            payload_json=bureau.payload,
            observed_at=bureau.observed_at,
            attempt_count=job.attempts,
        )
    )

    technical = bureau.outcome in {"timeout", "unavailable", "schema_error", "incomplete"}
    if technical:
        code = {
            "timeout": "SOURCE_TIMEOUT",
            "unavailable": "SOURCE_UNAVAILABLE",
            "schema_error": "SOURCE_SCHEMA_ERROR",
            "incomplete": "SOURCE_INCOMPLETE",
        }[bureau.outcome]
        if job.attempts < settings.job_max_attempts:
            delay = _retry_delay(job.attempts)
            requeue_job(
                session,
                job,
                lease_token=lease_token,
                delay_seconds=delay,
                last_error=code,
            )
            return "requeued"

        # Исчерпаны попытки
        from_status = app.status
        new_status = next_status(
            ApplicationStatus.CHECKING,
            WorkflowCommand.PROCESSING_FAILED,
            actor="WORKER",
        )
        app.status = new_status.value
        app.version += 1
        app.updated_at = datetime.now(UTC)
        run.status = "FAILED"
        run.completed_at = datetime.now(UTC)
        _append_audit(
            session,
            application_id=app.id,
            action="PROCESSING_FAILED",
            from_status=from_status,
            to_status=new_status.value,
            revision_no=run.revision_no,
            metadata={"reason": code, "attempts": job.attempts},
        )
        mark_job_done(session, job, lease_token=lease_token, state="failed", last_error=code)
        return "failed"

    document_kinds = set((revision.snapshot_json or {}).get("document_kinds") or [])
    product_code = str((revision.snapshot_json or {}).get("product_code") or "")

    try:
        risk_input = build_risk_input(
            application_id=app.id,
            revision=run.revision_no,
            product_code=product_code,
            draft=draft,
            registry=registry.payload,
            bureau=bureau.payload,
            required_documents_present=bool(document_kinds),
            sources_complete=True,
            data_conflicts=[],
        )
        result = evaluate(risk_input)
    except (FeatureBuildError, RiskContractError) as exc:
        log.exception("risk contract error")
        if job.attempts < settings.job_max_attempts:
            requeue_job(
                session,
                job,
                lease_token=lease_token,
                delay_seconds=_retry_delay(job.attempts),
                last_error="RISK_CONTRACT_ERROR",
            )
            return "requeued"
        from_status = app.status
        new_status = next_status(
            ApplicationStatus.CHECKING,
            WorkflowCommand.PROCESSING_FAILED,
            actor="WORKER",
        )
        app.status = new_status.value
        app.version += 1
        run.status = "FAILED"
        run.completed_at = datetime.now(UTC)
        _append_audit(
            session,
            application_id=app.id,
            action="PROCESSING_FAILED",
            from_status=from_status,
            to_status=new_status.value,
            revision_no=run.revision_no,
            metadata={"reason": "RISK_CONTRACT_ERROR", "detail": str(exc)},
        )
        mark_job_done(
            session, job, lease_token=lease_token, state="failed", last_error="RISK_CONTRACT_ERROR"
        )
        return "failed"

    dumped = _serialize_result(result)
    session.add(
        RiskAssessment(
            run_id=run.id,
            score=result.risk_score,
            band=result.risk_band,
            factors_json=dumped.get("factors"),
            affordability_json=dumped.get("affordability"),
            recommendation=result.recommendation.value,
            reasons_json=list(result.reason_codes),
            candidate_json=dumped.get("candidate"),
        )
    )
    run.policy_version = result.policy_version
    run.model_version = result.model_version
    run.completed_at = datetime.now(UTC)
    run.status = "COMPLETED"

    from_status = app.status
    if result.recommendation == RiskRecommendation.NEEDS_INFO:
        new_status = next_status(
            ApplicationStatus.CHECKING, WorkflowCommand.REQUIRE_INFO, actor="WORKER"
        )
        session.add(
            InfoRequest(
                application_id=app.id,
                based_on_run_id=run.id,
                fields_json=list(result.requested_fields),
                document_kinds_json=[],
                message="; ".join(result.client_explanations) or "Нужны дополнительные сведения",
                status="OPEN",
                actor_id=app.creator_id,
            )
        )
        action = "REQUIRE_INFO"
    else:
        # OFFER и REJECT идут сотруднику
        new_status = next_status(
            ApplicationStatus.CHECKING, WorkflowCommand.FINISH, actor="WORKER"
        )
        action = "FINISH_CHECKS"

    app.status = new_status.value
    app.version += 1
    app.updated_at = datetime.now(UTC)
    _append_audit(
        session,
        application_id=app.id,
        action=action,
        from_status=from_status,
        to_status=new_status.value,
        revision_no=run.revision_no,
        metadata={
            "recommendation": result.recommendation.value,
            "reason_codes": list(result.reason_codes),
            "run_id": str(run.id),
        },
    )
    mark_job_done(session, job, lease_token=lease_token, state="completed")
    return "completed"
