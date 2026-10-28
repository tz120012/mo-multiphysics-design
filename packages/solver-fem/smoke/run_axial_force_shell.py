#!/usr/bin/env python3
"""Q4-8 smoke: axial magnetic pull special-report shell (placeholder / pending_calibration).

Does NOT run magnetostatics. Loads fixture + thinning dry-run AF artifacts.
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

FIXTURE = ROOT / "fixtures" / "q4_axial_force_placeholders.json"
REPORT = REPO / "docs" / "drafts" / "Q4-8-轴向磁拉力.md"


def main() -> int:
    fixture_path = Path(sys.argv[1]) if len(sys.argv) > 1 else FIXTURE
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))

    assert fixture.get("pending_calibration") is True, "fixture pending_calibration"
    assert fixture.get("axialForceN") is None, "fixture axialForceN must be null"
    assert fixture.get("bearingLoadN") is None, "fixture bearingLoadN must be null"
    assert fixture.get("deflectionHintMm") is None, "fixture deflectionHintMm must be null"
    assert REPORT.is_file(), f"missing report draft: {REPORT}"

    job_id = str(fixture.get("jobId") or "q4-8-axial-shell")
    with tempfile.TemporaryDirectory(prefix="mo-q48-") as tmp:
        published = write_result_artifacts(
            job_id=job_id,
            out_root=Path(tmp),
            topology="af",
            machine_type="pmsm",
            dim="3d",
            payload={
                "templateId": fixture.get("templateId") or "af_pmsm_3d",
                "axialForceN": fixture.get("axialForceN"),
                "bearingLoadN": fixture.get("bearingLoadN"),
                "deflectionHintMm": fixture.get("deflectionHintMm"),
            },
            dry_run=True,
            notes=fixture.get("notes")
            or "Q4-8 axial force shell; magnetostatics pending",
        )
        man = published["manifest"]
        sc = man.get("scalars") or {}
        assert man.get("topology") == "af"
        assert sc.get("pending_calibration") is True, "manifest pending_calibration"
        assert sc.get("dryRun") is True, "manifest dryRun"
        assert sc.get("axialForceN") is None, "manifest axialForceN"
        assert sc.get("bearingLoadN") is None, "manifest bearingLoadN"
        assert sc.get("deflectionHintMm") is None, "manifest deflectionHintMm"
        assert "lossesW" in sc

        scalars_file = Path(tmp) / "results" / "fem" / job_id / "scalars.json"
        assert scalars_file.is_file(), "scalars.json missing"
        full = json.loads(scalars_file.read_text(encoding="utf-8"))
        assert full.get("pending_calibration") is True

        try:
            report_rel = str(REPORT.relative_to(REPO))
        except ValueError:
            report_rel = str(REPORT)
        try:
            fix_rel = str(fixture_path.resolve().relative_to(REPO))
        except ValueError:
            fix_rel = str(fixture_path)

        out = {
            "schemaVersion": "axial-force-shell-v0",
            "pending_calibration": True,
            "reportDraft": report_rel,
            "fixture": fix_rel,
            "resultRef": published.get("resultRef"),
            "scalars": {
                "axialForceN": sc.get("axialForceN"),
                "bearingLoadN": sc.get("bearingLoadN"),
                "deflectionHintMm": sc.get("deflectionHintMm"),
                "pending_calibration": True,
                "dryRun": True,
                "templateId": fixture.get("templateId") or "af_pmsm_3d",
            },
            "notes": (
                "placeholder special-report shell; magnetostatics deferred; "
                "do NOT claim FEM ≤3%"
            ),
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))

    print("Q4-8 axial-force shell smoke OK (pending_calibration)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
