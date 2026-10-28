"""Q5-3 CREATOR 径向 PMSM 4p/6s（arXiv 2501.15921 Table 12）工厂与样例。"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from mo_geometry import (
    creator_radial_pmsm_4p6s,
    default_radial_pmsm,
    export_geometry_summary,
    rebuild_live_geometry,
    validate_radial,
)
from mo_geometry.radial import to_mems_geometry_fragment

_EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
_PREFIX = "radial_pmsm_creator_4p6s"


def _hard_errors(msgs: list[str]) -> list[str]:
    return [m for m in msgs if not m.startswith("warning:")]


def test_creator_validates_and_airgap_fit():
    p = creator_radial_pmsm_4p6s()
    assert _hard_errors(validate_radial(p)) == []
    # 47 + 2*0.4 = 47.8
    assert p["rotor"]["outerDiameter"] + 2 * p["airgap"] == pytest.approx(
        p["stator"]["innerDiameter"]
    )
    assert p["rotor"]["poleCount"] == 4
    assert p["stator"]["slotCount"] == 6
    assert p["rotor"]["magnetTopology"] == "IPM"
    assert p["machineType"] == "PMSM"
    assert p["topology"] == "RF"
    assert p["rotorTopology"] == "inner"
    assert p["stator"]["slotShape"] == "straight"
    assert p["stator"]["skewAngle"] is None
    assert p["rotor"]["magnetThickness"] == pytest.approx(4.35)
    assert p["axialActiveLength"] == pytest.approx(30.1)
    assert p["stator"]["stackLength"] == pytest.approx(30.1)


def test_creator_summary_si_poles_slots():
    p = creator_radial_pmsm_4p6s()
    s = export_geometry_summary(p)
    assert s["poles"] == 4
    assert s["slots"] == 6
    assert s["stack_length_m"] == pytest.approx(0.0301)
    assert s["airgap_m"] == pytest.approx(0.0004)
    assert s["rotor_od_m"] == pytest.approx(0.047)
    assert s["stator_id_m"] == pytest.approx(0.0478)
    assert s["magnet_thickness_m"] == pytest.approx(0.00435)


def test_default_radial_pmsm_unchanged_by_creator():
    """creator 工厂不得改坏 default demo 几何。"""
    d = default_radial_pmsm()
    assert d["rotor"]["poleCount"] == 6
    assert d["stator"]["slotCount"] == 18
    assert d["rotor"]["magnetTopology"] == "SPM"
    assert d["stator"]["outerDiameter"] == pytest.approx(80.0)
    c = creator_radial_pmsm_4p6s()
    assert c["rotor"]["poleCount"] != d["rotor"]["poleCount"]
    assert c["stator"]["slotCount"] != d["stator"]["slotCount"]


def test_examples_match_factory_live():
    p = creator_radial_pmsm_4p6s()
    live = rebuild_live_geometry(p)
    params_disk = json.loads((_EXAMPLES / f"{_PREFIX}_params.json").read_text())
    mesh_disk = json.loads((_EXAMPLES / f"{_PREFIX}_mesh.json").read_text())
    summary_disk = json.loads((_EXAMPLES / f"{_PREFIX}_geometry_summary.json").read_text())
    assert params_disk == to_mems_geometry_fragment(p)
    assert mesh_disk == live["meshDescriptor"]
    assert summary_disk == live["geometrySummary"]
    assert summary_disk["poles"] == 4
    assert summary_disk["slots"] == 6


def test_analytic_request_skeleton_shape():
    path = _EXAMPLES / f"{_PREFIX}_analytic_request.json"
    req = json.loads(path.read_text())
    assert req["topology"] == "RF"
    assert req["machine_type"] == "PMSM"
    g = req["geometry"]
    assert g["poles"] == 4
    assert g["slots"] == 6
    assert g["stack_length_m"] == pytest.approx(0.0301)
    assert g["airgap_m"] == pytest.approx(0.0004)
    assert g["rotor_od_m"] == pytest.approx(0.047)
    assert g["stator_id_m"] == pytest.approx(0.0478)
    assert g["magnet_thickness_m"] == pytest.approx(0.00435)
    # turns: (6/3)*328 = 656
    assert g["turns_per_phase"] == 656
    op = req["operating_point"]
    assert op["speed_rpm"] == 2000
    assert op["current_a_peak"] == pytest.approx(0.21 * math.sqrt(2), rel=1e-5)
    meta = req["meta"]
    assert meta["not_golden"] is True
    assert meta["pending_calibration"] is True
    assert meta["nc_binary_vendored"] is False
    assert "2501.15921" in meta["source"]["arxiv"]
