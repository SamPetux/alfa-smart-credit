"""Worker: claim → evaluate / disbursement. Тот же образ, что API."""

from __future__ import annotations

import logging
import time

from backend.app.core.config import get_settings
from backend.app.core.logging_utils import log_event
from backend.app.core.request_context import clear_request_context, set_application_id, set_request_id
from backend.app.db.session import get_session_factory
from backend.app.jobs.claim import claim_next_job, mark_job_done
from backend.app.jobs.disbursement import process_disbursement_job
from backend.app.jobs.evaluate_pipeline import process_evaluate_job

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("worker")


def process_once() -> str | None:
    """Один цикл: claim + process. Для тестов и ручного прогона. None если очередь пуста."""
    settings = get_settings()
    session = get_session_factory()()
    try:
        job = claim_next_job(session, settings=settings)
        if job is None:
            session.commit()
            return None
        job_id = job.id
        set_request_id(f"job-{job_id.hex[:12]}")
        set_application_id(str(job.application_id))
        started = time.perf_counter()
        if job.kind == "evaluate_application":
            result = process_evaluate_job(session, job, settings=settings)
        elif job.kind == "simulate_disbursement":
            result = process_disbursement_job(session, job, settings=settings)
        else:
            token = job.lease_token
            if token is not None:
                mark_job_done(
                    session,
                    job,
                    lease_token=token,
                    state="failed",
                    last_error=f"unknown_kind:{job.kind}",
                )
            result = "failed"
        session.commit()
        log_event(
            "JOB_FINISHED",
            job_id=str(job_id),
            job_kind=job.kind,
            result=result,
            duration_ms=int((time.perf_counter() - started) * 1000),
            attempt=job.attempts,
        )
        return result
    except Exception:
        session.rollback()
        log.exception("worker process_once failed")
        log_event("JOB_WORKER_ERROR", level=logging.ERROR)
        raise
    finally:
        clear_request_context()
        session.close()


def drain(*, max_jobs: int = 50) -> list[str]:
    """Обработать до max_jobs доступных задач (тесты)."""
    outcomes: list[str] = []
    for _ in range(max_jobs):
        outcome = process_once()
        if outcome is None:
            break
        outcomes.append(outcome)
        if outcome == "requeued":
            continue
    return outcomes


def main() -> None:
    settings = get_settings()
    log_event(
        "WORKER_STARTED",
        lease_seconds=settings.job_lease_seconds,
        max_attempts=settings.job_max_attempts,
        poll_seconds=settings.worker_poll_seconds,
        demo_mode=settings.demo_mode,
        app_env=settings.app_env,
    )
    while True:
        try:
            outcome = process_once()
            if outcome is None:
                time.sleep(settings.worker_poll_seconds)
        except Exception:
            log.exception("worker loop error; sleep and continue")
            time.sleep(settings.worker_poll_seconds)


if __name__ == "__main__":
    main()
