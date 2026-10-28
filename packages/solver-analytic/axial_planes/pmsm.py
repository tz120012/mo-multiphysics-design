"""AF + PMSM axial multi-plane unfold → SolveResult-compatible dict."""
from __future__ import annotations

import copy
import math
import time
from typing import Any

from materials_adapter import resolve_from_request
from radial_mec.materials import pm_hc
from radial_mec.network import MEC_MAX_ITER, MEC_TOL, build_spm_branches, solve_series_mec

from .geometry import derive_plane_geometry, plane_to_mec_geo

_L_DI_FRAC = 0.05
_L_DI_MIN = 0.1


def _note_join(notes: list[str]) -> str:
    base = (
        "AF PMSM axial multi-plane unfold v0 (concentric rings + series MEC per plane, "
        "analytic steel μ(B)). Engineering first cut — not calibrated to ≤5%; "
        "pending_calibration for golden benchmarks."
    )
    if notes:
        return base + " Defaults: " + "; ".join(notes)
    return base


def _phase_resistance(common: dict[str, float], planes: list[dict[str, float]], sigma: float) -> float:
    """Crude phase R from mean turn length on mean annulus radius."""
    r_m = common["r_mean_annulus_m"]
    disk_t = common["disk_thickness_m"]
    # End-turn ≈ 1.5 × mean pole pitch; active ≈ 2 × radial span (go+return radial)
    radial_span = common["outer_radius_m"] - common["inner_radius_m"]
    tau_p = 2.0 * math.pi * r_m / common["poles"]
    mlt = 2.0 * radial_span + 1.5 * math.pi * tau_p + 2.0 * disk_t
    turns = common["turns_per_phase"]
    # Conductor area guess from mid-plane tooth area
    mid = planes[len(planes) // 2]
    a_cond = max(
        1.5e-6,
        0.12 * mid["A_tooth_m2"] / max(turns / mid["n_teeth_per_pole"], 1.0),
    )
    return turns * mlt / (sigma * a_cond)


def _iron_volumes(planes: list[dict[str, float]], poles: float) -> tuple[float, float]:
    v_tooth = 0.0
    v_yoke = 0.0
    for pl in planes:
        v_tooth += pl["A_tooth_m2"] * pl["L_tooth_m"] * poles
        v_yoke += pl["A_sy_m2"] * pl["L_sy_m"] * poles
        v_yoke += pl["A_ry_m2"] * pl["L_ry_m"] * poles
    return v_tooth, v_yoke


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
    def p(B: float) -> float:
        b = abs(B)
        return kh * abs(f_hz) * (b**alpha) + ke * (f_hz * b) ** 2

    return p(B_tooth) * max(v_tooth, 0.0) + p(B_yoke) * max(v_yoke, 0.0)


def _solve_planes_flux(
    planes: list[dict[str, float]],
    mmf_a: float,
    mur_pm: float,
) -> tuple[list[Any], float]:
    """Solve each plane MEC independently; return (solutions, sum Φ)."""
    sols = []
    phi_sum = 0.0
    for pl in planes:
        geo = plane_to_mec_geo(pl)
        branches = build_spm_branches(geo, mur_pm=mur_pm)
        sol = solve_series_mec(branches, mmf_a, tol=MEC_TOL, max_iter=MEC_MAX_ITER)
        sols.append(sol)
        phi_sum += sol.flux_wb
    return sols, phi_sum


def solve_axial_pmsm_planes(request: dict[str, Any]) -> dict[str, Any]:
    """Public entry: AF+PMSM SolveRequest → SolveResult.

    ``meta.solver='axial_planes'``, ``meta.mock=false``. Deterministic (no RNG).
    """
    t0 = time.perf_counter()
    notes: list[str] = []

    if request.get("topology") != "AF":
        raise ValueError("axial_planes only supports topology=AF")
    if request.get("machine_type") != "PMSM":
        raise ValueError(
            f"axial_planes MVP is AF+PMSM only; got machine_type={request.get('machine_type')!r} "
            "(AF+BLDC / AF+ACIM not implemented yet)"
        )

    g_in = request.get("geometry") or {}
    op = request.get("operating_point") or {}

    common, planes = derive_plane_geometry(g_in, notes)
    mat = resolve_from_request(request, need_magnet=True, need_bar=False)
    notes.extend(mat.notes)

    br = mat.br_t
    mur_pm = mat.mur_pm
    sigma = mat.sigma_copper

    n_rpm = float(op.get("speed_rpm", 0.0))
    i_pk = float(op.get("current_a_peak", 0.0))
    gamma = math.radians(float(op.get("gamma_deg", 0.0)))
    iq = i_pk * math.cos(gamma)
    id_ = -i_pk * math.sin(gamma)

    poles = common["poles"]
    p = common["pole_pairs"]
    kw = common["kw"]
    Nph = common["turns_per_phase"]
    n_pl = int(common["n_planes"])

    F_pm = pm_hc(br, mur_pm) * common["magnet_thickness_m"]
    F_d = 1.5 * Nph * kw * id_ / max(p, 1.0)
    F_net = F_pm + F_d

    sols, phi_sum = _solve_planes_flux(planes, F_net, mur_pm)
    psi_pm = kw * Nph * abs(phi_sum)

    # Area-weighted mean B for losses / meta
    a_tot = sum(pl["A_g_m2"] for pl in planes) or 1e-18
    B_g_mean = sum(sols[i].branches["airgap"].B * planes[i]["A_g_m2"] for i in range(n_pl)) / a_tot
    B_tooth_mean = (
        sum(sols[i].branches["stator_tooth"].B * planes[i]["A_tooth_m2"] for i in range(n_pl))
        / (sum(pl["A_tooth_m2"] for pl in planes) or 1e-18)
    )
    B_sy_mean = (
        sum(sols[i].branches["stator_yoke"].B * planes[i]["A_sy_m2"] for i in range(n_pl))
        / (sum(pl["A_sy_m2"] for pl in planes) or 1e-18)
    )
    B_ry_mean = (
        sum(sols[i].branches["rotor_yoke"].B * planes[i]["A_ry_m2"] for i in range(n_pl))
        / (sum(pl["A_ry_m2"] for pl in planes) or 1e-18)
    )

    omega_m = n_rpm * 2.0 * math.pi / 60.0
    omega_e = p * omega_m
    back_emf = omega_e * psi_pm
    torque = 1.5 * p * psi_pm * iq

    # Optional multi-disk scale (meta only default 1)
    disk_count = max(int(common["disk_count"]), 1)
    if disk_count > 1:
        # Crude: more airgaps in RFMR/FRMF ≈ more torque path; scale flux linkage
        # Keep conservative: note only unless geometry says airgap_count
        notes.append(
            f"disk_count={disk_count} recorded; torque uses single-airgap equivalent "
            "(multi-disk series/parallel not expanded)"
        )

    di = max(_L_DI_FRAC * max(abs(i_pk), 1.0), _L_DI_MIN)

    def psi_for_id_iq(id_val: float, iq_val: float) -> tuple[float, float]:
        F_d_loc = 1.5 * Nph * kw * id_val / max(p, 1.0)
        _, phi_d = _solve_planes_flux(planes, F_pm + F_d_loc, mur_pm)
        psi_d = kw * Nph * phi_d
        F_q = 1.5 * Nph * kw * iq_val / max(p, 1.0)
        _, phi_q = _solve_planes_flux(planes, F_q, mur_pm)
        psi_q = kw * Nph * phi_q
        return psi_d, psi_q

    psi_d0, psi_q0 = psi_for_id_iq(id_, iq)
    psi_d1, _ = psi_for_id_iq(id_ + di, iq)
    _, psi_q1 = psi_for_id_iq(id_, iq + di)
    ld = abs((psi_d1 - psi_d0) / di)
    lq = abs((psi_q1 - psi_q0) / di)

    i_rms = i_pk / math.sqrt(2.0)
    r_ph = _phase_resistance(common, planes, sigma)
    copper = 1.5 * i_rms**2 * r_ph

    f_hz = abs(n_rpm) * p / 60.0
    v_tooth, v_yoke = _iron_volumes(planes, poles)
    B_yoke_mean = 0.5 * (abs(B_sy_mean) + abs(B_ry_mean))
    iron = _steinmetz_iron_w(
        B_tooth_mean,
        B_yoke_mean,
        v_tooth,
        v_yoke,
        f_hz,
        kh=mat.steel_kh,
        alpha=mat.steel_alpha,
        ke=mat.steel_ke,
    )

    v_pm = sum(pl["A_pm_m2"] * pl["magnet_thickness_m"] for pl in planes) * poles
    magnet_eddy = 0.02 * (B_g_mean**2) * (f_hz**2) * v_pm

    plane_meta = []
    all_converged = True
    max_iters = 0
    for i, (pl, sol) in enumerate(zip(planes, sols)):
        all_converged = all_converged and sol.converged
        max_iters = max(max_iters, sol.iterations)
        plane_meta.append(
            {
                "index": i,
                "r_mean_m": pl["r_mean_m"],
                "dr_m": pl["dr_m"],
                "flux_pole_wb": sol.flux_wb,
                "B_airgap_t": sol.branches["airgap"].B,
                "converged": sol.converged,
                "iterations": sol.iterations,
            }
        )

    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    return {
        "schema_version": request.get("schema_version", "0.0.0-gate0"),
        "meta": {
            "solver": "axial_planes",
            "elapsed_ms": round(elapsed_ms, 3),
            "mock": False,
            "n_planes": n_pl,
            "note": _note_join(notes),
            "axial": {
                "inner_radius_m": common["inner_radius_m"],
                "outer_radius_m": common["outer_radius_m"],
                "disk_thickness_m": common["disk_thickness_m"],
                "disk_count": disk_count,
                "flux_pole_sum_wb": phi_sum,
                "B_airgap_mean_t": B_g_mean,
                "B_tooth_mean_t": B_tooth_mean,
                "B_stator_yoke_mean_t": B_sy_mean,
                "B_rotor_yoke_mean_t": B_ry_mean,
                "F_pm_a": F_pm,
                "F_net_a": F_net,
                "psi_pm_wb": psi_pm,
                "converged": all_converged,
                "max_iterations": max_iters,
                "tol": MEC_TOL,
                "planes": plane_meta,
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


def solve_axial_pmsm_planes_copy(request: dict[str, Any]) -> dict[str, Any]:
    return solve_axial_pmsm_planes(copy.deepcopy(request))
