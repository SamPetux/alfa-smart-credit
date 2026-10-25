"""Claim jobs: FOR UPDATE SKIP LOCKED + lease."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from backend.app.core.config import Settings, get_settings
from backend.app.db.models import Job


def reclaim_expired_leases(session: Session, *, settings: Settings | None = None) -> int:
    settings = settings or get_settings()
    now = datetime.now(UTC)
    result = session.execute(
        update(Job)
        .where(
            Job.state == "running",
            Job.lease_until.is_not(None),
            Job.lease_until < now,
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
    return result.rowcount or 0


def claim_next_job(session: Session, *, settings: Settings | None = None) -> Job | None:
    settings = settings or get_settings()
    reclaim_expired_leases(session, settings=settings)
    now = datetime.now(UTC)

    job = session.scalar(
        select(Job)
        .where(
            Job.state == "pending",
            Job.available_at <= now,
            Job.kind == "evaluate_application",
        )
        .order_by(Job.available_at.asc())
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    if job is None:
        return None

    token = uuid4()
    job.state = "running"
    job.attempts = int(job.attempts or 0) + 1
    job.lease_token = token
    job.lease_until = now + timedelta(seconds=settings.job_lease_seconds)
    job.updated_at = now
    session.flush()
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
