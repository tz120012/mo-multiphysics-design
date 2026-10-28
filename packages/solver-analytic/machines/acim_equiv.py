"""ACIM single-cage steady-state equivalent circuit (Q2-3).

Classic T-model: Rs, Xσs, Xm, Xσr', Rr'.
Parameters estimated from GeometrySummary + materials (engineering first cut).
Not calibrated to ≤5%.
"""
from __future__ import annotations

import math
import time
from typing import Any

from materials_adapter import resolve_from_request

MU0 = 4.0 * math.pi * 1e-7


def _f(d: dict, key: str, default: float) -> float:
    v = d.get(key, default)
    if v is None:
        return float(default)
    return float(v)


def estimate_circuit_params(
    geometry: dict[str, Any],
    *,
    sigma_copper: float,
    sigma_bar: float,
    notes: list[str],
) -> dict[str, float]:
    """Derive Rs, Rr', Xm, Xσs, Xσr' (Ω, SI) from compact geometry."""
    poles = max(int(geometry["poles"]), 2)
    slots = max(int(geometry["slots"]), 3)
    L = float(geometry["stack_length_m"])
    g = float(geometry["airgap_m"])
    rod = float(geometry["rotor_od_m"])
    sid = float(geometry["stator_id_m"])
    p = poles / 2.0

    if "turns_per_phase" not in geometry or geometry["turns_per_phase"] is None:
        turns = 72
        notes.append("turns_per_phase defaulted to 72 (ACIM)")
    else:
        turns = max(int(geometry["turns_per_phase"]), 1)

    kw = _f(geometry, "winding_factor", 0.90)
    if "winding_factor" not in geometry:
        notes.append("winding_factor defaulted to 0.90 (ACIM)")

    kg = _f(geometry, "carter_factor", 1.2)
    if "carter_factor" not in geometry:
        notes.append("carter_factor defaulted to 1.2 (ACIM)")
    g_eff = g * kg

    # Mean airgap diameter / pole pitch
    D = 0.5 * (rod + sid)
    tau_p = math.pi * D / poles
    tau_s = math.pi * sid / slots

    # Magnetizing inductance (m-phase approx, m=3):
    # Lm ≈ (μ0 * m * (kw Nph)^2 * τp * L) / (π^2 * p * g_eff) * D/D  — use common form:
    # Xm = 2πf Lm; store Lm here, scale by f later.
    m_ph = 3.0
    Lm = (MU0 * m_ph * (kw * turns) ** 2 * tau_p * L) / (math.pi * p * g_eff)
    # Clamp to sane band for tiny demo geometries
    Lm = max(Lm, 1e-4)

    # Leakage: fractions of Lm (engineering)
    sigma_leak_s = _f(geometry, "leakage_frac_stator", 0.04)
    sigma_leak_r = _f(geometry, "leakage_frac_rotor", 0.05)
    if "leakage_frac_stator" not in geometry:
        notes.append("leakage_frac_stator defaulted to 0.04")
    if "leakage_frac_rotor" not in geometry:
        notes.append("leakage_frac_rotor defaulted to 0.05")
    Lσs = sigma_leak_s * Lm
    Lσr = sigma_leak_r * Lm

    # Stator resistance: MLT ≈ 2(L + 1.5 π τs)
    end = math.pi * tau_s * 1.5
    mlt = 2.0 * (L + end)
    # Conductor area guess from tooth pitch
    a_cond = max(1.0e-6, 0.12 * (0.45 * tau_s) * max(0.12 * sid, 0.01) / max(turns / max(slots / 3.0, 1.0), 1.0))
    if "conductor_area_m2" in geometry and geometry["conductor_area_m2"]:
        a_cond = float(geometry["conductor_area_m2"])
    else:
        notes.append(f"conductor_area_m2 estimated as {a_cond:.4g} m²")
    Rs = turns * mlt / (sigma_copper * a_cond)

    # Rotor bar: number of bars ≈ slots (single-cage approx) or explicit
    n_bars = int(geometry["rotor_bars"]) if geometry.get("rotor_bars") else slots
    if "rotor_bars" not in geometry:
        notes.append(f"rotor_bars defaulted to slots={n_bars}")

    if "bar_area_m2" in geometry and geometry["bar_area_m2"]:
        a_bar = float(geometry["bar_area_m2"])
    else:
        # Default bar section ~ few tens of mm² scaled with machine size
        a_bar = max(2.0e-5, 0.08 * tau_s * max(0.1 * sid, 0.008))
        notes.append(f"bar_area_m2 defaulted to {a_bar:.4g} m²")

    # Bar resistance (one bar), end-ring share crude factor 1.3
    R_bar = 1.3 * L / (sigma_bar * a_bar)
    # Refer to stator: a ≈ (kw * Nph * m / N_bars)^2 * (effective turns ratio)^2
    # Classic: Rr' = R_bar * (m / N_bars) * (kw * Nph)^2  (order-of-magnitude)
    turns_ratio_sq = (kw * turns) ** 2 * (m_ph / max(n_bars, 1))
    Rr_p = R_bar * turns_ratio_sq
    # Keep Rr' in a usable band vs Rs
    if Rr_p < 0.05 * Rs:
        Rr_p = 0.3 * Rs
        notes.append("Rr' floored to 0.3*Rs for numeric stability")
    if Rr_p > 5.0 * Rs:
        Rr_p = 2.0 * Rs
        notes.append("Rr' capped at 2*Rs for numeric stability")

    return {
        "poles": float(poles),
        "pole_pairs": p,
        "slots": float(slots),
        "stack_length_m": L,
        "airgap_m": g,
        "airgap_eff_m": g_eff,
        "rotor_od_m": rod,
        "stator_id_m": sid,
        "turns_per_phase": float(turns),
        "kw": kw,
        "Rs": Rs,
        "Rr_p": Rr_p,
        "Lm": Lm,
        "Lsigma_s": Lσs,
        "Lsigma_r": Lσr,
        "n_bars": float(n_bars),
        "a_bar_m2": a_bar,
        "D_ag_m": D,
        "tau_p_m": tau_p,
    }


def _series(z1: complex, z2: complex) -> complex:
    return z1 + z2


def _parallel(z1: complex, z2: complex) -> complex:
    denom = z1 + z2
    if abs(denom) < 1e-30:
        return complex(1e30, 0.0)
    return (z1 * z2) / denom


def solve_acim_steady(
    params: dict[str, float],
    *,
    f_hz: float,
    v_ph_peak: float,
    slip: float,
) -> dict[str, float]:
    """Single-cage T-model at given slip; V is phase peak → use RMS = peak/√2."""
    s = float(slip)
    if abs(s) < 1e-8:
        s = 1e-8  # avoid div0 at sync (no-load asymptote)
    omega = 2.0 * math.pi * abs(f_hz)
    Rs = params["Rs"]
    Rr = params["Rr_p"]
    Xs = omega * params["Lsigma_s"]
    Xr = omega * params["Lsigma_r"]
    Xm = omega * params["Lm"]

    # Neglect core-loss resistance in parallel for v0 (iron via Steinmetz later)
    Z1 = complex(Rs, Xs)
    Zm = complex(0.0, Xm)
    Z2 = complex(Rr / s, Xr)

    Zf = _parallel(Zm, Z2)
    Zin = _series(Z1, Zf)
    V_rms = abs(v_ph_peak) / math.sqrt(2.0)
    I1 = complex(V_rms, 0.0) / Zin

    # Current into rotor branch: I2 = I1 * Zm / (Zm + Z2)
    I2 = I1 * Zm / (Zm + Z2)
    Im = I1 * Z2 / (Zm + Z2)

    I1_rms = abs(I1)
    I2_rms = abs(I2)

    P_cu_s = 3.0 * I1_rms**2 * Rs
    P_cu_r = 3.0 * I2_rms**2 * Rr  # = 3 |I2|^2 Rr  (actual rotor copper; note Rr is referred)
    # Air-gap power
    P_ag = 3.0 * I2_rms**2 * (Rr / s)
    P_mech = (1.0 - s) * P_ag

    # Sync mechanical speed [rad/s]
    p = params["pole_pairs"]
    n_sync_rpm = abs(f_hz) * 60.0 / p if p > 0 else 0.0
    omega_sync = n_sync_rpm * 2.0 * math.pi / 60.0
    torque = P_ag / omega_sync if omega_sync > 1e-12 else 0.0

    # Power factor
    S = 3.0 * V_rms * I1_rms
    P_in = 3.0 * V_rms * I1_rms * math.cos(math.atan2(I1.imag, I1.real))
    # More accurately P_in = Re(3 V I1*)
    P_in = 3.0 * (V_rms * I1.real)  # V on real axis
    pf = (P_in / S) if S > 1e-18 else 0.0

    # Induced / airgap voltage rough: Em = |I_m| * Xm (or |V - I1 Z1|)
    E_ag = abs(I1 * Zf)  # voltage across magnetizing branch (RMS)
    E_ag_peak = E_ag * math.sqrt(2.0)

    return {
        "slip": s,
        "f_hz": float(f_hz),
        "torque_nm": float(torque),
        "I1_rms": float(I1_rms),
        "I2_rms": float(I2_rms),
        "Im_rms": float(abs(Im)),
        "P_cu_stator_w": float(P_cu_s),
        "P_cu_rotor_w": float(P_cu_r),
        "P_ag_w": float(P_ag),
        "P_mech_w": float(P_mech),
        "P_in_w": float(P_in),
        "pf": float(pf),
        "E_ag_v_peak": float(E_ag_peak),
        "Rs": Rs,
        "Rr_p": Rr,
        "Xm": Xm,
        "Xs": Xs,
        "Xr": Xr,
        "n_sync_rpm": float(n_sync_rpm),
    }


def _iron_loss_rough(params: dict[str, float], f_hz: float, E_ag_peak: float, kh: float, ke: float, alpha: float) -> float:
    """Very coarse iron loss from airgap voltage → B estimate × volume."""
    # B ~ E / (4.44 f kw Nph A) — use tooth+yoke volume ~ π D L * 0.3 * hy_guess
    D = params["D_ag_m"]
    L = params["stack_length_m"]
    turns = params["turns_per_phase"]
    kw = params["kw"]
    A = params["tau_p_m"] * L * 0.7
    denom = 4.44 * max(abs(f_hz), 1e-3) * kw * turns * max(A, 1e-8)
    B = (E_ag_peak / math.sqrt(2.0)) / denom
    B = min(abs(B), 1.8)
    V_iron = math.pi * D * L * max(0.15 * D, 0.01)  # crude annulus
    p = kh * abs(f_hz) * (B**alpha) + ke * (f_hz * B) ** 2
    return float(max(p * V_iron, 0.0))


def solve_radial_acim_equiv(request: dict[str, Any]) -> dict[str, Any]:
    """SolveRequest-like → SolveResult-like for RF + ACIM.

    ``meta.solver='acim_equiv'``, ``meta.mock=false``.
    Requires ``operating_point.voltage_v_peak`` (phase) or ``current_a_peak`` (then
    solves with estimated Z at given/computed slip — voltage preferred).
    """
    t0 = time.perf_counter()
    notes: list[str] = []

    if request.get("topology") != "RF":
        raise ValueError("acim_equiv only supports topology=RF")
    if request.get("machine_type") != "ACIM":
        raise ValueError("acim_equiv requires machine_type=ACIM")

    g_in = request.get("geometry") or {}
    op = request.get("operating_point") or {}
    mat = resolve_from_request(request, need_magnet=False, need_bar=True)
    notes.extend(mat.notes)

    params = estimate_circuit_params(
        g_in,
        sigma_copper=mat.sigma_copper,
        sigma_bar=mat.sigma_bar,
        notes=notes,
    )
    p = params["pole_pairs"]

    n_rpm = float(op.get("speed_rpm", 0.0))
    # Supply frequency + slip
    if op.get("freq_hz") is not None:
        f_hz = float(op["freq_hz"])
    elif op.get("slip") is not None and abs(1.0 - float(op["slip"])) > 1e-6 and abs(n_rpm) > 1e-6:
        s0 = float(op["slip"])
        f_hz = abs(n_rpm) * p / (60.0 * (1.0 - s0))
        notes.append(f"freq_hz derived from speed and slip → {f_hz:.4g} Hz")
    else:
        f_hz = 50.0
        notes.append("freq_hz defaulted to 50 Hz")

    n_sync = abs(f_hz) * 60.0 / max(p, 1e-12)
    if op.get("slip") is not None:
        slip = float(op["slip"])
    else:
        slip = 1.0 if n_sync < 1e-9 else (n_sync - n_rpm) / n_sync
        notes.append(f"slip computed as (n_sync-n)/n_sync = {slip:.6g}")

    # Voltage: prefer voltage_v_peak (phase); else invent from current * |Zin| at slip (iter-free one-shot)
    if op.get("voltage_v_peak") is not None:
        v_peak = float(op["voltage_v_peak"])
    elif op.get("current_a_peak") is not None:
        # One-shot: build Zin at slip, V = I * |Zin| (peak)
        i_pk = float(op["current_a_peak"])
        omega = 2.0 * math.pi * abs(f_hz)
        Z1 = complex(params["Rs"], omega * params["Lsigma_s"])
        Zm = complex(0.0, omega * params["Lm"])
        s_u = slip if abs(slip) > 1e-8 else 1e-8
        Z2 = complex(params["Rr_p"] / s_u, omega * params["Lsigma_r"])
        Zin = Z1 + _parallel(Zm, Z2)
        v_peak = (i_pk / math.sqrt(2.0)) * abs(Zin) * math.sqrt(2.0)
        notes.append(f"voltage_v_peak inferred from current_a_peak via |Zin| → {v_peak:.4g} V")
    else:
        raise ValueError(
            "ACIM solve needs operating_point.voltage_v_peak (preferred) "
            "or current_a_peak"
        )

    circ = solve_acim_steady(params, f_hz=f_hz, v_ph_peak=v_peak, slip=slip)
    iron = _iron_loss_rough(
        params,
        f_hz,
        circ["E_ag_v_peak"],
        mat.steel_kh,
        mat.steel_ke,
        mat.steel_alpha,
    )

    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    note = (
        "ACIM single-cage steady equivalent circuit v0 (Rs/Rr'/Xm/Xσ from geometry+materials). "
        "Engineering first cut — not calibrated to ≤5%."
    )
    if notes:
        note = note + " Defaults: " + "; ".join(notes)

    return {
        "schema_version": request.get("schema_version", "0.0.0-gate0"),
        "meta": {
            "solver": "acim_equiv",
            "elapsed_ms": round(elapsed_ms, 3),
            "mock": False,
            "note": note,
            "acim": {
                "slip": circ["slip"],
                "freq_hz": circ["f_hz"],
                "n_sync_rpm": circ["n_sync_rpm"],
                "I1_rms": circ["I1_rms"],
                "I2_rms": circ["I2_rms"],
                "pf": circ["pf"],
                "P_in_w": circ["P_in_w"],
                "P_mech_w": circ["P_mech_w"],
                "Rs": circ["Rs"],
                "Rr_p": circ["Rr_p"],
                "Xm": circ["Xm"],
                "Xsigma_s": circ["Xs"],
                "Xsigma_r": circ["Xr"],
            },
            "materials_sources": mat.sources,
        },
        "torque_nm": float(circ["torque_nm"]),
        # Map airgap/induced voltage into back_emf_v_peak slot (documented in note)
        "back_emf_v_peak": float(circ["E_ag_v_peak"]),
        "losses_w": {
            "copper": float(circ["P_cu_stator_w"]),
            "iron": float(iron),
            "rotor_bar": float(circ["P_cu_rotor_w"]),
        },
    }
