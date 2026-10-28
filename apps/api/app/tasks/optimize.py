"""Optimize job Celery task (Q4-9).

Runs packages/solver-opt NSGA stub on Celery queue `optimize` or in-process
daemon thread — never on the FastAPI request thread.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from app.celery_app import celery_app
from app.jobs_store import job_get, job_update

_DEFAULT_FIXTURE = "seed42_rf_pmsm_payload.json"


def result_ref_for(job_id: str) -> str:
    """Contract path inside .mems (Q4-9; aligns FEM L4 pattern)."""
    return f"solver/optimize/jobs/{job_id}/manifest.json"


def _work_root() -> Path:
    """Prefer MO_OPT_WORKDIR → MO_FEM_WORKDIR → /tmp/mo-opt."""
    for key in ("MO_OPT_WORKDIR", "MO_FEM_WORKDIR"):
        root = os.environ.get(key)
        if root:
            return Path(root)
    return Path("/tmp/mo-opt")


def _repo_root() -> Path:
    # apps/api/app/tasks/optimize.py → parents[4] = repo root
    return Path(__file__).resolve().parents[4]


def _solver_opt_root() -> Path:
    env = os.environ.get("SOLVER_OPT_PATH")
    if env:
        return Path(env).resolve()
    docker_default = Path("/opt/mo/packages/solver-opt")
    if docker_default.is_dir():
        return docker_default
    return (_repo_root() / "packages" / "solver-opt").resolve()


def _ensure_solver_opt_on_path() -> Path:
    """sys.path: solver-opt (+ solver-analytic if needed for adapters)."""
    opt = _solver_opt_root()
    if not opt.is_dir():
        raise FileNotFoundError(f"solver-opt not found under {opt}")
    opt_s = str(opt)
    if opt_s not in sys.path:
        sys.path.insert(0, opt_s)
    analytic = os.environ.get("SOLVER_ANALYTIC_PATH")
    if analytic:
        ap = Path(analytic).resolve()
    else:
        ap = (_repo_root() / "packages" / "solver-analytic").resolve()
        docker_a = Path("/opt/mo/packages/solver-analytic")
        if docker_a.is_dir() and not (ap / "solve.py").is_file():
            ap = docker_a
    if ap.is_dir() and str(ap) not in sys.path:
        sys.path.insert(0, str(ap))
    return opt


def _load_default_fixture_payload() -> dict[str, Any]:
    opt = _solver_opt_root()
    path = opt / "fixtures" / _DEFAULT_FIXTURE
    if not path.is_file():
        raise FileNotFoundError(f"default optimize fixture missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _is_cancelled(job_id: str) -> bool:
    cur = job_get(job_id)
    return bool(cur and cur.get("status") == "cancelled")


def _fail(job_id: str, code: str, message: str) -> dict[str, Any]:
    err = {"code": code, "message": message}
    job_update(job_id, status="failed", error=err)
    return {"jobId": job_id, "status": "failed", "error": err}


def _cancelled_result(job_id: str) -> dict[str, Any]:
    return {"jobId": job_id, "status": "cancelled"}


def write_optimize_artifacts(
    job_id: str,
    manifest: dict[str, Any],
    pareto: dict[str, Any],
) -> None:
    """Write under workdir mems_shadow/ (and mirror) so artifacts_resolve can read."""
    root = _work_root()
    man_rel = result_ref_for(job_id)
    pareto_rel = f"results/optimize/{job_id}/pareto.json"
    for base in (root / "mems_shadow", root):
        man_dest = base / man_rel
        pareto_dest = base / pareto_rel
        try:
            man_dest.parent.mkdir(parents=True, exist_ok=True)
            pareto_dest.parent.mkdir(parents=True, exist_ok=True)
            man_dest.write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            pareto_dest.write_text(
                json.dumps(pareto, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        except OSError:
            pass


def _resolve_base_solve_request(payload: dict[str, Any]) -> tuple[dict[str, Any], str]:
    """Return (baseSolveRequest, source_note). Fixture default when omitted."""
    base = payload.get("baseSolveRequest")
    if isinstance(base, dict) and base:
        return base, "payload.baseSolveRequest"
    fixture = _load_default_fixture_payload()
    fb = fixture.get("baseSolveRequest")
    if not isinstance(fb, dict) or not fb:
        raise ValueError("fixture baseSolveRequest missing")
    return fb, f"fixture:{_DEFAULT_FIXTURE}"


def _run_solver_opt(job_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Call solver-opt analytic NSGA stub; return {pareto, manifest, result}."""
    _ensure_solver_opt_on_path()
    from adapters.analytic import AnalyticObjectives  # type: ignore[import-not-found]
    from nsga.core import run_nsga2_stub  # type: ignore[import-not-found]

    profile = payload.get("evaluatorProfile") or "analytic"
    if profile != "analytic":
        raise ValueError(
            f"MVP evaluatorProfile must be 'analytic' (got {profile!r}); "
            "analytic+drive / analytic+fem are stretch (F3)"
        )

    variables = payload.get("variables") or []
    objectives = payload.get("objectives") or []
    nsga = payload.get("nsga") or {}
    if not isinstance(variables, list) or not variables:
        raise ValueError("variables required")
    if not isinstance(objectives, list) or len(objectives) < 1:
        raise ValueError("objectives required")
    pop = int(nsga["popSize"])
    gens = int(nsga["generations"])
    seed = int(nsga["seed"])

    senses = [str(o.get("sense") or "minimize") for o in objectives]
    objective_ids = [str(o.get("metricId") or o.get("id") or f"f{i}") for i, o in enumerate(objectives)]
    variable_ids = [str(v.get("id") or v.get("name") or f"x{i}") for i, v in enumerate(variables)]

    base_req, base_src = _resolve_base_solve_request(payload)
    adapter = AnalyticObjectives(base_req, variables, solver="mec")

    def evaluate(x: list[float]) -> list[float]:
        return adapter.evaluate(x)[0]

    result = run_nsga2_stub(
        variables=variables,
        senses=senses,
        evaluate=evaluate,
        pop_size=pop,
        generations=gens,
        seed=seed,
    )

    pareto_rel = f"results/optimize/{job_id}/pareto.json"
    pareto = {
        "jobId": job_id,
        "seed": seed,
        "generations": gens,
        "objectiveIds": objective_ids,
        "variableIds": variable_ids,
        "fronts": result["fronts"],
        "individuals": result["individuals"],
        "digest": result["digest"],
        "notes": (
            "solver-opt nsga.core.run_nsga2_stub + adapters.analytic "
            f"(baseSolveRequest from {base_src}); analytic-only MVP"
        ),
    }
    manifest = {
        "jobId": job_id,
        "status": "succeeded",
        "evaluatorProfile": "analytic",
        "nsga": {"popSize": pop, "generations": gens, "seed": seed},
        "summary": {
            "generationsRun": gens,
            "paretoCount": result["digest"]["paretoCount"],
            "evaluations": result["evaluations"],
            "note": (
                "analytic-only MVP via packages/solver-opt; not accuracy-gated; "
                f"baseSolveRequest={base_src}"
            ),
        },
        # Keep scalars alias for older FEM-style list consumers
        "scalars": {
            "paretoCount": result["digest"]["paretoCount"],
            "evaluations": result["evaluations"],
            "generations": gens,
            "popSize": pop,
        },
        "artifacts": [
            {
                "path": pareto_rel,
                "kind": "pareto",
                # Also emit FemArtifact-compatible fields for list endpoint
                "role": "pareto",
                "format": "json",
            }
        ],
        "resultRef": result_ref_for(job_id),
    }
    return {"pareto": pareto, "manifest": manifest, "raw": result}


def _complete_optimize_job(job_id: str, payload: dict[str, Any] | None) -> dict[str, Any]:
    """Shared by Celery optimize queue and job_dispatch in-process degrade."""
    if _is_cancelled(job_id):
        return _cancelled_result(job_id)

    job_update(job_id, status="running")
    # Brief pause so cancel during running can win before heavy eval.
    time.sleep(0.08)
    if _is_cancelled(job_id):
        return _cancelled_result(job_id)

    p = payload or {}
    try:
        out = _run_solver_opt(job_id, p)
    except Exception as exc:  # noqa: BLE001
        return _fail(job_id, "optimize_failed", str(exc))

    if _is_cancelled(job_id):
        return _cancelled_result(job_id)

    manifest = out["manifest"]
    pareto = out["pareto"]
    write_optimize_artifacts(job_id, manifest, pareto)
    ref = result_ref_for(job_id)
    job_update(job_id, payload={"input": p, "manifest": manifest})
    job_update(job_id, status="succeeded", resultRef=ref, error=None)
    return {
        "jobId": job_id,
        "status": "succeeded",
        "resultRef": ref,
        "manifest": manifest,
    }


@celery_app.task(name="app.tasks.optimize.run_optimize_job", bind=True, queue="optimize")
def run_optimize_job(self, job_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """queued → running → succeeded|failed|cancelled. Worker-side solver-opt only."""
    return _complete_optimize_job(job_id, payload)
