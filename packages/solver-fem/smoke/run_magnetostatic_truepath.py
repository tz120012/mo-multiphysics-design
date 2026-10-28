#!/usr/bin/env python3
"""Q5-2 smoke: magnetostatic TRUE PATH (WhitneyAV + Maxwell postprocess).

Default: real gmsh→ElmerGrid→ElmerSolver when binaries exist (host PATH or
docker exec mo-fem / mo-worker-fem). Never silently falls back to heat-proxy.

--dry-run: structure / template checks only (no Elmer).

Stdout JSON includes equationMode, magnetostaticPathReady, pending_calibration,
elmerExit, axialForceN, postprocess.
Do NOT claim FEM ≤3%.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TEMPLATE_DIR = ROOT / "templates" / "af_pmsm_3d_ms"
TEMPLATE_META = TEMPLATE_DIR / "template.json"
CASE_SIF = TEMPLATE_DIR / "case.sif"
MESH_GEO = TEMPLATE_DIR / "mesh.geo"
HEAT_SIF = ROOT / "templates" / "af_pmsm_3d" / "case.sif"
DOC = REPO / "docs" / "drafts" / "Q5-2-真磁静力学后处理.md"

DOCKER_CANDIDATES = ("mo-fem", "mo-worker-fem")


def _fail(msg: str, code: int = 1) -> int:
    print(f"FAIL: {msg}", file=sys.stderr)
    return code


def _structure_checks() -> dict[str, Any]:
    assert TEMPLATE_META.is_file(), f"missing {TEMPLATE_META}"
    assert CASE_SIF.is_file(), f"missing {CASE_SIF}"
    assert MESH_GEO.is_file(), f"missing {MESH_GEO}"
    meta = json.loads(TEMPLATE_META.read_text(encoding="utf-8"))
    assert meta.get("equationMode") == "magnetostatic"
    assert meta.get("pending_calibration") is True
    assert meta.get("magnetostaticPathReady") is True
    sif = CASE_SIF.read_text(encoding="utf-8")
    assert "HeatSolve" not in sif and "Procedure = \"HeatSolve\"" not in sif, (
        "af_pmsm_3d_ms must NOT use HeatSolve (heat-proxy)"
    )
    assert "Equation = Heat Equation" not in sif, (
        "af_pmsm_3d_ms must NOT use Heat Equation"
    )
    assert "WhitneyAVSolver" in sif or "MagnetoDynamics" in sif, (
        "case.sif must use MagnetoDynamics / WhitneyAV"
    )
    assert "Magnetic Force" in sif or "Calculate Nodal Forces" in sif or (
        "Calculate Maxwell Stress" in sif
    ), "case.sif must enable Maxwell/nodal force postprocess"
    assert HEAT_SIF.is_file(), "heat-proxy af_pmsm_3d case.sif missing"
    heat = HEAT_SIF.read_text(encoding="utf-8")
    assert "HeatEquation" in heat or "Heat Equation" in heat, (
        "af_pmsm_3d must remain heat-proxy"
    )
    return meta


def _host_bins() -> dict[str, str | None]:
    return {
        "gmsh": shutil.which("gmsh"),
        "ElmerGrid": shutil.which("ElmerGrid"),
        "ElmerSolver": shutil.which("ElmerSolver"),
    }


def _docker_bin() -> str | None:
    for c in ("docker",):
        p = shutil.which(c)
        if p:
            return p
    return None


def _docker_container_with_elmer() -> str | None:
    docker = _docker_bin()
    if not docker:
        return None
    for name in DOCKER_CANDIDATES:
        try:
            r = subprocess.run(
                ["sudo", docker, "exec", name, "bash", "-c",
                 "command -v ElmerSolver && command -v gmsh && command -v ElmerGrid"],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        if r.returncode == 0:
            return name
    return None


def _run_truepath_host(work: Path, job_id: str) -> dict[str, Any]:
    from run_job import run_job  # noqa: WPS433

    payload = {
        "templateId": "af_pmsm_3d_ms",
        "equationMode": "magnetostatic",
        "topology": "AF",
        "machineType": "PMSM",
        "dim": "3d",
        "solverKernel": "elmer",
        "meshProfile": "af_pmsm_3d_ms_min",
    }
    return run_job(job_id, payload, work, dry_run=False)


def _run_truepath_docker(container: str, work_host: Path, job_id: str) -> dict[str, Any]:
    """Copy template into shared volume via docker cp, run Elmer inside container,
    then postprocess on host with postprocess_ms + thinning.
    """
    from postprocess_ms import postprocess_magnetostatic_job  # noqa: WPS433
    from thinning import write_result_artifacts  # noqa: WPS433

    remote = f"/var/mo/fem/q5_truepath_{job_id[:8]}"
    docker = _docker_bin()
    assert docker

    def dexec(cmd: str, timeout: int = 300) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["sudo", docker, "exec", container, "bash", "-c", cmd],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

    r = dexec(f"rm -rf {remote} && mkdir -p {remote}")
    if r.returncode != 0:
        raise RuntimeError(f"docker mkdir failed: {r.stderr}")

    for name in ("mesh.geo", "case.sif"):
        src = TEMPLATE_DIR / name
        subprocess.run(
            ["sudo", docker, "cp", str(src), f"{container}:{remote}/{name}"],
            check=True,
            capture_output=True,
        )

    pipeline = (
        f"cd {remote} && "
        "gmsh mesh.geo -3 -o mesh.msh && "
        "ElmerGrid 14 2 mesh.msh && "
        "ElmerSolver case.sif"
    )
    r = dexec(pipeline, timeout=600)
    log_path = work_host / "docker_elmer.log"
    log_path.write_text(
        (r.stdout or "") + "\n---STDERR---\n" + (r.stderr or ""),
        encoding="utf-8",
    )
    if r.returncode != 0:
        raise RuntimeError(
            f"Elmer pipeline in {container} failed (exit {r.returncode}); "
            f"see {log_path}"
        )

    # Pull scalars.dat (+ names) back to host solve dir
    solve = work_host / "solve"
    solve.mkdir(parents=True, exist_ok=True)
    for fname in ("scalars.dat", "scalars.dat.names"):
        subprocess.run(
            ["sudo", docker, "cp", f"{container}:{remote}/{fname}", str(solve / fname)],
            check=False,
            capture_output=True,
        )
    if not (solve / "scalars.dat").is_file():
        raise RuntimeError(f"scalars.dat not produced in {container}:{remote}")

    pp = postprocess_magnetostatic_job(solve)
    payload = {
        "templateId": "af_pmsm_3d_ms",
        "equationMode": "magnetostatic",
        "topology": "AF",
        "machineType": "PMSM",
        "dim": "3d",
        "solverKernel": "elmer",
        "magnetostaticPathReady": True,
        "postprocess": pp.get("postprocess") or "maxwell",
        "axialForceN": pp.get("axialForceN"),
        "bearingLoadN": pp.get("axialForceN"),
        "magneticEnergyJ": pp.get("magneticEnergyJ"),
        "forceXN": pp.get("forceXN"),
        "forceYN": pp.get("forceYN"),
    }
    notes = (
        "ElmerSolver OK via docker "
        f"{container} (magnetostatic WhitneyAV + Maxwell); "
        "pending_calibration — do NOT claim FEM ≤3%"
    )
    published = write_result_artifacts(
        job_id=job_id,
        out_root=work_host,
        topology="AF",
        machine_type="PMSM",
        dim="3d",
        solver_kernel="elmer",
        payload=payload,
        dry_run=False,
        status="succeeded",
        elmer_exit=0,
        notes=notes,
    )
    # Copy elmer scalars into results for artifacts
    res = work_host / "results" / "fem" / job_id
    res.mkdir(parents=True, exist_ok=True)
    shutil.copy2(solve / "scalars.dat", res / "elmer_scalars.dat")
    names = solve / "scalars.dat.names"
    if names.is_file():
        shutil.copy2(names, res / "elmer_scalars.dat.names")

    return {
        "jobId": job_id,
        "jobDir": str(work_host),
        "dryRun": False,
        "equationMode": "magnetostatic",
        "magnetostaticPathReady": True,
        "postprocess": payload["postprocess"],
        "axialForceN": payload["axialForceN"],
        "magneticEnergyJ": payload.get("magneticEnergyJ"),
        "resultRef": published["resultRef"],
        "manifestPath": published["manifestPath"],
        "manifest": published["manifest"],
        "elmerExit": 0,
        "dockerContainer": container,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Q5-2 magnetostatic true-path smoke")
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Structure checks only; do not invoke Elmer",
    )
    ap.add_argument(
        "--job-id",
        default=None,
        help="Optional job id",
    )
    args = ap.parse_args()
    job_id = args.job_id or f"q5-2-ms-{uuid4().hex[:8]}"

    try:
        meta = _structure_checks()
    except AssertionError as exc:
        return _fail(str(exc))

    if args.dry_run:
        from thinning import write_result_artifacts  # noqa: WPS433

        with tempfile.TemporaryDirectory(prefix="mo-q52-dry-") as tmp:
            published = write_result_artifacts(
                job_id=job_id,
                out_root=Path(tmp),
                topology="AF",
                machine_type="PMSM",
                dim="3d",
                payload={
                    "templateId": "af_pmsm_3d_ms",
                    "equationMode": "magnetostatic",
                    "magnetostaticPathReady": True,
                    "postprocess": "maxwell",
                    "axialForceN": None,
                },
                dry_run=True,
                notes=(
                    "truepath --dry-run structure OK; Elmer not invoked; "
                    "pending_calibration — do NOT claim FEM ≤3%"
                ),
            )
            out = {
                "schemaVersion": "magnetostatic-truepath-v0",
                "equationMode": "magnetostatic",
                "magnetostaticPathReady": True,
                "pending_calibration": True,
                "elmerExit": None,
                "axialForceN": None,
                "postprocess": "maxwell",
                "dryRun": True,
                "resultRef": published.get("resultRef"),
                "templateId": "af_pmsm_3d_ms",
                "doc": str(DOC.relative_to(REPO)) if DOC.is_file() else str(DOC),
                "notes": (
                    "structure checks passed; heat-proxy unchanged; "
                    "use without --dry-run for real Elmer"
                ),
            }
            print(json.dumps(out, ensure_ascii=False, indent=2))
        print("Q5-2 magnetostatic truepath dry-run OK", file=sys.stderr)
        return 0

    bins = _host_bins()
    missing = [k for k, v in bins.items() if not v]
    result: dict[str, Any] | None = None
    mode = "host"

    with tempfile.TemporaryDirectory(prefix="mo-q52-ms-") as tmp:
        work = Path(tmp)
        if not missing:
            try:
                result = _run_truepath_host(work, job_id)
            except Exception as exc:  # noqa: BLE001
                return _fail(f"host Elmer truepath failed: {exc}")
        else:
            container = _docker_container_with_elmer()
            if not container:
                return _fail(
                    "Elmer toolchain missing on host PATH "
                    f"(need gmsh, ElmerGrid, ElmerSolver; missing={missing}) "
                    "and no running docker container with Elmer "
                    f"(tried {list(DOCKER_CANDIDATES)}). "
                    "Do NOT silently use heat-proxy. "
                    "Start: make up-fem / make up-fem-box, or install in worker image."
                )
            mode = f"docker:{container}"
            try:
                result = _run_truepath_docker(container, work, job_id)
            except Exception as exc:  # noqa: BLE001
                return _fail(f"docker Elmer truepath failed: {exc}")

        assert result is not None
        sc = (result.get("manifest") or {}).get("scalars") or {}
        axial = result.get("axialForceN")
        if axial is None:
            axial = sc.get("axialForceN")

        out = {
            "schemaVersion": "magnetostatic-truepath-v0",
            "equationMode": "magnetostatic",
            "magnetostaticPathReady": True,
            "pending_calibration": True,
            "elmerExit": result.get("elmerExit"),
            "axialForceN": axial,
            "magneticEnergyJ": result.get("magneticEnergyJ")
            or sc.get("magneticEnergyJ"),
            "postprocess": result.get("postprocess") or sc.get("postprocess") or "maxwell",
            "dryRun": False,
            "resultRef": result.get("resultRef"),
            "templateId": "af_pmsm_3d_ms",
            "runMode": mode,
            "doc": str(DOC.relative_to(REPO)) if DOC.is_file() else str(DOC),
            "notes": (
                "magnetostatic WhitneyAV true path + Maxwell/nodal force; "
                "≠ heat-proxy; pending_calibration — do NOT claim FEM ≤3%"
            ),
        }
        # Keep a copy of scalars under REPO-visible tmp is gone; print is enough.
        print(json.dumps(out, ensure_ascii=False, indent=2))

        if out["elmerExit"] != 0:
            return _fail(f"elmerExit={out['elmerExit']}")
        if out["equationMode"] != "magnetostatic":
            return _fail("equationMode not magnetostatic")
        if out["axialForceN"] is None:
            return _fail("axialForceN missing after Maxwell postprocess")
        if out["pending_calibration"] is not True:
            return _fail("pending_calibration must stay true")

    print(
        "Q5-2 magnetostatic truepath smoke OK "
        f"(runMode={mode}; axialForceN={out['axialForceN']}; pending_calibration)",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        raise SystemExit(_fail(str(exc)))
