"""Analytic job Celery task (placeholder result; Q2-6)."""

from __future__ import annotations

import time
from typing import Any

from app.celery_app import celery_app
from app.jobs_store import job_update


@celery_app.task(name="app.tasks.analytic.run_analytic_job", bind=True)
def run_analytic_job(self, job_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """queued → running → succeeded. Payload echoed in resultRef placeholder."""
    job_update(job_id, status="running")
    # Placeholder compute; real MEC/Wasm hooks land with Q2-2+.
    time.sleep(0.05)
    result_ref = f"analytic://placeholder/{job_id}"
    if payload:
        # Keep resultRef as a short pointer; full echo lives in payload update.
        job_update(job_id, payload={"input": payload, "echo": True})
    job_update(job_id, status="succeeded", resultRef=result_ref, error=None)
    return {"jobId": job_id, "status": "succeeded", "resultRef": result_ref}
