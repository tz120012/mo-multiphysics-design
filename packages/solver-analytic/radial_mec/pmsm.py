"""Radial RF + PMSM nonlinear MEC → SolveResult-compatible dict."""
from __future__ import annotations

import copy
import math
import time
from typing import Any

from .geometry import derive_mec_geometry
from .materials import MU0, pm_hc, pm_mu_r
from .network import build_spm_branches, solve_series_mec


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
    # Mean turn ≈ 2*(L + end-turn); end-turn ~ π * tau_s-ish * factor
    L = geo["stack_length_m"]
    end = math.pi * geo["tau_s_m"] * 1.5
    mlt = 2.0 * (L + end)
    turns = geo["turns_per_phase"]
    # Slot copper area rough: 0.4 * (0.5*tau_s) * ht * fill 0.4 / (conductors...)
    # Use equivalent conductor cross-section so R stays in a sensible band
    a_cond = max(1.5e-6, 0.15 * geo["A_tooth_m2"] / max(turns / geo["n_teeth_per_pole"], 1.0))
    return turns * mlt / (sigma * a_cond)


def _iron_volume(geo: dict[str, float]) -> tuple[float, float]:
    """(tooth_volume, yoke_volume) rough [m³]."""
    v_tooth = geo["A_tooth_m2"] * geo["L_tooth_m"] * geo["poles"]
    # Full stator + rotor yoke rings approx
    v_sy = geo["A_sy_m2"] * math.pi * (geo["stator_id_m"] + 2 * geo["L_tooth_m"] + 0.5 * (
        geo["A_sy_m2"] / max(geo["stack_length_m"], 1e-12)
    ))
    # Simpler: yoke path * area * poles (already L_sy is per-pole arc)
    v_sy = geo["A_sy_m2"] * geo["L_sy_m"] * geo["poles"]
    v_ry = geo["A_ry_m2"] * geo["L_ry_m"] * geo["poles"]
    return v_tooth, v_sy + v_ry


def _steinmetz_iron_w(
    B_tooth: float,
    B_yoke: float,
    v_tooth: float,
    v_yoke: float,
    f_hz: float,
) -> float:
    """Coarse iron loss: Ph = kh f B^α + Pe = ke (f B)^2, volumes in m³ → W."""
    # Densities tuned for demo steel (W/m³ scale)
    kh, alpha, ke = 150.0, 1.8, 0.8
    def p(B: float) -> float:
        b = abs(B)
        return kh * abs(f_hz) * (b**alpha) + ke * (f_hz * b) ** 2

    return p(B_tooth) * max(v_tooth, 0.0) + p(B_yoke) * max(v_yoke, 0.0)


def _solve_flux_for_mmf(geo: dict[str, float], mmf_a: float, mur_pm: float):
    branches = build_spm_branches(geo, mur_pm=mur_pm)
    return solve_series_mec(branches, mmf_a)


def solve_radial_pmsm_mec(request: dict[str, Any]) -> dict[str, Any]:
    """Public entry: SolveRequest-like dict → SolveResult-like dict.

    ``meta.solver='mec'``, ``meta.mock=false``.
    """
    t0 = time.perf_counter()
    notes: list[str] = []

    if request.get("topology") != "RF":
        raise ValueError("radial_mec only supports topology=RF")
    if request.get("machine_type") != "PMSM":
        raise ValueError("radial_mec PMSM path only; BLDC/ACIM not in this module yet")

    g_in = request.get("geometry") or {}
    m_in = request.get("materials") or {}
    op = request.get("operating_point") or {}

    geo = derive_mec_geometry(g_in, notes)

    br = float(m_in["br_t"]) if m_in.get("br_t") is not None else 1.2
    if m_in.get("br_t") is None:
        notes.append("br_t defaulted to 1.2 T")
    mur_pm = pm_mu_r(float(m_in["mur_pm"])) if m_in.get("mur_pm") is not None else pm_mu_r()
    if m_in.get("mur_pm") is None:
        notes.append("mur_pm defaulted to 1.05")

    sigma = float(m_in["sigma_copper"]) if m_in.get("sigma_copper") is not None else 5.8e7
    if m_in.get("sigma_copper") is None:
        notes.append("sigma_copper defaulted to 5.8e7 S/m")

    n_rpm = float(op.get("speed_rpm", 0.0))
    i_pk = float(op.get("current_a_peak", 0.0))
    gamma_deg = float(op.get("gamma_deg", 0.0))
    gamma = math.radians(gamma_deg)
    # Convention (matches Gate0 mock): gamma=0 → Iq = Ipeak (max torque for SPM)
    iq = i_pk * math.cos(gamma)
    id_ = -i_pk * math.sin(gamma)

    poles = geo["poles"]
    p = geo["pole_pairs"]
    kw = geo["kw"]
    Nph = geo["turns_per_phase"]

    # --- PM MMF and no-load / load flux ---
    # F_pm = Hc * hm; armature MMF on d-axis opposes/aids PM (simplified)
    F_pm = pm_hc(br, mur_pm) * geo["magnet_thickness_m"]
    # Peak fundamental stator MMF (ampere-turns) referred to one pole path
    # F_s ≈ (3/2) * (Nph * kw * I) / p   then /2 for half-path pairing ≈ /p factor
    F_s_peak = 1.5 * Nph * kw * i_pk / max(p, 1.0)
    # d-axis component of armature reaction (demagnetizing when id < 0)
    F_d = 1.5 * Nph * kw * id_ / max(p, 1.0)
    # Net MMF driving airgap flux (PM + d-axis AR); q-axis mainly torque, weak flux for SPM
    F_net = F_pm + F_d

    sol = _solve_flux_for_mmf(geo, F_net, mur_pm)
    phi_pole = sol.flux_wb  # Wb per pole path

    B_g = sol.branches["airgap"].B
    B_tooth = sol.branches["stator_tooth"].B
    B_sy = sol.branches["stator_yoke"].B
    B_ry = sol.branches["rotor_yoke"].B

    # Phase flux linkage peak (fundamental): ψ = kw * Nph * Φ_pole
    # (one pole flux links the phase with winding factor)
    psi_pm = kw * Nph * abs(phi_pole)

    omega_m = n_rpm * 2.0 * math.pi / 60.0
    omega_e = p * omega_m
    back_emf = omega_e * psi_pm  # V peak (phase)

    # Electromagnetic torque (SPM): T = (3/2) * p * ψ_pm * Iq
    torque = 1.5 * p * psi_pm * iq

    # --- Ld / Lq via incremental flux (small ΔI) ---
    di = max(0.05 * max(abs(i_pk), 1.0), 0.1)

    def psi_for_id_iq(id_val: float, iq_val: float) -> tuple[float, float]:
        F_d_loc = 1.5 * Nph * kw * id_val / max(p, 1.0)
        sol_d = _solve_flux_for_mmf(geo, F_pm + F_d_loc, mur_pm)
        psi_d = kw * Nph * sol_d.flux_wb
        # q-axis path: similar reluctance but without PM (cross-sat neglected)
        F_q = 1.5 * Nph * kw * iq_val / max(p, 1.0)
        branches_q = build_spm_branches(geo, mur_pm=mur_pm)
        # Short PM branch recoil still present; drive with F_q only on q path approx
        sol_q = solve_series_mec(branches_q, F_q)
        psi_q = kw * Nph * sol_q.flux_wb
        return psi_d, psi_q

    psi_d0, psi_q0 = psi_for_id_iq(id_, iq)
    psi_d1, _ = psi_for_id_iq(id_ + di, iq)
    _, psi_q1 = psi_for_id_iq(id_, iq + di)
    ld = (psi_d1 - psi_d0) / di
    lq = (psi_q1 - psi_q0) / di
    # Clamp non-physical negatives from coarse model
    ld = abs(ld)
    lq = abs(lq)

    # --- Losses ---
    i_rms = i_pk / math.sqrt(2.0)
    r_ph = _phase_resistance(geo, sigma)
    copper = 1.5 * i_rms**2 * r_ph

    f_hz = abs(n_rpm) * p / 60.0
    v_tooth, v_yoke = _iron_volume(geo)
    B_yoke_mean = 0.5 * (abs(B_sy) + abs(B_ry))
    iron = _steinmetz_iron_w(B_tooth, B_yoke_mean, v_tooth, v_yoke, f_hz)

    # Magnet eddy (very coarse ~ B_g^2 * f^2 * volume)
    v_pm = geo["A_pm_m2"] * geo["magnet_thickness_m"] * poles
    magnet_eddy = 0.02 * (B_g**2) * (f_hz**2) * v_pm

    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    result = {
        "schema_version": request.get("schema_version", "0.0.0-gate0"),
        "meta": {
            "solver": "mec",
            "elapsed_ms": round(elapsed_ms, 3),
            "mock": False,
            "note": _note_join(notes),
            "mec": {
                "converged": sol.converged,
                "iterations": sol.iterations,
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
    return result


def solve_radial_pmsm_mec_copy(request: dict[str, Any]) -> dict[str, Any]:
    """Same as solve_radial_pmsm_mec but does not mutate caller input."""
    return solve_radial_pmsm_mec(copy.deepcopy(request))
