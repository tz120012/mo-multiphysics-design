"""Write thinned FEM artifacts per docs/drafts/Q3-前端与FEM边界.md §5."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_result_artifacts(
    *,
    job_id: str,
    out_root: Path,
    topology: str,
    machine_type: str,
    dim: str,
    solver_kernel: str = "elmer",
    payload: dict[str, Any] | None = None,
    dry_run: bool = True,
    status: str = "succeeded",
    elmer_exit: int | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """Create manifest + scalars JSON + stub glTF + preview PNG under out_root."""
    job_solver = out_root / "solver" / "fem" / "jobs" / job_id
    job_results = out_root / "results" / "fem" / job_id
    job_solver.mkdir(parents=True, exist_ok=True)
    job_results.mkdir(parents=True, exist_ok=True)

    if notes is None:
        if dry_run:
            notes = "dry-run stub; no ElmerSolver invoked"
        else:
            notes = (
                "ElmerSolver invoked (heat-proxy Q3 E2E); "
                "pending_calibration — do NOT claim FEM ≤3%"
            )

    scalars: dict[str, Any] = {
        "schemaVersion": "fem-scalars-v0",
        "torqueNm": 0.0,
        "notes": notes,
        "dryRun": dry_run,
        "pending_calibration": True,
        "inputEcho": {
            "topology": topology,
            "machineType": machine_type,
            "dim": dim,
            "solverKernel": solver_kernel,
            "meshProfile": (payload or {}).get("meshProfile"),
            "templateId": (payload or {}).get("templateId"),
        },
    }
    if elmer_exit is not None:
        scalars["elmerExit"] = elmer_exit
    scalars_path = job_results / "scalars.json"
    scalars_path.write_text(json.dumps(scalars, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    fixture = Path(__file__).resolve().parent / "fixtures" / "rf_pmsm_2d_dryrun"
    gltf_dst = job_results / "slice.gltf"
    png_dst = job_results / "preview.png"
    gltf_src = fixture / "slice.gltf"
    png_src = fixture / "preview.png"
    if gltf_src.is_file():
        gltf_dst.write_bytes(gltf_src.read_bytes())
    else:
        gltf_dst.write_text('{"asset":{"version":"2.0"}}\n', encoding="utf-8")
    if png_src.is_file():
        png_dst.write_bytes(png_src.read_bytes())
    else:
        png_dst.write_bytes(b"")

    artifacts = [
        {
            "path": f"results/fem/{job_id}/scalars.json",
            "role": "scalars",
            "format": "json",
            "bytes": scalars_path.stat().st_size,
        },
        {
            "path": f"results/fem/{job_id}/slice.gltf",
            "role": "slice",
            "format": "gltf",
            "bytes": gltf_dst.stat().st_size,
        },
        {
            "path": f"results/fem/{job_id}/preview.png",
            "role": "preview",
            "format": "png",
            "bytes": png_dst.stat().st_size,
        },
    ]
    ts = _now()
    manifest = {
        "jobId": job_id,
        "status": status,
        "solverKernel": solver_kernel,
        "topology": topology,
        "machineType": machine_type,
        "dim": dim,
        "scalars": {
            "torqueNm": 0.0,
            "dryRun": dry_run,
            "pending_calibration": True,
        },
        "artifacts": artifacts,
        "createdAt": ts,
        "updatedAt": ts,
        "notes": notes,
    }
    if elmer_exit is not None:
        manifest["scalars"]["elmerExit"] = elmer_exit
    man_path = job_solver / "manifest.json"
    man_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        "manifestPath": str(man_path),
        "resultRef": f"solver/fem/jobs/{job_id}/manifest.json",
        "manifest": manifest,
    }


def write_dry_run_artifacts(
    *,
    job_id: str,
    out_root: Path,
    topology: str,
    machine_type: str,
    dim: str,
    solver_kernel: str = "elmer",
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Backward-compatible dry-run helper."""
    return write_result_artifacts(
        job_id=job_id,
        out_root=out_root,
        topology=topology,
        machine_type=machine_type,
        dim=dim,
        solver_kernel=solver_kernel,
        payload=payload,
        dry_run=True,
    )
