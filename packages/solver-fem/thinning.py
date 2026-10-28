"""Write thinned FEM artifacts per docs/drafts/Q3-轴向与FEM边界.md §5."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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
    """Create manifest + scalars JSON + stub glTF + preview PNG under out_root."""
    job_solver = out_root / "solver" / "fem" / "jobs" / job_id
    job_results = out_root / "results" / "fem" / job_id
    job_solver.mkdir(parents=True, exist_ok=True)
    job_results.mkdir(parents=True, exist_ok=True)

    scalars = {
        "schemaVersion": "fem-scalars-v0",
        "torqueNm": 0.0,
        "notes": "dry-run; FEM <=3% pending_calibration — do not claim accuracy",
        "dryRun": True,
        "inputEcho": {
            "topology": topology,
            "machineType": machine_type,
            "dim": dim,
            "solverKernel": solver_kernel,
            "meshProfile": (payload or {}).get("meshProfile"),
            "templateId": (payload or {}).get("templateId"),
        },
    }
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
        "status": "succeeded",
        "solverKernel": solver_kernel,
        "topology": topology,
        "machineType": machine_type,
        "dim": dim,
        "scalars": {"torqueNm": 0.0, "dryRun": True, "pending_calibration": True},
        "artifacts": artifacts,
        "createdAt": ts,
        "updatedAt": ts,
        "notes": "dry-run stub; no host Elmer/GetDP/Gmsh",
    }
    man_path = job_solver / "manifest.json"
    man_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        "manifestPath": str(man_path),
        "resultRef": f"solver/fem/jobs/{job_id}/manifest.json",
        "manifest": manifest,
    }
