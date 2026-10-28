#!/usr/bin/env python3
"""Q5-4 FEM magnetostatic calibration compare (textbook air-gap pull).

Runs templates/ms_gap_force_3d (closed pot-core) via host Elmer or docker:mo-fem /
mo-worker-fem, parses Maxwell Fz, compares to F_ref = Bg²·A/(2·μ0) with
Bg = Br·hm/(hm+g·μr_pm) (1D) and/or FEM airgap body-rms Bz (single metric).

Does NOT use heat-proxy. Does NOT invent golden. Prints JSON + exit:
  0 = ran OK (whether or not ≤3% — see claimable in JSON)
  1 = pipeline / parse failure
"""
from __future__ import annotations

import argparse
import json
import math
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

TEMPLATE_DIR = ROOT / "templates" / "ms_gap_force_3d"
DOCKER_CANDIDATES = ("mo-fem", "mo-worker-fem")

# Geometry / material params (must match mesh.geo + case.sif)
# Closed pot-core: pole face L×W; side-yoke return (see mesh.geo)
L = 0.05  # m
W = 0.05
H_PM = 0.008
G = 0.001
BR = 1.0  # T
MU0 = 4.0 * math.pi * 1.0e-7
MU_R_PM = 1.05
TOL_REL = 0.03


def textbook_bg_and_force() -> dict[str, float]:
    """1D non-sat. circuit: reluctance of PM + gap; iron μ→∞; no fringing.

    Bg = Br / (1 + (g/hm)·μr_pm) = Br·hm / (hm + g·μr_pm)
    (with μr_pm≈1.05). Classic limit μr_pm=1 → Br·hm/(hm+g).
    Fz = Bg² · A / (2 · μ0)  (attractive magnitude).
    """
    a = L * W
    bg = BR * H_PM / (H_PM + G * MU_R_PM)
    fz = (bg * bg) * a / (2.0 * MU0)
    return {
        "Br_T": BR,
        "hm_m": H_PM,
        "g_m": G,
        "mu_r_pm": MU_R_PM,
        "A_m2": a,
        "Bg_T": bg,
        "Fz_ref_N": fz,
        "mu0": MU0,
    }


def _docker_bin() -> str | None:
    return shutil.which("docker")


def _docker_container() -> str | None:
    docker = _docker_bin()
    if not docker:
        return None
    for name in DOCKER_CANDIDATES:
        try:
            r = subprocess.run(
                [
                    "sudo",
                    docker,
                    "exec",
                    name,
                    "bash",
                    "-c",
                    "command -v ElmerSolver && command -v gmsh && command -v ElmerGrid",
                ],
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


def _host_bins() -> dict[str, str | None]:
    return {
        "gmsh": shutil.which("gmsh"),
        "ElmerGrid": shutil.which("ElmerGrid"),
        "ElmerSolver": shutil.which("ElmerSolver"),
    }


def _run_pipeline_docker(container: str, work: Path) -> dict[str, Any]:
    from postprocess_ms import postprocess_magnetostatic_job  # noqa: WPS433

    remote = f"/var/mo/fem/q54_calib_{uuid4().hex[:8]}"
    docker = _docker_bin()
    assert docker

    def dexec(cmd: str, timeout: int = 600) -> subprocess.CompletedProcess[str]:
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
    r = dexec(pipeline, timeout=900)
    log_path = work / "docker_elmer.log"
    log_path.write_text(
        (r.stdout or "") + "\n---STDERR---\n" + (r.stderr or ""),
        encoding="utf-8",
    )
    if r.returncode != 0:
        raise RuntimeError(
            f"Elmer pipeline in {container} failed (exit {r.returncode}); "
            f"see {log_path}"
        )

    solve = work / "solve"
    solve.mkdir(parents=True, exist_ok=True)
    for fname in ("scalars.dat", "scalars.dat.names"):
        subprocess.run(
            ["sudo", docker, "cp", f"{container}:{remote}/{fname}", str(solve / fname)],
            check=False,
            capture_output=True,
        )
    if not (solve / "scalars.dat").is_file():
        raise RuntimeError(f"scalars.dat missing from {container}:{remote}")

    pp = postprocess_magnetostatic_job(solve)
    # Optional: body-mean Bz from SaveScalars variable 1 (often col before forces)
    bg_stats = _try_parse_bg_stats(solve / "scalars.dat", solve / "scalars.dat.names")
    return {
        "elmerExit": 0,
        "runMode": f"docker:{container}",
        "axialForceN": pp.get("axialForceN"),
        "magneticEnergyJ": pp.get("magneticEnergyJ"),
        "forceXN": pp.get("forceXN"),
        "forceYN": pp.get("forceYN"),
        "Bg_fem_body_mean_T": bg_stats.get("mean"),
        "Bg_fem_body_rms_T": bg_stats.get("rms"),
        "postprocess": pp.get("postprocess") or "maxwell",
        "ppNotes": pp.get("notes"),
        "log": str(log_path),
    }


def _try_parse_bg_stats(dat: Path, names: Path) -> dict[str, float | None]:
    """Parse airgap body-mean / body-rms of Magnetic Flux Density 3 (Bz)."""
    out: dict[str, float | None] = {"mean": None, "rms": None}
    if not dat.is_file():
        return out
    text = dat.read_text(encoding="utf-8", errors="replace").strip()
    if not text:
        return out
    values = [float(x) for x in [ln for ln in text.splitlines() if ln.strip()][-1].split()]
    if not names.is_file():
        return out
    for ln in names.read_text(encoding="utf-8", errors="replace").splitlines():
        low = ln.lower()
        if "magnetic flux density" not in low:
            continue
        if not ("3" in low or "z" in low):
            continue
        try:
            idx = int(ln.strip().split(":", 1)[0]) - 1
        except ValueError:
            continue
        if not (0 <= idx < len(values)):
            continue
        val = float(values[idx])
        if "rms" in low:
            out["rms"] = val
        elif "mean" in low:
            out["mean"] = val
    return out


def _try_parse_bg_mean(dat: Path, names: Path) -> float | None:
    """Back-compat: prefer body mean Bz."""
    return _try_parse_bg_stats(dat, names).get("mean")


def _run_pipeline_host(work: Path) -> dict[str, Any]:
    from postprocess_ms import postprocess_magnetostatic_job  # noqa: WPS433

    solve = work / "solve"
    solve.mkdir(parents=True, exist_ok=True)
    for name in ("mesh.geo", "case.sif"):
        shutil.copy2(TEMPLATE_DIR / name, solve / name)

    steps = [
        ["gmsh", "mesh.geo", "-3", "-o", "mesh.msh"],
        ["ElmerGrid", "14", "2", "mesh.msh"],
        ["ElmerSolver", "case.sif"],
    ]
    log = work / "host_elmer.log"
    chunks: list[str] = []
    for cmd in steps:
        r = subprocess.run(cmd, cwd=solve, capture_output=True, text=True, check=False)
        chunks.append(f"$ {' '.join(cmd)}\n{r.stdout}\n{r.stderr}\nexit={r.returncode}\n")
        if r.returncode != 0:
            log.write_text("\n".join(chunks), encoding="utf-8")
            raise RuntimeError(f"host step failed: {cmd}; see {log}")
    log.write_text("\n".join(chunks), encoding="utf-8")
    pp = postprocess_magnetostatic_job(solve)
    bg_stats = _try_parse_bg_stats(solve / "scalars.dat", solve / "scalars.dat.names")
    return {
        "elmerExit": 0,
        "runMode": "host",
        "axialForceN": pp.get("axialForceN"),
        "magneticEnergyJ": pp.get("magneticEnergyJ"),
        "forceXN": pp.get("forceXN"),
        "forceYN": pp.get("forceYN"),
        "Bg_fem_body_mean_T": bg_stats.get("mean"),
        "Bg_fem_body_rms_T": bg_stats.get("rms"),
        "postprocess": pp.get("postprocess") or "maxwell",
        "ppNotes": pp.get("notes"),
        "log": str(log),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Q5-4 FEM calibration compare")
    ap.add_argument(
        "--keep-work",
        default=None,
        help="Optional directory to keep solve artifacts",
    )
    args = ap.parse_args()

    assert (TEMPLATE_DIR / "case.sif").is_file(), f"missing {TEMPLATE_DIR}"
    sif = (TEMPLATE_DIR / "case.sif").read_text(encoding="utf-8")
    assert "HeatSolve" not in sif and "Heat Equation" not in sif
    assert "WhitneyAVSolver" in sif
    assert "Magnetization" in sif

    ref = textbook_bg_and_force()
    work_ctx: Any
    if args.keep_work:
        work = Path(args.keep_work)
        work.mkdir(parents=True, exist_ok=True)
        work_ctx = None
    else:
        work_ctx = tempfile.TemporaryDirectory(prefix="mo-q54-calib-")
        work = Path(work_ctx.name)

    try:
        bins = _host_bins()
        missing = [k for k, v in bins.items() if not v]
        if not missing:
            result = _run_pipeline_host(work)
        else:
            container = _docker_container()
            if not container:
                print(
                    json.dumps(
                        {
                            "ok": False,
                            "error": (
                                "no Elmer on host and no docker mo-fem/mo-worker-fem"
                            ),
                            "missingHost": missing,
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                )
                return 1
            result = _run_pipeline_docker(container, work)

        fz_fem = result.get("axialForceN")
        if fz_fem is None:
            print(
                json.dumps(
                    {"ok": False, "error": "axialForceN missing", "result": result},
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 1

        fz_ref = ref["Fz_ref_N"]
        # Attractive force: FEM sign may be ±; compare magnitude to textbook pull
        fz_fem_mag = abs(float(fz_fem))
        rel_err = abs(fz_fem_mag - fz_ref) / abs(fz_ref) if fz_ref else float("inf")

        # Single-metric: Maxwell pressure from FEM airgap Bz.
        # Prefer body-rms: rms(Bz)^2 == mean(Bz^2), matching Maxwell B^2 pressure.
        bg_mean = result.get("Bg_fem_body_mean_T")
        bg_rms = result.get("Bg_fem_body_rms_T")
        bg_for_force = bg_rms if bg_rms is not None else bg_mean
        bg_kind = "body_rms" if bg_rms is not None else "body_mean"
        single: dict[str, Any] | None = None
        if bg_for_force is not None and abs(float(bg_for_force)) > 1e-12:
            fz_from_bg = (float(bg_for_force) ** 2) * ref["A_m2"] / (2.0 * MU0)
            rel_bg = abs(fz_fem_mag - fz_from_bg) / abs(fz_from_bg)
            single = {
                "metric": f"Fz_vs_Bg_{bg_kind}²A/(2μ0)",
                "Bg_fem_body_mean_T": float(bg_mean) if bg_mean is not None else None,
                "Bg_fem_body_rms_T": float(bg_rms) if bg_rms is not None else None,
                "Bg_used_T": float(bg_for_force),
                "Bg_used_kind": bg_kind,
                "Fz_from_Bg_N": fz_from_bg,
                "relError": rel_bg,
                "within_3pct": rel_bg <= TOL_REL,
                "note": (
                    "书面单指标：用 FEM 气隙 body-rms(Bz)（=√mean(Bz²)）代入 Maxwell 压强 "
                    "F=Bg²A/(2μ0)，检验力后处理与 B² 一致性；闭磁路下较 body-mean 更物理。"
                    "非独立激励标杆；1D 教材对比见 compare_1d。"
                ),
            }

        claimable_1d = rel_err <= TOL_REL
        claimable_single = bool(single and single["within_3pct"])
        # §4.3: either independent 1D OR written single-metric coverage
        claimable = claimable_1d or claimable_single

        out = {
            "schemaVersion": "fem-calibration-compare-v0",
            "caseId": "ms-gap-force-001",
            "templateId": "ms_gap_force_3d",
            "equationMode": "magnetostatic",
            "pending_calibration": not claimable,
            "heatProxyCounted": False,
            "toleranceRel": TOL_REL,
            "runMode": result["runMode"],
            "elmerExit": result["elmerExit"],
            "postprocess": result["postprocess"],
            "textbook": {
                "source": (
                    "非饱和气隙磁拉力（Maxwell 磁压强）:"
                    " Fz = Bg²·A/(2·μ0);"
                    " 一维磁路 Bg = Br·hm/(hm + g·μr_pm);"
                    " 教材/手册通式（如机电能量转换 / 电磁场教材气隙力章）"
                ),
                **ref,
            },
            "fem": {
                "axialForceN": float(fz_fem),
                "axialForceN_abs": fz_fem_mag,
                "magneticEnergyJ": result.get("magneticEnergyJ"),
                "forceXN": result.get("forceXN"),
                "forceYN": result.get("forceYN"),
                "Bg_fem_body_mean_T": bg_mean,
                "Bg_fem_body_rms_T": bg_rms,
            },
            "compare_1d": {
                "metric": "Fz_abs_vs_textbook_1D",
                "Fz_ref_N": fz_ref,
                "Fz_fem_abs_N": fz_fem_mag,
                "relError": rel_err,
                "within_3pct": claimable_1d,
            },
            "compare_single_metric_Bg": single,
            "claimable_fem_le_3pct": claimable,
            "claimScope": (
                "仅 verification case ms-gap-force-001 / 本模板；"
                "非完整 AF 电机；heat-proxy 不计"
            ),
            "tipAncestorRequired": "797ce67",
            "notes": (
                "magnetostatic ≠ heat-proxy; "
                "do not claim MVP; F2 only after Motor sign-off on report"
            ),
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        # Persist under repo-visible path when keep-work set
        if args.keep_work:
            (work / "calibration_compare.json").write_text(
                json.dumps(out, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        return 0
    finally:
        if work_ctx is not None:
            work_ctx.cleanup()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        raise SystemExit(1)
