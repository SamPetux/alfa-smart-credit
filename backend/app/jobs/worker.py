"""Worker: claim → evaluate pipeline. Тот же образ, что API."""

from __future__ import annotations

import logging
import time

from backend.app.core.config import get_settings
from backend.app.db.session import get_session_factory
from backend.app.jobs.claim import claim_next_job
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
        result = process_evaluate_job(session, job, settings=settings)
        session.commit()
        log.info("job %s → %s", job_id, result)
        return result
    except Exception:
        session.rollback()
        log.exception("worker process_once failed")
        raise
    finally:
        session.close()


def drain(*, max_jobs: int = 50) -> list[str]:
    """Обработать до max_jobs доступных задач (тесты)."""
    outcomes: list[str] = []
    for _ in range(max_jobs):
        outcome = process_once()
        if outcome is None:
            break
        outcomes.append(outcome)
        # После requeue с delay может не быть сразу следующей
        if outcome == "requeued":
            continue
    return outcomes


def main() -> None:
    settings = get_settings()
    log.info(
        "worker started (lease=%ss max_attempts=%s poll=%ss)",
        settings.job_lease_seconds,
        settings.job_max_attempts,
        settings.worker_poll_seconds,
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
