"""CLI / library entry: prepare job dir and dry-run or (later) invoke container solvers."""
from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path
from typing import Any
from uuid import uuid4

from thinning import write_dry_run_artifacts

PKG = Path(__file__).resolve().parent
TEMPLATES = {
    ("RF", "PMSM", "2d"): "rf_pmsm_2d",
    ("AF", "PMSM", "3d"): "af_pmsm_3d",
}


def resolve_template(payload: dict[str, Any]) -> str:
    if payload.get("templateId"):
        return str(payload["templateId"])
    key = (
        str(payload.get("topology", "RF")),
        str(payload.get("machineType", "PMSM")),
        str(payload.get("dim", "2d")),
    )
    return TEMPLATES.get(key, "rf_pmsm_2d")


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


def run_job(job_id: str, payload: dict[str, Any] | None, work_root: Path, dry_run: bool = True) -> dict[str, Any]:
    payload = payload or {}
    job_dir = prepare_job_dir(work_root / "jobs" / job_id, payload)
    topology = str(payload.get("topology", "RF"))
    machine_type = str(payload.get("machineType", "PMSM"))
    dim = str(payload.get("dim", "2d"))
    kernel = str(payload.get("solverKernel", "elmer"))

    # Real Elmer/GetDP only inside container when dry_run is False and binaries exist.
    if not dry_run:
        import shutil as sh
        if sh.which("ElmerSolver") is None and sh.which("getdp") is None:
            dry_run = True

    out = write_dry_run_artifacts(
        job_id=job_id,
        out_root=job_dir / "out",
        topology=topology,
        machine_type=machine_type,
        dim=dim,
        solver_kernel=kernel,
        payload=payload,
    )
    # Also mirror under work_root/mems_shadow for workers that sync into .mems
    shadow = write_dry_run_artifacts(
        job_id=job_id,
        out_root=work_root / "mems_shadow",
        topology=topology,
        machine_type=machine_type,
        dim=dim,
        solver_kernel=kernel,
        payload=payload,
    )
    return {
        "jobId": job_id,
        "jobDir": str(job_dir),
        "dryRun": dry_run,
        "resultRef": shadow["resultRef"],
        "manifestPath": shadow["manifestPath"],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Mo FEM job runner (dry-run default)")
    ap.add_argument("--job-id", default=str(uuid4()))
    ap.add_argument("--payload", type=Path, help="JSON payload file")
    ap.add_argument("--work-root", type=Path, default=Path(os.environ.get("MO_FEM_WORKDIR", "/tmp/mo-fem")))
    ap.add_argument("--dry-run", action="store_true", default=os.environ.get("MO_FEM_DRY_RUN", "1") != "0")
    ap.add_argument("--no-dry-run", action="store_true")
    args = ap.parse_args()
    payload = {}
    if args.payload and args.payload.is_file():
        payload = json.loads(args.payload.read_text(encoding="utf-8"))
    dry = False if args.no_dry_run else True
    result = run_job(args.job_id, payload, args.work_root, dry_run=dry)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
