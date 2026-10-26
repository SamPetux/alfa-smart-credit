"""Worker: имитация выдачи (simulate_disbursement). Один эффект на заявку."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import Settings, get_settings
from backend.app.db.models import (
    Agreement,
    Application,
    AuditEvent,
    DisbursementSimulation,
    Job,
    Offer,
)
from backend.app.jobs.claim import mark_job_done, requeue_job
from backend.app.schemas.enums import ApplicationStatus, WorkflowCommand
from backend.app.workflow.transitions import IllegalTransitionError, next_status

log = logging.getLogger("worker.disbursement")

_RETRY_DELAYS = (1, 3, 3)


def _retry_delay(attempts: int) -> int:
    idx = max(0, min(attempts - 1, len(_RETRY_DELAYS) - 1))
    return _RETRY_DELAYS[idx]


def process_disbursement_job(
    session: Session,
    job: Job,
    *,
    settings: Settings | None = None,
) -> str:
    settings = settings or get_settings()
    lease_token = job.lease_token
    if lease_token is None:
        return "stale"

    app = session.get(Application, job.application_id)
    if app is None:
        mark_job_done(
            session, job, lease_token=lease_token, state="failed", last_error="app_missing"
        )
        return "failed"

    existing = session.scalar(
        select(DisbursementSimulation).where(
            DisbursementSimulation.application_id == app.id
        )
    )
    if existing is not None:
        if app.status != ApplicationStatus.COMPLETED.value:
            # Идемпотентный догон статуса, если запись уже есть
            try:
                new_status = next_status(
                    ApplicationStatus(app.status),
                    WorkflowCommand.COMPLETE_SIMULATION,
                    actor="WORKER",
                )
                from_status = app.status
                app.status = new_status.value
                app.version += 1
                app.updated_at = datetime.now(UTC)
                session.add(
                    AuditEvent(
                        application_id=app.id,
                        actor_id=None,
                        action="COMPLETE_SIMULATION",
                        from_status=from_status,
                        to_status=new_status.value,
                        revision_no=app.current_revision,
                        metadata_json={
                            "disbursement_id": str(existing.id),
                            "idempotent": True,
                        },
                    )
                )
            except IllegalTransitionError:
                pass
        mark_job_done(session, job, lease_token=lease_token, state="completed")
        return "completed"

    if app.status != ApplicationStatus.SIGNED.value:
        mark_job_done(
            session,
            job,
            lease_token=lease_token,
            state="failed",
            last_error=f"unexpected_status:{app.status}",
        )
        return "failed"

    payload = job.payload_json or {}
    agreement_id_raw = payload.get("agreement_id")
    if not agreement_id_raw:
        mark_job_done(
            session,
            job,
            lease_token=lease_token,
            state="failed",
            last_error="missing_agreement_id",
        )
        return "failed"

    agreement_id = UUID(str(agreement_id_raw))
    agreement = session.get(Agreement, agreement_id)
    if agreement is None or agreement.signed_at is None:
        mark_job_done(
            session,
            job,
            lease_token=lease_token,
            state="failed",
            last_error="agreement_not_signed",
        )
        return "failed"

    offer = session.get(Offer, agreement.offer_id)
    if offer is None or offer.application_id != app.id:
        mark_job_done(
            session,
            job,
            lease_token=lease_token,
            state="failed",
            last_error="offer_mismatch",
        )
        return "failed"

    # Демо-хук для тестов retry: force_fail=true падает до max_attempts
    if payload.get("force_fail") and job.attempts < settings.job_max_attempts:
        delay = _retry_delay(job.attempts)
        requeue_job(
            session,
            job,
            lease_token=lease_token,
            delay_seconds=delay,
            last_error="forced_disbursement_failure",
        )
        return "requeued"

    if payload.get("force_fail") and job.attempts >= settings.job_max_attempts:
        mark_job_done(
            session,
            job,
            lease_token=lease_token,
            state="failed",
            last_error="forced_disbursement_failure",
        )
        return "failed"

    amount = Decimal(str(payload.get("amount") or (offer.terms_json or {}).get("amount")))
    now = datetime.now(UTC)
    try:
        new_status = next_status(
            ApplicationStatus.SIGNED,
            WorkflowCommand.COMPLETE_SIMULATION,
            actor="WORKER",
        )
    except IllegalTransitionError as exc:
        mark_job_done(
            session, job, lease_token=lease_token, state="failed", last_error=str(exc)
        )
        return "failed"

    simulation = DisbursementSimulation(
        application_id=app.id,
        agreement_id=agreement.id,
        amount=amount,
        completed_at=now,
    )
    session.add(simulation)

    from_status = app.status
    app.status = new_status.value
    app.version += 1
    app.updated_at = now
    session.add(
        AuditEvent(
            application_id=app.id,
            actor_id=None,
            action="COMPLETE_SIMULATION",
            from_status=from_status,
            to_status=new_status.value,
            revision_no=app.current_revision,
            metadata_json={
                "agreement_id": str(agreement.id),
                "amount": str(amount),
                "is_simulation": True,
            },
        )
    )
    mark_job_done(session, job, lease_token=lease_token, state="completed")
    session.flush()
    log.info("disbursement simulated for app %s amount=%s", app.id, amount)
    return "completed"
