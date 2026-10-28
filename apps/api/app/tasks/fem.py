"""FEM job Celery task (stub manifest; Q3). Never runs Elmer/GetDP in-process."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.celery_app import celery_app
from app.jobs_store import job_update


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_stub_manifest(job_id: str, payload: dict[str, Any] | None) -> dict[str, Any]:
    """Minimal shape matching packages/solver-fem/api/fem-manifest.schema.json."""
    p = payload or {}
    ts = _now_iso()
    return {
        "jobId": job_id,
        "status": "succeeded",
        "solverKernel": p.get("solverKernel", "elmer"),
        "topology": p.get("topology", "RF"),
        "machineType": p.get("machineType", "PMSM"),
        "dim": p.get("dim", "2d"),
        "scalars": {
            "torqueNm": 0.0,
            "dryRun": True,
            "pending_calibration": True,
            "notes": "API stub; Elmer/GetDP run only in FEM worker/container",
        },
        "artifacts": [],
        "createdAt": ts,
        "updatedAt": ts,
    }


def result_ref_for(job_id: str) -> str:
    """Contract path inside .mems (F1 mems-zip + thinned artifacts; tip 27a8de2)."""
    return f"solver/fem/jobs/{job_id}/manifest.json"


def maybe_write_local_manifest(job_id: str, manifest: dict[str, Any]) -> None:
    """Best-effort local write under MO_FEM_WORKDIR (shared volume); ignore if unset."""
    root = os.environ.get("MO_FEM_WORKDIR")
    if not root:
        return
    dest = Path(root) / "solver" / "fem" / "jobs" / job_id / "manifest.json"
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except OSError:
        pass


def _complete_fem_job(job_id: str, payload: dict[str, Any] | None) -> dict[str, Any]:
    job_update(job_id, status="running")
    time.sleep(0.05)
    manifest = build_stub_manifest(job_id, payload)
    maybe_write_local_manifest(job_id, manifest)
    ref = result_ref_for(job_id)
    if payload:
        job_update(job_id, payload={"input": payload, "manifest": manifest})
    job_update(job_id, status="succeeded", resultRef=ref, error=None)
    return {"jobId": job_id, "status": "succeeded", "resultRef": ref, "manifest": manifest}


@celery_app.task(name="app.tasks.fem.run_fem_job", bind=True, queue="fem")
def run_fem_job(self, job_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """queued → running → succeeded. Stub only — no Elmer in API/worker Python path."""
    return _complete_fem_job(job_id, payload)
