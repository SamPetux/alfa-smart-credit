"""Claim jobs: FOR UPDATE SKIP LOCKED + lease reclaim с лимитом попыток."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.orm import Session

import logging

from backend.app.core.config import Settings, get_settings
from backend.app.core.logging_utils import log_event
from backend.app.db.models import Job


def reclaim_expired_leases(session: Session, *, settings: Settings | None = None) -> int:
    """Вернуть просроченные lease в очередь или failed при исчерпании attempts."""
    settings = settings or get_settings()
    now = datetime.now(UTC)
    max_attempts = settings.job_max_attempts

    failed = session.execute(
        update(Job)
        .where(
            Job.state == "running",
            Job.lease_until.is_not(None),
            Job.lease_until < now,
            Job.attempts >= max_attempts,
        )
        .values(
            state="failed",
            lease_until=None,
            lease_token=None,
            last_error="lease_expired_max_attempts",
            updated_at=now,
        )
    )
    failed_n = failed.rowcount or 0

    pending = session.execute(
        update(Job)
        .where(
            Job.state == "running",
            Job.lease_until.is_not(None),
            Job.lease_until < now,
            Job.attempts < max_attempts,
        )
        .values(
            state="pending",
            lease_until=None,
            lease_token=None,
            available_at=now,
            last_error="lease_expired",
            updated_at=now,
        )
    )
    pending_n = pending.rowcount or 0
    total = failed_n + pending_n
    if total:
        log_event(
            "LEASE_RECLAIMED",
            reclaimed_pending=pending_n,
            reclaimed_failed=failed_n,
        )
    return total


def claim_next_job(session: Session, *, settings: Settings | None = None) -> Job | None:
    settings = settings or get_settings()
    reclaim_expired_leases(session, settings=settings)
    now = datetime.now(UTC)

    job = session.scalar(
        select(Job)
        .where(
            Job.state == "pending",
            Job.available_at <= now,
            Job.kind.in_(("evaluate_application", "simulate_disbursement")),
        )
        .order_by(Job.available_at.asc())
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    if job is None:
        return None

    # Не claim-ить сверх лимита (защита от зацикливания после reclaim)
    if int(job.attempts or 0) >= settings.job_max_attempts:
        job.state = "failed"
        job.last_error = job.last_error or "max_attempts_exceeded"
        job.updated_at = now
        session.flush()
        log_event(
            "JOB_MAX_ATTEMPTS",
            job_id=str(job.id),
            application_id=str(job.application_id),
            attempt=job.attempts,
            level=logging.WARNING,
        )
        return None

    token = uuid4()
    job.state = "running"
    job.attempts = int(job.attempts or 0) + 1
    job.lease_token = token
    job.lease_until = now + timedelta(seconds=settings.job_lease_seconds)
    job.updated_at = now
    session.flush()
    log_event(
        "JOB_CLAIMED",
        job_id=str(job.id),
        application_id=str(job.application_id),
        job_kind=job.kind,
        attempt=job.attempts,
        run_id=str(job.run_id) if job.run_id else None,
    )
    return job


def mark_job_done(
    session: Session,
    job: Job,
    *,
    lease_token: UUID,
    state: str = "completed",
    last_error: str | None = None,
) -> bool:
    """Завершить job только если lease всё ещё наш. False = stale worker."""
    if job.lease_token != lease_token or job.state != "running":
        return False
    job.state = state
    job.lease_token = None
    job.lease_until = None
    job.last_error = last_error
    job.updated_at = datetime.now(UTC)
    return True


def requeue_job(
    session: Session,
    job: Job,
    *,
    lease_token: UUID,
    delay_seconds: int,
    last_error: str,
) -> bool:
    if job.lease_token != lease_token or job.state != "running":
        return False
    now = datetime.now(UTC)
    job.state = "pending"
    job.lease_token = None
    job.lease_until = None
    job.available_at = now + timedelta(seconds=delay_seconds)
    job.last_error = last_error
    job.updated_at = now
    return True
