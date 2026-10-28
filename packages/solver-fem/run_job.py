"""CLI / library entry: prepare job dir; dry-run artifacts or real ElmerSolver."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any
from uuid import uuid4

from postprocess_ms import postprocess_magnetostatic_job
from thinning import write_result_artifacts

PKG = Path(__file__).resolve().parent
TEMPLATES = {
    ("RF", "PMSM", "2d"): "rf_pmsm_2d",
    ("AF", "PMSM", "3d"): "af_pmsm_3d",
}

# Magnetostatic true-path template (≠ heat-proxy af_pmsm_3d)
MAGNETOSTATIC_TEMPLATE_IDS = frozenset({"af_pmsm_3d_ms"})


class FemSolveError(RuntimeError):
    """Raised when a required FEM binary is missing or a solver step fails."""


def resolve_template(payload: dict[str, Any]) -> str:
    if payload.get("templateId"):
        return str(payload["templateId"])
    key = (
        str(payload.get("topology", "RF")),
        str(payload.get("machineType", "PMSM")),
        str(payload.get("dim", "2d")),
    )
    return TEMPLATES.get(key, "rf_pmsm_2d")


def resolve_equation_mode(payload: dict[str, Any], *, dry_run: bool) -> str:
    """Return heat_proxy | magnetostatic.

    Missing equationMode + dryRun=false → heat_proxy (Q3 E2E compat).
    templateId af_pmsm_3d_ms implies magnetostatic when equationMode omitted.
    """
    raw = payload.get("equationMode")
    if raw is not None:
        mode = str(raw).strip().lower().replace("-", "_")
        if mode in {"heat_proxy", "heatproxy"}:
            return "heat_proxy"
        if mode in {"magnetostatic", "magneto_static", "ms"}:
            return "magnetostatic"
        raise FemSolveError(f"unknown equationMode: {raw!r}")
    tid = str(payload.get("templateId") or "")
    if tid in MAGNETOSTATIC_TEMPLATE_IDS:
        return "magnetostatic"
    if dry_run:
        return "heat_proxy"  # dry-run default; shell may override via payload
    return "heat_proxy"


def _template_path_ready(tid: str) -> bool:
    meta = PKG / "templates" / tid / "template.json"
    if not meta.is_file():
        return False
    try:
        data = json.loads(meta.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return bool(data.get("magnetostaticPathReady"))


def prepare_job_dir(job_dir: Path, payload: dict[str, Any]) -> Path:
    job_dir.mkdir(parents=True, exist_ok=True)
    for sub in ("input", "mesh", "solve", "out"):
        (job_dir / sub).mkdir(exist_ok=True)
    tid = resolve_template(payload)
    src = PKG / "templates" / tid
    if src.is_dir():
        for p in src.iterdir():
            if p.is_file():
                shutil.copy2(p, job_dir / "input" / p.name)
    (job_dir / "input" / "payload.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return job_dir


def _require_bin(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise FemSolveError(
            f"{name} not on PATH; rebuild worker-fem with Elmer toolchain "
            "or set MO_FEM_DRY_RUN=1"
        )
    return path


def _run(cmd: list[str], cwd: Path, log_path: Path, timeout: int) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("ab") as log:
        log.write(f"\n$ {' '.join(cmd)}\n".encode())
        log.flush()
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            stdout=log,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
        )
    if proc.returncode != 0:
        raise FemSolveError(
            f"command failed ({proc.returncode}): {' '.join(cmd)}; see {log_path}"
        )


def run_elmer_pipeline(job_dir: Path, dim: str) -> int:
    """gmsh → ElmerGrid → ElmerSolver in job_dir/solve. Returns ElmerSolver exit (0)."""
    _require_bin("gmsh")
    _require_bin("ElmerGrid")
    _require_bin("ElmerSolver")

    solve = job_dir / "solve"
    if solve.exists():
        shutil.rmtree(solve)
    solve.mkdir(parents=True)

    geo_src = job_dir / "input" / "mesh.geo"
    sif_src = job_dir / "input" / "case.sif"
    if not geo_src.is_file() or not sif_src.is_file():
        raise FemSolveError("template missing mesh.geo or case.sif under input/")

    shutil.copy2(geo_src, solve / "mesh.geo")
    shutil.copy2(sif_src, solve / "case.sif")

    log = job_dir / "out" / "elmer_pipeline.log"
    gmsh_dim = "2" if str(dim).lower() in {"2d", "2"} else "3"
    _run(
        ["gmsh", "mesh.geo", f"-{gmsh_dim}", "-o", "mesh.msh"],
        cwd=solve,
        log_path=log,
        timeout=180,
    )
    # ElmerGrid: input format 14 (Gmsh) → output format 2 (Elmer mesh)
    _run(["ElmerGrid", "14", "2", "mesh.msh"], cwd=solve, log_path=log, timeout=120)
    _run(["ElmerSolver", "case.sif"], cwd=solve, log_path=log, timeout=600)
    return 0


def run_job(
    job_id: str,
    payload: dict[str, Any] | None,
    work_root: Path,
    dry_run: bool = True,
) -> dict[str, Any]:
    payload = dict(payload or {})
    equation_mode = resolve_equation_mode(payload, dry_run=dry_run)
    payload.setdefault("equationMode", equation_mode)
    if equation_mode == "magnetostatic":
        payload.setdefault("templateId", "af_pmsm_3d_ms")
        tid = str(payload.get("templateId") or "af_pmsm_3d_ms")
        path_ready = _template_path_ready(tid)
        payload["magnetostaticPathReady"] = path_ready
        payload.setdefault("postprocess", "maxwell")

    job_dir = prepare_job_dir(work_root / "jobs" / job_id, payload)
    topology = str(payload.get("topology", "RF"))
    machine_type = str(payload.get("machineType", "PMSM"))
    dim = str(payload.get("dim", "2d"))
    kernel = str(payload.get("solverKernel", "elmer"))

    elmer_exit: int | None = None
    status = "succeeded"
    notes: str | None = None

    if not dry_run:
        if equation_mode == "magnetostatic":
            if not payload.get("magnetostaticPathReady"):
                raise FemSolveError(
                    "magnetostatic real Elmer path not ready "
                    "(magnetostaticPathReady=false); use dry-run / "
                    "smoke/run_magnetostatic_truepath.py --dry-run, or "
                    "equationMode=heat_proxy for Q3 E2E scheduling only — "
                    "do NOT claim FEM ≤3%"
                )
            if kernel == "getdp":
                raise FemSolveError(
                    "GetDP magnetostatic not wired; use elmer WhitneyAV path"
                )
            # AF MS template is 3d regardless of payload dim default
            if str(payload.get("templateId")) in MAGNETOSTATIC_TEMPLATE_IDS:
                dim = str(payload.get("dim") or "3d")
                topology = str(payload.get("topology") or "AF")
                machine_type = str(payload.get("machineType") or "PMSM")
            elmer_exit = run_elmer_pipeline(job_dir, dim)
            pp = postprocess_magnetostatic_job(job_dir / "solve")
            payload["axialForceN"] = pp.get("axialForceN")
            payload["bearingLoadN"] = pp.get("axialForceN")
            payload["postprocess"] = pp.get("postprocess") or "maxwell"
            if pp.get("magneticEnergyJ") is not None:
                payload["magneticEnergyJ"] = pp["magneticEnergyJ"]
            if pp.get("forceXN") is not None:
                payload["forceXN"] = pp["forceXN"]
            if pp.get("forceYN") is not None:
                payload["forceYN"] = pp["forceYN"]
            # Mirror SaveScalars into published results for artifacts consumers
            src_dat = job_dir / "solve" / "scalars.dat"
            if src_dat.is_file():
                pub = work_root / "results" / "fem" / job_id
                pub.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_dat, pub / "elmer_scalars.dat")
                names = Path(str(src_dat) + ".names")
                if names.is_file():
                    shutil.copy2(names, pub / "elmer_scalars.dat.names")
            notes = (
                "ElmerSolver OK (magnetostatic WhitneyAV + Maxwell/nodal force); "
                "equationMode=magnetostatic; magnetostaticPathReady=true; "
                "pending_calibration — do NOT claim FEM ≤3% "
                f"(postprocess={payload.get('postprocess')}; "
                f"axialForceN={payload.get('axialForceN')})"
            )
        elif kernel == "getdp":
            raise FemSolveError("GetDP real solve not wired yet (F2 stub); use elmer")
        else:
            elmer_exit = run_elmer_pipeline(job_dir, dim)
            notes = (
                "ElmerSolver OK (heat-proxy Q3 E2E); equationMode=heat_proxy; "
                "pending_calibration — do NOT claim FEM ≤3% "
                "(≠ magnetostatic motor solve)"
            )
    elif equation_mode == "magnetostatic":
        notes = (
            "dry-run magnetostatic; magnetostaticPathReady="
            f"{payload.get('magnetostaticPathReady')}; "
            "pending_calibration — do NOT claim FEM ≤3%"
        )

    published = write_result_artifacts(
        job_id=job_id,
        out_root=work_root,
        topology=topology,
        machine_type=machine_type,
        dim=dim,
        solver_kernel=kernel,
        payload=payload,
        dry_run=dry_run,
        status=status,
        elmer_exit=elmer_exit,
        notes=notes,
    )
    # Mirror under job_dir/out for local inspection
    write_result_artifacts(
        job_id=job_id,
        out_root=job_dir / "out",
        topology=topology,
        machine_type=machine_type,
        dim=dim,
        solver_kernel=kernel,
        payload=payload,
        dry_run=dry_run,
        status=status,
        elmer_exit=elmer_exit,
        notes=notes,
    )
    return {
        "jobId": job_id,
        "jobDir": str(job_dir),
        "dryRun": dry_run,
        "equationMode": equation_mode,
        "magnetostaticPathReady": payload.get("magnetostaticPathReady"),
        "postprocess": payload.get("postprocess"),
        "axialForceN": payload.get("axialForceN"),
        "resultRef": published["resultRef"],
        "manifestPath": published["manifestPath"],
        "manifest": published["manifest"],
        "elmerExit": elmer_exit,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Mo FEM job runner")
    ap.add_argument("--job-id", default=str(uuid4()))
    ap.add_argument("--payload", type=Path, help="JSON payload file")
    ap.add_argument(
        "--work-root",
        type=Path,
        default=Path(os.environ.get("MO_FEM_WORKDIR", "/tmp/mo-fem")),
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        default=None,
        help="Force dry-run (default from MO_FEM_DRY_RUN)",
    )
    ap.add_argument("--no-dry-run", action="store_true")
    args = ap.parse_args()
    payload: dict[str, Any] = {}
    if args.payload and args.payload.is_file():
        payload = json.loads(args.payload.read_text(encoding="utf-8"))
    if args.no_dry_run:
        dry = False
    elif args.dry_run:
        dry = True
    else:
        dry = os.environ.get("MO_FEM_DRY_RUN", "1") != "0"
    result = run_job(args.job_id, payload, args.work_root, dry_run=dry)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
