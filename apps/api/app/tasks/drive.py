"""Drive job Celery task (Q4-1…4). Runs packages/solver-drive."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable

from app.celery_app import celery_app
from app.jobs_store import job_update


def result_ref_for(job_id: str) -> str:
    return f"drive://jobs/{job_id}"


def _work_root() -> Path | None:
    root = os.environ.get("MO_DRIVE_WORKDIR") or os.environ.get("MO_FEM_WORKDIR")
    return Path(root) if root else None


def maybe_write_local_result(job_id: str, result: dict[str, Any]) -> None:
    root = _work_root()
    if root is None:
        return
    dest = root / "solver" / "drive" / "jobs" / job_id / "result.json"
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(result, ensure_ascii=False) + "\n", encoding="utf-8")
    except OSError:
        pass


def _import_solve() -> tuple[Callable[..., dict[str, Any]], Callable[..., dict[str, Any]]]:
    solver_path = os.environ.get("SOLVER_DRIVE_PATH")
    if not solver_path:
        repo_root = Path(__file__).resolve().parents[4]
        solver_path = str(repo_root / "packages" / "solver-drive")
    sp = Path(solver_path).resolve()
    if not (sp / "solve.py").is_file():
        raise FileNotFoundError(f"solver-drive solve.py not found under {sp}")
    sp_s = str(sp)
    if sp_s not in sys.path:
        sys.path.insert(0, sp_s)
    from solve import run_drive_case, run_efficiency_map  # type: ignore[import-not-found]

    return run_drive_case, run_efficiency_map


def _slim_result(result: dict[str, Any]) -> dict[str, Any]:
    """Keep Job payload manageable: waveforms already downsampled; maps keep matrix+axes."""
    return result


def _fail(job_id: str, code: str, message: str) -> dict[str, Any]:
    err = {"code": code, "message": message}
    job_update(job_id, status="failed", error=err)
    return {"jobId": job_id, "status": "failed", "error": err}


def _complete_drive_job(job_id: str, payload: dict[str, Any] | None) -> dict[str, Any]:
    """Shared by Celery and in-process degrade."""
    job_update(job_id, status="running")
    time.sleep(0.02)
    p = payload or {}
    mode = str(p.get("mode") or "").strip().lower()
    try:
        run_case, run_map = _import_solve()
        if mode == "efficiency_map":
            result = run_map(p)
        else:
            result = run_case(p)
    except Exception as exc:  # noqa: BLE001
        return _fail(job_id, "drive_failed", str(exc))

    result = _slim_result(result)
    maybe_write_local_result(job_id, result)
    ref = result_ref_for(job_id)
    job_update(
        job_id,
        payload={
            "input": p,
            "result": result,
        },
    )
    job_update(job_id, status="succeeded", resultRef=ref, error=None)
    return {"jobId": job_id, "status": "succeeded", "resultRef": ref, "result": result}


@celery_app.task(name="app.tasks.drive.run_drive_job", bind=True)
def run_drive_job(self, job_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """queued → running → succeeded|failed."""
    return _complete_drive_job(job_id, payload)
