#!/usr/bin/env python3
"""Q7-3 同壳后处理契约 smoke（无 Elmer）：dry-run 两次 submit，断言同壳可读字段。

口径：零新 API；artifacts 形状可被 FE 同壳消费；heat-proxy ≠ MS；禁勾精度。
对照：docs/drafts/Q7-3-同壳后处理-FEM协作.md
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

DRAFT = REPO / "docs" / "drafts" / "Q7-3-同壳后处理-FEM协作.md"
REQUIRED_ROLES = frozenset({"scalars", "slice", "preview"})


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


def _assert_shell_readable(out: dict, *, expect_mode: str) -> dict:
    """Assert manifest/scalars shape FE can consume via GET /jobs/{id}/artifacts."""
    assert out.get("resultRef") == f"solver/fem/jobs/{out['jobId']}/manifest.json", (
        f"resultRef must point at manifest, got {out.get('resultRef')!r}"
    )
    man = out.get("manifest")
    assert isinstance(man, dict), "manifest missing on run_job return"
    sc = man.get("scalars") or {}
    assert sc.get("equationMode") == expect_mode, (
        f"manifest.scalars.equationMode want {expect_mode!r}, got {sc.get('equationMode')!r}"
    )
    assert sc.get("dryRun") is True, "同壳须能读 dryRun=true（本 smoke）"
    assert sc.get("pending_calibration") is True, "pending_calibration 须诚实（禁勾精度）"

    arts = man.get("artifacts") or []
    assert isinstance(arts, list) and arts, "artifacts[] 空则同壳无法拉精简件"
    roles = {a.get("role") for a in arts if isinstance(a, dict)}
    missing = REQUIRED_ROLES - roles
    assert not missing, f"artifacts 缺同壳三角色: {sorted(missing)}"

    for a in arts:
        if not isinstance(a, dict):
            continue
        if a.get("role") in REQUIRED_ROLES:
            path = a.get("path")
            assert isinstance(path, str) and path, f"artifact path 缺失: {a!r}"
            assert not path.startswith("/"), f"path 应为 mems 相对路径: {path!r}"

    man_path = Path(out["manifestPath"])
    assert man_path.is_file(), f"manifest 未落盘: {man_path}"
    disk = json.loads(man_path.read_text(encoding="utf-8"))
    assert (disk.get("scalars") or {}).get("equationMode") == expect_mode

    return {
        "jobId": out["jobId"],
        "resultRef": out["resultRef"],
        "equationMode": sc.get("equationMode"),
        "dryRun": sc.get("dryRun"),
        "pending_calibration": sc.get("pending_calibration"),
        "artifactRoles": sorted(r for r in roles if r is not None),
        "artifactsCount": len(arts),
    }


def main() -> int:
    assert DRAFT.is_file(), f"missing draft: {DRAFT}"

    with tempfile.TemporaryDirectory() as td:
        work = Path(td)

        job_a = str(uuid4())
        payload_a = _base_payload()
        out_a = run_job(job_a, payload_a, work, dry_run=True)

        job_b = str(uuid4())
        payload_b = _base_payload()
        payload_b["operatingPoint"] = {"rpm": 4500}
        payload_b["topology"] = "AF"
        payload_b["dim"] = "3d"
        payload_b["meshProfile"] = "af_pmsm_3d_ms_min"
        payload_b["templateId"] = "af_pmsm_3d_ms"
        payload_b["equationMode"] = "magnetostatic"
        out_b = run_job(job_b, payload_b, work, dry_run=True)

        assert out_a["jobId"] != out_b["jobId"]
        assert out_a["resultRef"] != out_b["resultRef"]

        shell_a = _assert_shell_readable(out_a, expect_mode="heat_proxy")
        shell_b = _assert_shell_readable(out_b, expect_mode="magnetostatic")

    report = {
        "schemaVersion": "q7-shell-postprocess-contract-v0",
        "pass": True,
        "draft": str(DRAFT.relative_to(REPO)),
        "notes": (
            "同壳消费既有 artifacts；manifest 含 equationMode/dryRun/pending_calibration；"
            "resultRef→manifest；三角色 scalars/slice/preview；"
            "heat-proxy≠MS；零新 API；不改 mems/files"
        ),
        "submit1": shell_a,
        "submit2": shell_b,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(json.dumps({"pass": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1) from exc
