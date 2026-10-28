#!/usr/bin/env python3
"""Lightweight asserts: reluctance formula + nonlinear MEC convergence."""
from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from radial_mec.materials import MU0, mu_r_steel, mu_steel  # noqa: E402
from radial_mec.network import (  # noqa: E402
    BranchState,
    build_spm_branches,
    reluctance_linear,
    solve_series_mec,
)
from radial_mec.geometry import derive_mec_geometry  # noqa: E402


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
    # ~ Hc*hm with Br=1.2
    F = (1.2 / (MU0 * 1.05)) * geo["magnet_thickness_m"]
    sol = solve_series_mec(branches, F, tol=1e-4, max_iter=80)
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


def main() -> int:
    test_reluctance_vacuum()
    test_mu_saturates()
    test_linear_iron_matches_closed_form()
    test_mec_converges_on_fixture_geo()
    print("OK radial_mec tests: reluctance + convergence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
