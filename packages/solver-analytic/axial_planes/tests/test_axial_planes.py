#!/usr/bin/env python3
"""AF multi-plane: reproducibility, n_planes, illegal topology/machine."""
from __future__ import annotations

import copy
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from axial_planes import solve_axial_pmsm_planes  # noqa: E402
from axial_planes.geometry import derive_plane_geometry  # noqa: E402
from solve import solve  # noqa: E402

FIXTURE = ROOT / "smoke" / "fixtures" / "axial_pmsm_request.json"


def _physics_key(out: dict) -> tuple:
    return (
        out["torque_nm"],
        out["back_emf_v_peak"],
        out["losses_w"]["copper"],
        out["losses_w"]["iron"],
        out["losses_w"].get("magnet_eddy"),
        out["inductance_h"]["ld"],
        out["inductance_h"]["lq"],
        out["meta"]["n_planes"],
        out["meta"]["axial"]["flux_pole_sum_wb"],
        out["meta"]["axial"]["B_airgap_mean_t"],
        out["meta"]["axial"]["converged"],
    )


def test_fixture_reproducible():
    req = json.loads(FIXTURE.read_text(encoding="utf-8"))
    a = solve(req)
    b = solve(copy.deepcopy(req))
    assert a["meta"]["solver"] == "axial_planes"
    assert a["meta"]["mock"] is False
    assert _physics_key(a) == _physics_key(b)
    assert math.isfinite(a["torque_nm"]) and abs(a["torque_nm"]) > 0


def test_n_planes_at_least_one():
    req = json.loads(FIXTURE.read_text(encoding="utf-8"))
    req["geometry"]["n_planes"] = 1
    out = solve_axial_pmsm_planes(req)
    assert out["meta"]["n_planes"] == 1
    assert len(out["meta"]["axial"]["planes"]) == 1
    assert abs(out["torque_nm"]) > 0


def test_n_planes_scales_rings():
    req = json.loads(FIXTURE.read_text(encoding="utf-8"))
    notes: list[str] = []
    _, planes3 = derive_plane_geometry(req["geometry"], notes, n_planes=3)
    notes2: list[str] = []
    _, planes5 = derive_plane_geometry(req["geometry"], notes2, n_planes=5)
    assert len(planes3) == 3
    assert len(planes5) == 5
    # Equal radial coverage
    span3 = planes3[-1]["r_outer_m"] - planes3[0]["r_inner_m"]
    span5 = planes5[-1]["r_outer_m"] - planes5[0]["r_inner_m"]
    assert abs(span3 - span5) < 1e-12


def test_reject_rf_on_axial_entry():
    req = json.loads(FIXTURE.read_text(encoding="utf-8"))
    req["topology"] = "RF"
    try:
        solve_axial_pmsm_planes(req)
        assert False, "expected ValueError"
    except ValueError as e:
        assert "AF" in str(e)


def test_reject_af_bldc():
    req = json.loads(FIXTURE.read_text(encoding="utf-8"))
    req["machine_type"] = "BLDC"
    try:
        solve(req, solver="mec")
        assert False, "expected ValueError"
    except ValueError as e:
        assert "BLDC" in str(e) or "PMSM" in str(e)


def test_reject_af_acim():
    req = json.loads(FIXTURE.read_text(encoding="utf-8"))
    req["machine_type"] = "ACIM"
    try:
        solve(req, solver="mec")
        assert False, "expected ValueError"
    except ValueError as e:
        assert "ACIM" in str(e) or "PMSM" in str(e)


def test_stub_mapping_radii():
    """rotor_od_m / stator_id_m are diameters → radii half."""
    notes: list[str] = []
    common, planes = derive_plane_geometry(
        {
            "poles": 16,
            "slots": 18,
            "airgap_m": 0.001,
            "rotor_od_m": 0.12,
            "stator_id_m": 0.06,
            "stack_length_m": 0.008,
            "magnet_thickness_m": 0.004,
            "n_planes": 4,
        },
        notes,
    )
    assert abs(common["outer_radius_m"] - 0.06) < 1e-15
    assert abs(common["inner_radius_m"] - 0.03) < 1e-15
    assert len(planes) == 4


def main() -> int:
    test_fixture_reproducible()
    test_n_planes_at_least_one()
    test_n_planes_scales_rings()
    test_reject_rf_on_axial_entry()
    test_reject_af_bldc()
    test_reject_af_acim()
    test_stub_mapping_radii()
    print("OK axial_planes tests")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
