"""rebuild_examples / live path smoke."""

from __future__ import annotations

import json
from pathlib import Path

from mo_geometry.rebuild_examples import rebuild


def test_rebuild_examples_writes_af_fields(tmp_path: Path):
    written = rebuild(tmp_path)
    assert written
    summary = json.loads((tmp_path / "axial_af_pmsm_rfmr_geometry_summary.json").read_text())
    assert summary["outer_radius_m"] == 0.06
    assert summary["inner_radius_m"] == 0.02
    assert summary["disk_thickness_m"] == summary["stack_length_m"]
    assert summary["disk_count"] == 3
    assert summary["n_planes"] == 4
    assert "magnet_arc_ratio" in summary

    entry = json.loads((tmp_path / "axial_af_pmsm_rfmr_pipeline_entry.json").read_text())
    assert entry["analyticSolveStub"]["geometry"] == summary
