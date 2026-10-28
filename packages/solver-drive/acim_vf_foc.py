"""ACIM V/f steady point + induction FOC (rotor-flux oriented, simplified) — Q4-3."""

from __future__ import annotations

import math
from typing import Any

from _plant import (
    currents_a,
    downsample,
    empty_losses,
    merge_plant,
    op_from_config,
    omega_mech,
)


def _acim_params(plant: dict[str, float]) -> dict[str, float]:
    Rs = float(plant["Rs"])
    Rr = float(plant.get("Rr", 0.04))
    Lm = float(plant.get("Lm", 0.08))
    Lsig = float(plant.get("Lsigma", 2e-3))
    # Split leakage roughly stator/rotor
    Lls = Lsig * 0.5
    Llr = Lsig * 0.5
    Ls = Lm + Lls
    Lr = Lm + Llr
    return {"Rs": Rs, "Rr": Rr, "Lm": Lm, "Ls": Ls, "Lr": Lr, "Lls": Lls, "Llr": Llr}


def solve_acim_vf(cfg: dict[str, Any]) -> dict[str, Any]:
    """Open-loop V/f steady operating point."""
    plant = merge_plant(cfg.get("plant") if isinstance(cfg.get("plant"), dict) else None)
    op = op_from_config(cfg)
    p = max(1.0, float(plant["p"]))
    Vdc = float(plant["Vdc"])
    pars = _acim_params(plant)
    temp = float(op["tempC"] or 80.0)

    speed = float(op["speedRpm"] or 1500.0)
    # Rated-ish sync frequency from speed + slip
    slip = float(op["slip"]) if op.get("slip") is not None else 0.03
    if op.get("freqHz") is not None:
        f_hz = float(op["freqHz"])
    else:
        # n_sync = 120*f / (2p) → f = n_sync * p / 60; n_mech = n_sync*(1-s)
        n_sync = speed / max(1.0 - slip, 1e-6)
        f_hz = n_sync * p / 60.0

    # V/f: Vpeak ≈ (Vdc/√3)*m with m ~ f/f_base (clip)
    f_base = float(cfg.get("fBaseHz") or cfg.get("f_base_hz") or 50.0)
    m = min(1.0, abs(f_hz) / max(f_base, 1.0))
    if op.get("voltageVPeak") is not None:
        v_peak = float(op["voltageVPeak"])
    else:
        v_peak = (Vdc / math.sqrt(3.0)) * m

    omega_e = 2.0 * math.pi * f_hz
    omega_s = omega_e  # electrical rad/s (stator)
    omega_r = omega_s * (1.0 - slip)  # rotor electrical
    omega_m = omega_r / p

    # Steady equivalent-circuit phasor (approx)
    Xm = omega_s * pars["Lm"] if abs(omega_s) > 1e-9 else 1e9
    Xls = omega_s * pars["Lls"]
    Xlr = omega_s * pars["Llr"]
    Rr = pars["Rr"]
    Rs = pars["Rs"]
    # Thevenin-ish rotor branch
    Zr_num = Rr / max(slip, 1e-4)
    Z_rotor = complex(Zr_num, Xlr)
    Z_mag = 1.0 / (1.0 / complex(0, Xm) + 1.0 / Z_rotor) if abs(Xm) > 1e-12 else Z_rotor
    Z_tot = complex(Rs, Xls) + Z_mag
    Vph = complex(v_peak / math.sqrt(2.0), 0.0)  # RMS phasor
    I1 = Vph / Z_tot if abs(Z_tot) > 1e-18 else complex(0)
    E = I1 * Z_mag
    I2 = E / Z_rotor if abs(Z_rotor) > 1e-18 else complex(0)
    i_rms = abs(I1)
    i_bar_rms = abs(I2)

    # Torque ≈ (3*p/ωs) * |I2|^2 * Rr/s
    if abs(omega_s) > 1e-9 and abs(slip) > 1e-8:
        te = (3.0 * p / omega_s) * (i_bar_rms**2) * (Rr / slip)
    else:
        te = 0.0
    if op.get("torqueNm") is not None:
        # Scale current to hit torque request (engineering)
        t_req = float(op["torqueNm"])
        if abs(te) > 1e-9:
            scale = t_req / te
            i_rms *= abs(scale) ** 0.5
            i_bar_rms *= abs(scale) ** 0.5
            te = t_req

    p_cu = 3.0 * (i_rms**2) * Rs
    p_bar = 3.0 * (i_bar_rms**2) * Rr  # rotor copper (bars placeholder)
    p_end = 0.15 * p_bar  # end-ring placeholder fraction
    p_fe = 0.02 * abs(f_hz) * (v_peak**2) * 0.01
    omega = omega_mech(speed)
    p_mech = te * omega
    p_elec = p_mech + p_cu + p_fe + p_bar + p_end
    eta = (p_mech / p_elec) if p_elec > 1e-12 and p_mech > 0 else 0.0

    # Waveforms: sinusoidal at stator freq
    n_pts = int(cfg.get("nSamples") or 360)
    n_pts = max(36, min(n_pts, 3600))
    period = 1.0 / max(abs(f_hz), 1e-9)
    dt = period / n_pts
    i_peak = i_rms * math.sqrt(2.0)
    t_s, ia, ib, ic, torque = [], [], [], [], []
    for i in range(n_pts):
        t = i * dt
        ang = 2.0 * math.pi * f_hz * t
        t_s.append(t)
        ia.append(i_peak * math.cos(ang))
        ib.append(i_peak * math.cos(ang - 2.0 * math.pi / 3.0))
        ic.append(i_peak * math.cos(ang + 2.0 * math.pi / 3.0))
        torque.append(te * (1.0 + 0.02 * math.sin(2.0 * ang)))

    t_avg = sum(torque) / len(torque)
    t_pp = max(torque) - min(torque)

    return {
        "mode": "acim_vf",
        "machineType": cfg.get("machineType") or "ACIM",
        "operatingPoint": {
            "speedRpm": speed,
            "torqueNm": t_avg,
            "tempC": temp,
            "slip": slip,
            "freqHz": f_hz,
        },
        "lossesW": empty_losses(
            copper=round(p_cu, 6),
            iron=round(p_fe, 6),
            magnetEddy=None,
            bar=round(p_bar, 6),
            endRing=round(p_end, 6),
        ),
        "currentsA": currents_a(rmsPhase=round(i_rms, 6), id=None, iq=None),
        "waveforms": {
            "t_s": downsample(t_s),
            "ia": downsample(ia),
            "ib": downsample(ib),
            "ic": downsample(ic),
            "torque_nm": downsample(torque),
        },
        "metrics": {
            "torqueAvgNm": round(t_avg, 6),
            "torqueRipplePpNm": round(t_pp, 6),
            "pMechW": round(p_mech, 6),
            "pElecW": round(p_elec, 6),
            "efficiency": round(eta, 6),
            "slip": slip,
            "freqHz": f_hz,
            "vPeak": v_peak,
            "modIndex": m,
        },
        "losses": {
            "copper": round(p_cu, 6),
            "iron": round(p_fe, 6),
            "bar": round(p_bar, 6),
            "end_ring": round(p_end, 6),
        },
        "meta": {
            "solver": "drive_acim_vf",
            "note": "Engineering V/f steady model — not an accuracy claim",
        },
    }


def solve_acim_foc(cfg: dict[str, Any]) -> dict[str, Any]:
    """Rotor-flux-oriented induction FOC (simplified steady)."""
    plant = merge_plant(cfg.get("plant") if isinstance(cfg.get("plant"), dict) else None)
    op = op_from_config(cfg)
    p = max(1.0, float(plant["p"]))
    pars = _acim_params(plant)
    temp = float(op["tempC"] or 80.0)
    speed = float(op["speedRpm"] or 1500.0)
    omega_m = omega_mech(speed)
    omega_r = omega_m * p  # rotor electrical

    # Flux command / ids
    psi_r = float(cfg.get("psiRWb") or cfg.get("psi_r_wb") or (pars["Lm"] * 5.0))
    # ids ≈ psi_r / Lm
    id_a = psi_r / max(pars["Lm"], 1e-9)
    if op.get("idA") is not None:
        id_a = float(op["idA"])
        psi_r = id_a * pars["Lm"]

    # Torque → iq: Te = (3/2)*p*(Lm/Lr)*psi_r*iq
    k_t = 1.5 * p * (pars["Lm"] / max(pars["Lr"], 1e-12)) * psi_r
    if op.get("iqA") is not None:
        iq_a = float(op["iqA"])
    elif op.get("torqueNm") is not None:
        iq_a = float(op["torqueNm"]) / max(k_t, 1e-12)
    elif op.get("currentAPeak") is not None:
        # remaining current for iq after id
        i_pk = abs(float(op["currentAPeak"]))
        iq_a = math.sqrt(max(i_pk**2 - id_a**2, 0.0))
    else:
        iq_a = 8.0

    te = k_t * iq_a
    # Slip frequency ω_sl = (Rr/Lr) * (iq/id)
    omega_sl = (pars["Rr"] / max(pars["Lr"], 1e-12)) * (iq_a / max(id_a, 1e-9))
    omega_e = omega_r + omega_sl
    f_hz = omega_e / (2.0 * math.pi)
    slip = omega_sl / max(omega_e, 1e-9)

    is_mag = math.hypot(id_a, iq_a)
    rms = is_mag / math.sqrt(2.0)
    Rs = pars["Rs"]
    p_cu = 3.0 * (rms**2) * Rs
    # Rotor: approx 3*(iq related) — use referred
    i_r = abs(iq_a) * (pars["Lm"] / max(pars["Lr"], 1e-12))
    p_bar = 3.0 * (i_r**2) * pars["Rr"]
    p_end = 0.15 * p_bar
    p_fe = 0.015 * abs(f_hz) * (psi_r**2) * 100.0
    p_mech = te * omega_m
    p_elec = p_mech + p_cu + p_fe + p_bar + p_end
    eta = (p_mech / p_elec) if p_elec > 1e-12 and p_mech > 0 else 0.0

    n_pts = int(cfg.get("nSamples") or 360)
    n_pts = max(36, min(n_pts, 3600))
    period = 1.0 / max(abs(f_hz), 1e-9)
    dt = period / n_pts
    beta = math.atan2(iq_a, id_a)
    t_s, ia, ib, ic, torque = [], [], [], [], []
    for i in range(n_pts):
        t = i * dt
        theta_e = 2.0 * math.pi * f_hz * t
        ang = theta_e + beta
        t_s.append(t)
        ia.append(is_mag * math.cos(ang))
        ib.append(is_mag * math.cos(ang - 2.0 * math.pi / 3.0))
        ic.append(is_mag * math.cos(ang + 2.0 * math.pi / 3.0))
        torque.append(te * (1.0 + 0.015 * math.sin(6.0 * theta_e)))

    t_avg = sum(torque) / len(torque)
    t_pp = max(torque) - min(torque)

    return {
        "mode": "acim_foc",
        "machineType": cfg.get("machineType") or "ACIM",
        "operatingPoint": {
            "speedRpm": speed,
            "torqueNm": t_avg,
            "tempC": temp,
            "slip": slip,
            "freqHz": f_hz,
        },
        "lossesW": empty_losses(
            copper=round(p_cu, 6),
            iron=round(p_fe, 6),
            magnetEddy=None,
            bar=round(p_bar, 6),
            endRing=round(p_end, 6),
        ),
        "currentsA": currents_a(
            rmsPhase=round(rms, 6),
            id=round(id_a, 6),
            iq=round(iq_a, 6),
        ),
        "waveforms": {
            "t_s": downsample(t_s),
            "ia": downsample(ia),
            "ib": downsample(ib),
            "ic": downsample(ic),
            "torque_nm": downsample(torque),
        },
        "metrics": {
            "torqueAvgNm": round(t_avg, 6),
            "torqueRipplePpNm": round(t_pp, 6),
            "pMechW": round(p_mech, 6),
            "pElecW": round(p_elec, 6),
            "efficiency": round(eta, 6),
            "slip": slip,
            "freqHz": f_hz,
            "psiRWb": psi_r,
            "omegaSlRad": omega_sl,
        },
        "losses": {
            "copper": round(p_cu, 6),
            "iron": round(p_fe, 6),
            "bar": round(p_bar, 6),
            "end_ring": round(p_end, 6),
        },
        "meta": {
            "solver": "drive_acim_foc",
            "note": "Engineering rotor-flux FOC — not an accuracy claim",
        },
    }
