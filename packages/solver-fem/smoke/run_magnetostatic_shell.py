#!/usr/bin/env python3
"""Q4+-5 / Q5-2 smoke: magnetostatic equationMode shell (no Elmer).

Structure + heat-proxy separation. True Elmer path:
  smoke/run_magnetostatic_truepath.py
Do NOT claim FEM ≤3%.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from thinning import write_result_artifacts  # noqa: E402

FIXTURE = ROOT / "fixtures" / "q4plus_magnetostatic_shell.json"
REPORT = REPO / "docs" / "drafts" / "Q4plus-5-磁静力学与轴向真值.md"
REPORT_Q5 = REPO / "docs" / "drafts" / "Q5-2-真磁静力学后处理.md"
TEMPLATE_META = ROOT / "templates" / "af_pmsm_3d_ms" / "template.json"


def main() -> int:
    fixture_path = Path(sys.argv[1]) if len(sys.argv) > 1 else FIXTURE
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))

    assert fixture.get("pending_calibration") is True, "fixture pending_calibration"
    assert fixture.get("equationMode") == "magnetostatic", "fixture equationMode"
    # Shell fixture may still say pathReady false (legacy shell-v0); template is SoT.
    assert fixture.get("axialForceN") is None, "fixture axialForceN must be null"
    assert fixture.get("bearingLoadN") is None, "fixture bearingLoadN must be null"
    assert fixture.get("deflectionHintMm") is None, "fixture deflectionHintMm must be null"
    assert REPORT.is_file(), f"missing boundary doc: {REPORT}"
    assert TEMPLATE_META.is_file(), f"missing template.json: {TEMPLATE_META}"

    meta = json.loads(TEMPLATE_META.read_text(encoding="utf-8"))
    assert meta.get("equationMode") == "magnetostatic", "template.json equationMode"
    assert meta.get("pending_calibration") is True, "template.json pending_calibration"
    # Q5-2: template marks true path ready; shell itself still does not run Elmer.
    assert meta.get("magnetostaticPathReady") is True, (
        "template.json magnetostaticPathReady expected true after Q5-2"
    )

    # heat-proxy templates must still exist and remain HeatEquation (not rewritten)
    heat_sif = ROOT / "templates" / "af_pmsm_3d" / "case.sif"
    assert heat_sif.is_file(), "af_pmsm_3d heat-proxy case.sif missing"
    heat_txt = heat_sif.read_text(encoding="utf-8")
    assert "HeatEquation" in heat_txt or "Heat Equation" in heat_txt, (
        "af_pmsm_3d must remain heat-proxy (HeatEquation)"
    )
    ms_sif = ROOT / "templates" / "af_pmsm_3d_ms" / "case.sif"
    ms_txt = ms_sif.read_text(encoding="utf-8")
    assert "HeatSolve" not in ms_txt
    assert "Equation = Heat Equation" not in ms_txt
    assert "WhitneyAVSolver" in ms_txt or "MagnetoDynamics" in ms_txt

    job_id = str(fixture.get("jobId") or "q4plus-5-ms-shell")
    with tempfile.TemporaryDirectory(prefix="mo-q4p5-") as tmp:
        published = write_result_artifacts(
            job_id=job_id,
            out_root=Path(tmp),
            topology=str(fixture.get("topology") or "AF"),
            machine_type=str(fixture.get("machineType") or "PMSM"),
            dim=str(fixture.get("dim") or "3d"),
            payload={
                "templateId": fixture.get("templateId") or "af_pmsm_3d_ms",
                "equationMode": "magnetostatic",
                "magnetostaticPathReady": True,
                "postprocess": "maxwell",
                "axialForceN": fixture.get("axialForceN"),
                "bearingLoadN": fixture.get("bearingLoadN"),
                "deflectionHintMm": fixture.get("deflectionHintMm"),
                "lossesW": fixture.get("lossesW") or {},
            },
            dry_run=True,
            notes=fixture.get("notes")
            or (
                "magnetostatic shell (no Elmer); true path = "
                "run_magnetostatic_truepath.py; pending_calibration — "
                "do NOT claim FEM ≤3%"
            ),
        )
        man = published["manifest"]
        sc = man.get("scalars") or {}
        assert man.get("topology") == "AF"
        assert sc.get("pending_calibration") is True, "manifest pending_calibration"
        assert sc.get("dryRun") is True, "manifest dryRun"
        assert sc.get("equationMode") == "magnetostatic", "manifest equationMode"
        assert sc.get("magnetostaticPathReady") is True, "manifest magnetostaticPathReady"
        assert sc.get("axialForceN") is None, "manifest axialForceN"
        assert sc.get("bearingLoadN") is None, "manifest bearingLoadN"
        assert sc.get("deflectionHintMm") is None, "manifest deflectionHintMm"
        assert "lossesW" in sc

        scalars_file = Path(tmp) / "results" / "fem" / job_id / "scalars.json"
        assert scalars_file.is_file(), "scalars.json missing"
        full = json.loads(scalars_file.read_text(encoding="utf-8"))
        assert full.get("pending_calibration") is True
        assert full.get("equationMode") == "magnetostatic"
        assert full.get("magnetostaticPathReady") is True

        try:
            report_rel = str(REPORT.relative_to(REPO))
        except ValueError:
            report_rel = str(REPORT)
        try:
            fix_rel = str(fixture_path.resolve().relative_to(REPO))
        except ValueError:
            fix_rel = str(fixture_path)

        out = {
            "schemaVersion": "magnetostatic-shell-v0",
            "equationMode": "magnetostatic",
            "pending_calibration": True,
            "magnetostaticPathReady": True,
            "reportDraft": report_rel,
            "truepathDoc": (
                str(REPORT_Q5.relative_to(REPO)) if REPORT_Q5.is_file() else str(REPORT_Q5)
            ),
            "truepathSmoke": "packages/solver-fem/smoke/run_magnetostatic_truepath.py",
            "fixture": fix_rel,
            "resultRef": published.get("resultRef"),
            "scalars": {
                "equationMode": "magnetostatic",
                "axialForceN": sc.get("axialForceN"),
                "bearingLoadN": sc.get("bearingLoadN"),
                "deflectionHintMm": sc.get("deflectionHintMm"),
                "pending_calibration": True,
                "magnetostaticPathReady": True,
                "dryRun": True,
                "templateId": fixture.get("templateId") or "af_pmsm_3d_ms",
                "lossesW": sc.get("lossesW"),
                "postprocess": "maxwell",
            },
            "notes": (
                "magnetostatic shell (no Elmer); heat-proxy ≠ magnetostatic; "
                "true path smoke = run_magnetostatic_truepath.py; "
                "do NOT claim FEM ≤3%"
            ),
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))

    print(
        "magnetostatic shell smoke OK (pending_calibration; pathReady=true on template)",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
