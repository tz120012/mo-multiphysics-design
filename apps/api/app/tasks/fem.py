"""FEM job Celery task. Gates on MO_FEM_DRY_RUN; never runs Elmer/GetDP in-process.

Q5-2: stub/success scalars echo equationMode (heat_proxy | magnetostatic);
pending_calibration always true until calibrated; magnetostaticPathReady false
and force scalars null on magnetostatic stub — never invent axialForceN from
heat-proxy. Real Elmer magnetostatic path owned by packages/solver-fem.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from app.celery_app import celery_app
from app.jobs_store import job_update

# Align with packages/solver-fem/run_job.MAGNETOSTATIC_TEMPLATE_IDS
_MAGNETOSTATIC_TEMPLATE_IDS = frozenset({"af_pmsm_3d_ms"})


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def resolve_equation_mode(payload: dict[str, Any] | None, *, dry_run: bool) -> str:
    """Return heat_proxy | magnetostatic (API stub + validation-side helper).

    Missing equationMode + dryRun=false → heat_proxy (Q3 E2E compat).
    templateId af_pmsm_3d_ms implies magnetostatic when equationMode omitted.
    """
    p = payload or {}
    raw = p.get("equationMode")
    if raw is not None:
        mode = str(raw).strip().lower().replace("-", "_")
        if mode in {"heat_proxy", "heatproxy"}:
            return "heat_proxy"
        if mode in {"magnetostatic", "magneto_static", "ms"}:
            return "magnetostatic"
        # Invalid values should be rejected at FemJobPayload validation; fail-safe:
        return "heat_proxy"
    tid = str(p.get("templateId") or "")
    if tid in _MAGNETOSTATIC_TEMPLATE_IDS:
        return "magnetostatic"
    if dry_run:
        return "heat_proxy"
    return "heat_proxy"


def build_stub_manifest(job_id: str, payload: dict[str, Any] | None) -> dict[str, Any]:
    """Minimal shape matching packages/solver-fem/api/fem-manifest.schema.json.

    Q5-2 honesty: echo equationMode; pending_calibration; magnetostatic stub
    sets magnetostaticPathReady=false and null force scalars (no heat-proxy fake).
    """
    p = payload or {}
    ts = _now_iso()
    equation_mode = resolve_equation_mode(p, dry_run=True)
    scalars: dict[str, Any] = {
        "dryRun": True,
        "pending_calibration": True,
        "equationMode": equation_mode,
        "notes": (
            "API stub; Elmer/GetDP run only in FEM worker/container; "
            "heat-proxy ≠ magnetostatic; pending_calibration — do NOT claim FEM ≤3%"
        ),
    }
    if equation_mode == "magnetostatic":
        scalars["magnetostaticPathReady"] = False
        # Force-related: never invent from heat-proxy
        scalars["axialForceN"] = None
        scalars["torqueNm"] = None
    else:
        # heat_proxy stub compat (Q3): placeholder torque; still pending_calibration
        scalars["torqueNm"] = 0.0
        scalars["axialForceN"] = None
    return {
        "jobId": job_id,
        "status": "succeeded",
        "solverKernel": p.get("solverKernel", "elmer"),
        "topology": p.get("topology", "RF"),
        "machineType": p.get("machineType", "PMSM"),
        "dim": p.get("dim", "2d"),
        "scalars": scalars,
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


def _fem_dry_run_enabled() -> bool:
    """True unless MO_FEM_DRY_RUN is literally '0' (aligned with solver-fem CLI)."""
    return os.environ.get("MO_FEM_DRY_RUN", "1") != "0"


def _work_root() -> Path:
    """Prefer MO_FEM_WORKDIR; else /tmp/mo-fem (same default as solver-fem CLI)."""
    root = os.environ.get("MO_FEM_WORKDIR")
    if root:
        return Path(root)
    return Path("/tmp/mo-fem")


def _import_run_job() -> Callable[..., dict[str, Any]]:
    """Import packages/solver-fem.run_job via SOLVER_FEM_PATH or repo-relative path."""
    solver_path = os.environ.get("SOLVER_FEM_PATH")
    if not solver_path:
        # apps/api/app/tasks/fem.py → repo root = parents[4]
        repo_root = Path(__file__).resolve().parents[4]
        solver_path = str(repo_root / "packages" / "solver-fem")
    sp = Path(solver_path).resolve()
    if not (sp / "run_job.py").is_file():
        raise FileNotFoundError(f"solver-fem run_job.py not found under {sp}")
    sp_s = str(sp)
    if sp_s not in sys.path:
        sys.path.insert(0, sp_s)
    from run_job import run_job  # type: ignore[import-not-found]

    return run_job


def _fail_fem_job(job_id: str, code: str, message: str) -> dict[str, Any]:
    err = {"code": code, "message": message}
    job_update(job_id, status="failed", error=err)
    return {"jobId": job_id, "status": "failed", "error": err}


def _complete_fem_stub(job_id: str, payload: dict[str, Any] | None) -> dict[str, Any]:
    """MO_FEM_DRY_RUN!=0: existing stub/succeeded path (default, matches Dockerfile/compose)."""
    manifest = build_stub_manifest(job_id, payload)
    maybe_write_local_manifest(job_id, manifest)
    ref = result_ref_for(job_id)
    if payload:
        job_update(job_id, payload={"input": payload, "manifest": manifest})
    job_update(job_id, status="succeeded", resultRef=ref, error=None)
    return {"jobId": job_id, "status": "succeeded", "resultRef": ref, "manifest": manifest}


def _complete_fem_via_run_job(job_id: str, payload: dict[str, Any] | None) -> dict[str, Any]:
    """MO_FEM_DRY_RUN=0: call solver-fem.run_job; fail the job on errors (no silent stub).

    equationMode is passed through payload; magnetostatic real path not ready
    raises FemSolveError → job failed (never falls back to heat stub that lies).
    """
    try:
        run_job = _import_run_job()
        result = run_job(job_id, payload, _work_root(), dry_run=False)
    except Exception as exc:  # noqa: BLE001 — surface to job.error
        return _fail_fem_job(job_id, "fem_run_job_failed", str(exc))

    ref = str(result.get("resultRef") or result_ref_for(job_id))
    manifest: dict[str, Any] | None = result.get("manifest")
    if not isinstance(manifest, dict):
        man_path = result.get("manifestPath")
        if not man_path:
            return _fail_fem_job(job_id, "fem_manifest_missing", "run_job returned no manifest")
        try:
            manifest = json.loads(Path(str(man_path)).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return _fail_fem_job(job_id, "fem_manifest_unreadable", str(exc))

    maybe_write_local_manifest(job_id, manifest)
    update_payload: dict[str, Any] = {
        "input": payload or {},
        "manifest": manifest,
        "run_job": {
            "jobDir": result.get("jobDir"),
            "dryRun": result.get("dryRun"),
            "equationMode": result.get("equationMode"),
            "resultRef": result.get("resultRef"),
            "manifestPath": result.get("manifestPath"),
            "elmerExit": result.get("elmerExit"),
        },
    }
    job_update(job_id, payload=update_payload)
    job_update(job_id, status="succeeded", resultRef=ref, error=None)
    return {
        "jobId": job_id,
        "status": "succeeded",
        "resultRef": ref,
        "manifest": manifest,
        "run_job": result,
    }


def _complete_fem_job(job_id: str, payload: dict[str, Any] | None) -> dict[str, Any]:
    """Shared by Celery fem queue and job_dispatch in-process degrade."""
    job_update(job_id, status="running")
    time.sleep(0.05)
    if _fem_dry_run_enabled():
        return _complete_fem_stub(job_id, payload)
    return _complete_fem_via_run_job(job_id, payload)


@celery_app.task(name="app.tasks.fem.run_fem_job", bind=True, queue="fem")
def run_fem_job(self, job_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """queued → running → succeeded|failed. dry=1 stub; dry=0 → solver-fem.run_job."""
    return _complete_fem_job(job_id, payload)
