"""Nonlinear reluctance network: series one-pole path with iterative μ(B)."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

from .materials import MU0, mu_steel, pm_mu_r


def reluctance_linear(length_m: float, area_m2: float, mu: float) -> float:
    """R = ℓ / (μ A). Guards against zero area."""
    a = max(float(area_m2), 1e-18)
    return float(length_m) / (float(mu) * a)


@dataclass
class BranchState:
    name: str
    length_m: float
    area_m2: float
    nonlinear: bool
    R: float = 0.0
    B: float = 0.0
    mu: float = MU0


@dataclass
class MecSolution:
    flux_wb: float
    mmf_total_a: float
    R_total: float
    branches: dict[str, BranchState]
    iterations: int
    converged: bool


def build_spm_branches(geo: dict[str, float], mur_pm: float | None = None) -> list[BranchState]:
    """Series SPM path: PM → airgap → tooth → stator yoke → rotor yoke."""
    mur = pm_mu_r() if mur_pm is None else float(mur_pm)
    return [
        BranchState("pm", geo["magnet_thickness_m"], geo["A_pm_m2"], False, mu=MU0 * mur),
        BranchState("airgap", geo["airgap_eff_m"], geo["A_g_m2"], False, mu=MU0),
        BranchState("stator_tooth", geo["L_tooth_m"], geo["A_tooth_m2"], True),
        BranchState("stator_yoke", geo["L_sy_m"], geo["A_sy_m2"], True),
        BranchState("rotor_yoke", geo["L_ry_m"], geo["A_ry_m2"], True),
    ]


def _update_branch_R(b: BranchState, flux_wb: float, mu_fn: Callable[[float], float]) -> None:
    b.B = flux_wb / max(b.area_m2, 1e-18)
    if b.nonlinear:
        b.mu = mu_fn(b.B)
    b.R = reluctance_linear(b.length_m, b.area_m2, b.mu)


def solve_series_mec(
    branches: list[BranchState],
    mmf_a: float,
    *,
    mu_fn: Callable[[float], float] = mu_steel,
    tol: float = 1e-4,
    max_iter: int = 80,
    flux0: float | None = None,
) -> MecSolution:
    """Iterate Φ = F / ΣR(B) until relative flux change < tol.

    Real magnetic-circuit fixed-point — not empirical scaling.
    Linear-only networks solve in one step (no under-relaxation).
    """
    for b in branches:
        if b.nonlinear:
            b.mu = mu_fn(0.0)
        b.R = reluctance_linear(b.length_m, b.area_m2, b.mu)

    any_nl = any(b.nonlinear for b in branches)
    phi = 0.0 if flux0 is None else float(flux0)
    converged = False
    it = 0

    for it in range(1, max_iter + 1):
        for b in branches:
            _update_branch_R(b, phi, mu_fn)
        R_tot = sum(b.R for b in branches)
        if R_tot <= 0.0 or not math.isfinite(R_tot):
            raise RuntimeError(f"invalid total reluctance {R_tot}")
        phi_new = float(mmf_a) / R_tot
        if not math.isfinite(phi_new):
            raise RuntimeError("non-finite flux in MEC iteration")

        if not any_nl:
            phi = phi_new
            for b in branches:
                _update_branch_R(b, phi, mu_fn)
            R_tot = sum(b.R for b in branches)
            converged = True
            break

        denom = max(abs(phi_new), 1e-16)
        if abs(phi_new - phi) / denom < tol:
            phi = phi_new
            for b in branches:
                _update_branch_R(b, phi, mu_fn)
            R_tot = sum(b.R for b in branches)
            converged = True
            break
        # Under-relax for stiff saturation
        phi = 0.45 * phi_new + 0.55 * phi

    R_tot = sum(b.R for b in branches)
    return MecSolution(
        flux_wb=phi,
        mmf_total_a=float(mmf_a),
        R_total=R_tot,
        branches={b.name: b for b in branches},
        iterations=it,
        converged=converged,
    )
