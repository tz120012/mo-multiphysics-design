"""Enqueue analytic/FEM jobs via Celery when Redis is up; else in-process degrade (Q2-6 / Q3)."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any
from uuid import UUID

from app.jobs_store import job_update, redis_available

logger = logging.getLogger("mo-api.jobs")


def _in_process_analytic(job_id: UUID, payload: dict[str, Any] | None) -> None:
    """Fake async: queued → running → succeeded in a daemon thread."""

    def _run() -> None:
        try:
            time.sleep(0.02)
            job_update(job_id, status="running")
            time.sleep(0.05)
            result_ref = f"analytic://placeholder/{job_id}"
            if payload:
                job_update(job_id, payload={"input": payload, "echo": True})
            job_update(job_id, status="succeeded", resultRef=result_ref, error=None)
        except Exception as exc:  # noqa: BLE001
            logger.exception("in-process analytic failed: %s", exc)
            job_update(
                job_id,
                status="failed",
                error={"code": "analytic_failed", "message": str(exc)},
            )

    threading.Thread(target=_run, name=f"analytic-{job_id}", daemon=True).start()


def _in_process_fem(job_id: UUID, payload: dict[str, Any] | None) -> None:
    """Fake async FEM: same status transitions via _complete_fem_job (MO_FEM_DRY_RUN gate)."""

    def _run() -> None:
        try:
            from app.tasks.fem import _complete_fem_job

            time.sleep(0.02)
            _complete_fem_job(str(job_id), payload)
        except Exception as exc:  # noqa: BLE001
            logger.exception("in-process fem failed: %s", exc)
            job_update(
                job_id,
                status="failed",
                error={"code": "fem_failed", "message": str(exc)},
            )

    threading.Thread(target=_run, name=f"fem-{job_id}", daemon=True).start()


def try_enqueue_analytic(job_id: UUID, payload: dict[str, Any] | None) -> str:
    """
    Attempt Celery enqueue. Returns mode: "celery" | "in_process".

    Requires CELERY_ENABLED=1 and reachable Redis; otherwise in-process fake async
    (API shape unchanged). Redis down or enqueue error also degrades.
    """
    from app.config import get_settings

    settings = get_settings()
    if settings.celery_enabled and redis_available():
        try:
            from app.tasks.analytic import run_analytic_job

            run_analytic_job.delay(str(job_id), payload)
            return "celery"
        except Exception as exc:  # noqa: BLE001
            logger.warning("Celery analytic enqueue failed, degrading to in-process: %s", exc)

    _in_process_analytic(job_id, payload)
    return "in_process"


def try_enqueue_fem(job_id: UUID, payload: dict[str, Any] | None) -> str:
    """
    Enqueue FEM on Celery queue `fem` (ops worker-fem). Returns "celery" | "in_process".

    Same CELERY_ENABLED + Redis gate as analytic; degrade to daemon thread
    (_complete_fem_job: stub unless MO_FEM_DRY_RUN=0 → solver-fem.run_job).
    resultRef contract: solver/fem/jobs/{jobId}/manifest.json
    """
    from app.config import get_settings

    settings = get_settings()
    if settings.celery_enabled and redis_available():
        try:
            from app.tasks.fem import run_fem_job

            run_fem_job.delay(str(job_id), payload)
            return "celery"
        except Exception as exc:  # noqa: BLE001
            logger.warning("Celery fem enqueue failed, degrading to in-process: %s", exc)

    _in_process_fem(job_id, payload)
    return "in_process"
