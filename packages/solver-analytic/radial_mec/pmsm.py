"""Radial RF + PMSM nonlinear MEC → SolveResult-compatible dict."""
from __future__ import annotations

import copy
import math
import time
from typing import Any

from materials_adapter import resolve_from_request

from .geometry import derive_mec_geometry
from .materials import pm_hc
from .network import MEC_MAX_ITER, MEC_TOL, build_spm_branches, solve_series_mec

# Fixed incremental current for Ld/Lq — no adaptive/random steps (reproducibility).
_L_DI_FRAC = 0.05
_L_DI_MIN = 0.1


def _note_join(notes: list[str]) -> str:
    base = (
        "Radial SPM PMSM MEC v0 (series one-pole path, analytic steel μ(B)). "
        "Engineering first cut — not calibrated to ≤5%."
    )
    if notes:
        return base + " Defaults: " + "; ".join(notes)
    return base


def _phase_resistance(geo: dict[str, float], sigma: float) -> float:
    """Crude phase resistance from mean turn length and copper fill guess."""
    L = geo["stack_length_m"]
    end = math.pi * geo["tau_s_m"] * 1.5
    mlt = 2.0 * (L + end)
    turns = geo["turns_per_phase"]
    a_cond = max(1.5e-6, 0.15 * geo["A_tooth_m2"] / max(turns / geo["n_teeth_per_pole"], 1.0))
    return turns * mlt / (sigma * a_cond)


def _iron_volume(geo: dict[str, float]) -> tuple[float, float]:
    """(tooth_volume, yoke_volume) rough [m³]."""
    v_tooth = geo["A_tooth_m2"] * geo["L_tooth_m"] * geo["poles"]
    v_sy = geo["A_sy_m2"] * geo["L_sy_m"] * geo["poles"]
    v_ry = geo["A_ry_m2"] * geo["L_ry_m"] * geo["poles"]
    return v_tooth, v_sy + v_ry


def _steinmetz_iron_w(
    B_tooth: float,
    B_yoke: float,
    v_tooth: float,
    v_yoke: float,
    f_hz: float,
    *,
    kh: float = 150.0,
    alpha: float = 1.8,
    ke: float = 0.8,
) -> float:
    """Coarse iron loss: Ph = kh f B^α + Pe = ke (f B)^2, volumes in m³ → W."""

    def p(B: float) -> float:
        b = abs(B)
        return kh * abs(f_hz) * (b**alpha) + ke * (f_hz * b) ** 2

    return p(B_tooth) * max(v_tooth, 0.0) + p(B_yoke) * max(v_yoke, 0.0)


def _solve_flux_for_mmf(geo: dict[str, float], mmf_a: float, mur_pm: float):
    branches = build_spm_branches(geo, mur_pm=mur_pm)
    return solve_series_mec(branches, mmf_a, tol=MEC_TOL, max_iter=MEC_MAX_ITER)


def solve_radial_pmsm_mec(request: dict[str, Any]) -> dict[str, Any]:
    """Public entry: SolveRequest-like dict → SolveResult-like dict.

    ``meta.solver='mec'``, ``meta.mock=false``.
    Physics outputs are deterministic for a fixed request (no RNG; fixed MEC tol/iters).
    """
    t0 = time.perf_counter()
    notes: list[str] = []

    if request.get("topology") != "RF":
        raise ValueError("radial_mec only supports topology=RF")
    if request.get("machine_type") not in ("PMSM", "BLDC"):
        raise ValueError("radial_mec PMSM/BLDC path only; ACIM uses machines.acim_equiv")

    is_bldc = request.get("machine_type") == "BLDC"
    if is_bldc:
        notes.append(
            "BLDC uses same SPM MEC magnetic path with square-wave current-angle/"
            "coefficient approx (meta.bldc_approx); not a full trapezoidal model"
        )

    g_in = request.get("geometry") or {}
    op = request.get("operating_point") or {}

    geo = derive_mec_geometry(g_in, notes)
    mat = resolve_from_request(request, need_magnet=True, need_bar=False)
    notes.extend(mat.notes)

    br = mat.br_t
    mur_pm = mat.mur_pm
    sigma = mat.sigma_copper

    n_rpm = float(op.get("speed_rpm", 0.0))
    i_pk = float(op.get("current_a_peak", 0.0))
    gamma_deg = float(op.get("gamma_deg", 0.0))
    # BLDC approx: treat as flat-top aligned current (gamma→0) with 2/√3 crest factor note
    if is_bldc and "gamma_deg" not in op:
        gamma_deg = 0.0
        notes.append("BLDC gamma_deg defaulted to 0 (aligned flat-top approx)")
    gamma = math.radians(gamma_deg)
    # Convention (matches Gate0 mock): gamma=0 → Iq = Ipeak (max torque for SPM)
    iq = i_pk * math.cos(gamma)
    id_ = -i_pk * math.sin(gamma)
    if is_bldc:
        # Square-wave / six-step: crude 2/√3 vs sine peak torque coefficient
        bldc_k = 2.0 / math.sqrt(3.0)
        iq = iq * bldc_k
        notes.append(f"BLDC torque coeff {bldc_k:.6g} applied on Iq")

    poles = geo["poles"]
    p = geo["pole_pairs"]
    kw = geo["kw"]
    Nph = geo["turns_per_phase"]

    F_pm = pm_hc(br, mur_pm) * geo["magnet_thickness_m"]
    F_d = 1.5 * Nph * kw * id_ / max(p, 1.0)
    F_net = F_pm + F_d

    sol = _solve_flux_for_mmf(geo, F_net, mur_pm)
    phi_pole = sol.flux_wb

    B_g = sol.branches["airgap"].B
    B_tooth = sol.branches["stator_tooth"].B
    B_sy = sol.branches["stator_yoke"].B
    B_ry = sol.branches["rotor_yoke"].B

    psi_pm = kw * Nph * abs(phi_pole)

    omega_m = n_rpm * 2.0 * math.pi / 60.0
    omega_e = p * omega_m
    back_emf = omega_e * psi_pm

    torque = 1.5 * p * psi_pm * iq

    di = max(_L_DI_FRAC * max(abs(i_pk), 1.0), _L_DI_MIN)

    def psi_for_id_iq(id_val: float, iq_val: float) -> tuple[float, float]:
        F_d_loc = 1.5 * Nph * kw * id_val / max(p, 1.0)
        sol_d = _solve_flux_for_mmf(geo, F_pm + F_d_loc, mur_pm)
        psi_d = kw * Nph * sol_d.flux_wb
        F_q = 1.5 * Nph * kw * iq_val / max(p, 1.0)
        branches_q = build_spm_branches(geo, mur_pm=mur_pm)
        sol_q = solve_series_mec(branches_q, F_q, tol=MEC_TOL, max_iter=MEC_MAX_ITER)
        psi_q = kw * Nph * sol_q.flux_wb
        return psi_d, psi_q

    psi_d0, psi_q0 = psi_for_id_iq(id_, iq if not is_bldc else i_pk * math.cos(gamma))
    psi_d1, _ = psi_for_id_iq(id_ + di, iq if not is_bldc else i_pk * math.cos(gamma))
    _, psi_q1 = psi_for_id_iq(id_, (iq if not is_bldc else i_pk * math.cos(gamma)) + di)
    ld = abs((psi_d1 - psi_d0) / di)
    lq = abs((psi_q1 - psi_q0) / di)

    i_rms = i_pk / math.sqrt(2.0)
    # Copper: 3·I_rms²·R_ph (three-phase). Optional measured/override R from
    # materials.rs_ohm | phase_resistance_ohm (e.g. CREATOR Table 10).
    mats_in = request.get("materials") or {}
    r_override = mats_in.get("rs_ohm", mats_in.get("phase_resistance_ohm"))
    if r_override is not None:
        r_ph = float(r_override)
        notes.append(f"phase resistance overridden from materials.rs_ohm={r_ph:g} Ω")
    else:
        r_ph = _phase_resistance(geo, sigma)
    copper = 3.0 * i_rms**2 * r_ph

    f_hz = abs(n_rpm) * p / 60.0
    v_tooth, v_yoke = _iron_volume(geo)
    B_yoke_mean = 0.5 * (abs(B_sy) + abs(B_ry))
    iron = _steinmetz_iron_w(
        B_tooth,
        B_yoke_mean,
        v_tooth,
        v_yoke,
        f_hz,
        kh=mat.steel_kh,
        alpha=mat.steel_alpha,
        ke=mat.steel_ke,
    )

    v_pm = geo["A_pm_m2"] * geo["magnet_thickness_m"] * poles
    magnet_eddy = 0.02 * (B_g**2) * (f_hz**2) * v_pm

    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    result: dict[str, Any] = {
        "schema_version": request.get("schema_version", "0.0.0-gate0"),
        "meta": {
            "solver": "mec",
            "elapsed_ms": round(elapsed_ms, 3),
            "mock": False,
            "note": _note_join(notes),
            "mec": {
                "converged": sol.converged,
                "iterations": sol.iterations,
                "tol": MEC_TOL,
                "max_iter": MEC_MAX_ITER,
                "flux_pole_wb": phi_pole,
                "B_airgap_t": B_g,
                "B_tooth_t": B_tooth,
                "B_stator_yoke_t": B_sy,
                "B_rotor_yoke_t": B_ry,
                "R_total": sol.R_total,
                "F_pm_a": F_pm,
                "F_net_a": F_net,
                "psi_pm_wb": psi_pm,
            },
            "materials_sources": mat.sources,
        },
        "torque_nm": float(torque),
        "back_emf_v_peak": float(back_emf),
        "losses_w": {
            "copper": float(max(copper, 0.0)),
            "iron": float(max(iron, 0.0)),
            "magnet_eddy": float(max(magnet_eddy, 0.0)),
        },
        "inductance_h": {"ld": float(ld), "lq": float(lq)},
    }
    if is_bldc:
        result["meta"]["bldc_approx"] = True
        result["meta"]["note"] = result["meta"]["note"] + " [BLDC approx path]"
    return result


def solve_radial_pmsm_mec_copy(request: dict[str, Any]) -> dict[str, Any]:
    """Same as solve_radial_pmsm_mec but does not mutate caller input."""
    return solve_radial_pmsm_mec(copy.deepcopy(request))
