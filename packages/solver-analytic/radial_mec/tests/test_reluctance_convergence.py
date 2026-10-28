#!/usr/bin/env python3
"""Lightweight asserts: reluctance, nonlinear MEC convergence, reproducibility, dispatch."""
from __future__ import annotations

import copy
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from radial_mec.materials import MU0, mu_r_steel, mu_steel  # noqa: E402
from radial_mec.network import (  # noqa: E402
    MEC_MAX_ITER,
    MEC_TOL,
    BranchState,
    build_spm_branches,
    reluctance_linear,
    solve_series_mec,
)
from radial_mec.geometry import derive_mec_geometry  # noqa: E402
from radial_mec import solve_radial_pmsm_mec  # noqa: E402
from solve import solve  # noqa: E402

FIXTURE = ROOT / "smoke" / "fixtures" / "radial_pmsm_request.json"


def _physics_key(out: dict) -> tuple:
    """Comparable physics tuple (exclude wall-clock elapsed_ms)."""
    return (
        out["torque_nm"],
        out["back_emf_v_peak"],
        out["losses_w"]["copper"],
        out["losses_w"]["iron"],
        out["losses_w"].get("magnet_eddy"),
        out["inductance_h"]["ld"],
        out["inductance_h"]["lq"],
        out["meta"]["mec"]["flux_pole_wb"],
        out["meta"]["mec"]["B_airgap_t"],
        out["meta"]["mec"]["iterations"],
        out["meta"]["mec"]["converged"],
    )


def test_reluctance_vacuum():
    R = reluctance_linear(0.001, 0.01, MU0)
    expect = 0.001 / (MU0 * 0.01)
    assert abs(R - expect) / expect < 1e-12


def test_mu_saturates():
    assert mu_r_steel(0.1) > 1000.0
    assert mu_r_steel(1.8) < mu_r_steel(0.5)
    assert mu_steel(0.0) > MU0


def test_mec_converges_on_fixture_geo():
    notes: list[str] = []
    geo = derive_mec_geometry(
        {
            "poles": 10,
            "slots": 12,
            "stack_length_m": 0.04,
            "airgap_m": 0.0008,
            "rotor_od_m": 0.06,
            "stator_id_m": 0.0616,
            "magnet_thickness_m": 0.003,
            "turns_per_phase": 48,
        },
        notes,
    )
    branches = build_spm_branches(geo)
    F = (1.2 / (MU0 * 1.05)) * geo["magnet_thickness_m"]
    sol = solve_series_mec(branches, F, tol=MEC_TOL, max_iter=MEC_MAX_ITER)
    assert sol.converged, f"did not converge in {sol.iterations} iters"
    assert math.isfinite(sol.flux_wb) and sol.flux_wb > 0.0
    bg = sol.branches["airgap"].B
    assert 0.2 < abs(bg) < 1.6, f"unrealistic Bg={bg}"
    for name in ("stator_tooth", "stator_yoke", "rotor_yoke"):
        b = abs(sol.branches[name].B)
        assert b < 2.2, f"{name} B={b} oversaturated beyond model intent"


def test_linear_iron_matches_closed_form():
    """With fixed μ, one step must match Φ = F / ΣR."""
    branches = [
        BranchState("a", 0.002, 0.01, False, mu=MU0),
        BranchState("b", 0.01, 0.005, False, mu=2000 * MU0),
    ]
    for b in branches:
        b.R = reluctance_linear(b.length_m, b.area_m2, b.mu)
    F = 1000.0
    R = sum(b.R for b in branches)
    phi_cf = F / R
    sol = solve_series_mec(branches, F, tol=1e-9, max_iter=5)
    assert abs(sol.flux_wb - phi_cf) / phi_cf < 1e-6


def test_pmsm_reproducible():
    """Same fixture → bit-identical physics (no RNG; fixed MEC params)."""
    req = json.loads(FIXTURE.read_text(encoding="utf-8"))
    a = solve_radial_pmsm_mec(copy.deepcopy(req))
    b = solve_radial_pmsm_mec(copy.deepcopy(req))
    assert _physics_key(a) == _physics_key(b)
    assert a["meta"]["mec"]["tol"] == MEC_TOL
    assert a["meta"]["mec"]["max_iter"] == MEC_MAX_ITER
    assert a["meta"]["mock"] is False


def test_torque_scales_with_current():
    """SPM: |T| rises with Iq (gamma=0); monotonic on a coarse grid."""
    req = json.loads(FIXTURE.read_text(encoding="utf-8"))
    torques = []
    for i_pk in (5.0, 15.0, 25.0, 40.0):
        r = copy.deepcopy(req)
        r["operating_point"]["current_a_peak"] = i_pk
        r["operating_point"]["gamma_deg"] = 0.0
        out = solve_radial_pmsm_mec(r)
        torques.append(out["torque_nm"])
        assert math.isfinite(out["torque_nm"])
    # Strictly increasing for this unsaturated / mildly sat SPM path
    for a, b in zip(torques, torques[1:]):
        assert b > a, f"torque not increasing with current: {torques}"
    # Near-linear at low current: T(25)/T(5) roughly ~5 (allow saturation sag)
    ratio = torques[2] / torques[0]
    assert 3.0 < ratio < 6.5, f"unexpected T vs I ratio {ratio}"


def test_mock_vs_mec_dispatch():
    req = json.loads(FIXTURE.read_text(encoding="utf-8"))
    mock = solve(req, solver="mock")
    mec = solve(req, solver="mec")
    assert mock["meta"]["solver"] == "mock" and mock["meta"]["mock"] is True
    assert mec["meta"]["solver"] == "mec" and mec["meta"]["mock"] is False
    # Different models → different numbers (sanity that paths truly diverge)
    assert mock["torque_nm"] != mec["torque_nm"]


def test_acim_dispatch_and_finite():
    acim_path = ROOT / "smoke" / "fixtures" / "radial_acim_request.json"
    req = json.loads(acim_path.read_text(encoding="utf-8"))
    out = solve(req, solver="mec")
    assert out["meta"]["solver"] == "acim_equiv"
    assert out["meta"]["mock"] is False
    assert math.isfinite(out["torque_nm"])
    assert math.isfinite(out["losses_w"]["rotor_bar"])
    # Reproducibility
    out2 = solve(copy.deepcopy(req), solver="mec")
    assert out["torque_nm"] == out2["torque_nm"]
    assert out["back_emf_v_peak"] == out2["back_emf_v_peak"]
    assert out["losses_w"]["rotor_bar"] == out2["losses_w"]["rotor_bar"]


def main() -> int:
    test_reluctance_vacuum()
    test_mu_saturates()
    test_linear_iron_matches_closed_form()
    test_mec_converges_on_fixture_geo()
    test_pmsm_reproducible()
    test_torque_scales_with_current()
    test_mock_vs_mec_dispatch()
    test_acim_dispatch_and_finite()
    print(
        "OK radial_mec tests: reluctance + convergence + reproduce + "
        "T(I) + mock/mec + acim"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
