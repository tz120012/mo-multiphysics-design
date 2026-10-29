#!/usr/bin/env python3
"""Q6 改参→再触发 smoke（无 Elmer）：两次 dry-run submit，jobId/resultRef 必须不同。

口径：heat-proxy ≠ magnetostatic；不扩 F2；不改求解核心。
对照：docs/drafts/Q6-FEM-改参再触发.md
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from run_job import run_job  # noqa: E402

DRAFT = REPO / "docs" / "drafts" / "Q6-FEM-改参再触发.md"


def _base_payload() -> dict:
    return {
        "topology": "RF",
        "machineType": "PMSM",
        "dim": "2d",
        "solverKernel": "elmer",
        "meshProfile": "rf_pmsm_2d_default",
        "operatingPoint": {"rpm": 3000},
        "materials": {"magnet": "N42"},
    }


def main() -> int:
    assert DRAFT.is_file(), f"missing draft: {DRAFT}"

    with tempfile.TemporaryDirectory() as td:
        work = Path(td)

        # 第一次：缺省 / heat_proxy 兼容路径
        job_a = str(uuid4())
        payload_a = _base_payload()
        out_a = run_job(job_a, payload_a, work, dry_run=True)

        # 第二次：改参（OP + 切到磁静力学模板）→ 必须新 job
        job_b = str(uuid4())
        payload_b = _base_payload()
        payload_b["operatingPoint"] = {"rpm": 4500}
        payload_b["topology"] = "AF"
        payload_b["dim"] = "3d"
        payload_b["meshProfile"] = "af_pmsm_3d_ms_min"
        payload_b["templateId"] = "af_pmsm_3d_ms"
        payload_b["equationMode"] = "magnetostatic"
        out_b = run_job(job_b, payload_b, work, dry_run=True)

    assert out_a["jobId"] != out_b["jobId"], "jobId must differ across re-triggers"
    assert out_a["resultRef"] != out_b["resultRef"], "resultRef must differ (no silent reuse)"
    assert out_a["equationMode"] == "heat_proxy", (
        f"first submit must be heat_proxy, got {out_a['equationMode']!r}"
    )
    assert out_b["equationMode"] == "magnetostatic", (
        f"second submit must be magnetostatic, got {out_b['equationMode']!r}"
    )
    # 诚实：不得把两次结果混为同一 artifacts 路径
    assert out_a["resultRef"] == f"solver/fem/jobs/{job_a}/manifest.json"
    assert out_b["resultRef"] == f"solver/fem/jobs/{job_b}/manifest.json"

    report = {
        "schemaVersion": "q6-retrigger-smoke-v0",
        "pass": True,
        "draft": str(DRAFT.relative_to(REPO)),
        "notes": (
            "改参后须新 job；禁止静默复用旧 artifacts；"
            "heat-proxy ≠ magnetostatic；组装在 FE/API；solver-fem 入口不变"
        ),
        "submit1": {
            "jobId": out_a["jobId"],
            "resultRef": out_a["resultRef"],
            "equationMode": out_a["equationMode"],
            "operatingPoint": payload_a["operatingPoint"],
        },
        "submit2": {
            "jobId": out_b["jobId"],
            "resultRef": out_b["resultRef"],
            "equationMode": out_b["equationMode"],
            "operatingPoint": payload_b["operatingPoint"],
            "templateId": payload_b["templateId"],
        },
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(json.dumps({"pass": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1) from exc
