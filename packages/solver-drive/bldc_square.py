"""BLDC six-step / square-wave current source — engineering model (Q4-1)."""

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


def _sector(theta_elec: float) -> int:
    """Electrical angle → six-step sector 0..5."""
    twopi = 2.0 * math.pi
    a = theta_elec % twopi
    return int(a // (math.pi / 3.0)) % 6


def _phase_currents(sector: int, i_mag: float) -> tuple[float, float, float]:
    """Classic six-step: two phases ±I, one open≈0."""
    table = (
        (i_mag, -i_mag, 0.0),
        (i_mag, 0.0, -i_mag),
        (0.0, i_mag, -i_mag),
        (-i_mag, i_mag, 0.0),
        (-i_mag, 0.0, i_mag),
        (0.0, -i_mag, i_mag),
    )
    return table[sector]


def solve_bldc_square(cfg: dict[str, Any]) -> dict[str, Any]:
    plant = merge_plant(cfg.get("plant") if isinstance(cfg.get("plant"), dict) else None)
    op = op_from_config(cfg)
    speed = float(op["speedRpm"] or 3000.0)
    p = max(1.0, float(plant["p"]))
    Rs = float(plant["Rs"])
    psi_f = float(plant["psi_f"])
    temp = float(op["tempC"] or 80.0)

    # Current magnitude: from iq/id peak request, torque request, or default
    i_mag: float
    if op.get("currentAPeak") is not None:
        i_mag = abs(float(op["currentAPeak"]))
    elif op.get("iqA") is not None:
        i_mag = abs(float(op["iqA"]))
    elif op.get("torqueNm") is not None and abs(psi_f) > 1e-12:
        # Te ≈ (3/2)*p*psi*Iq for SPM; square-wave uses ~1.0*p*psi*I (eng.)
        t_req = float(op["torqueNm"])
        i_mag = abs(t_req) / max(p * psi_f, 1e-12)
    else:
        i_mag = 10.0

    n_pts = int(cfg.get("nSamples") or cfg.get("n_samples") or 360)
    n_pts = max(36, min(n_pts, 3600))
    elec_period = 1.0 / max((speed / 60.0) * p, 1e-9)
    dt = elec_period / n_pts

    t_s: list[float] = []
    ia: list[float] = []
    ib: list[float] = []
    ic: list[float] = []
    torque: list[float] = []

    # Trapezoidal back-EMF × square current → torque ripple
    ke = p * psi_f  # V·s / elec rad ≈ Wb·p

    for i in range(n_pts):
        t = i * dt
        theta_e = 2.0 * math.pi * (t / elec_period)
        sec = _sector(theta_e)
        a, b, c = _phase_currents(sec, i_mag)
        # Idealized trapezoidal torque: flat in mid-sector, dips near commutation
        edge = (theta_e % (math.pi / 3.0)) / (math.pi / 3.0)
        trap = 1.0 - 0.15 * max(0.0, 1.0 - min(edge, 1.0 - edge) * 8.0)
        # Six-step effective: Te ≈ ke * I * trap (two phases conducting)
        te = ke * i_mag * trap
        t_s.append(t)
        ia.append(a)
        ib.append(b)
        ic.append(c)
        torque.append(te)

    t_avg = sum(torque) / len(torque)
    t_pp = max(torque) - min(torque)
    # Copper: two phases conducting → 2 * I^2 * Rs
    p_cu = 2.0 * (i_mag**2) * Rs
    omega = omega_mech(speed)
    p_mech = t_avg * omega
    # Iron / magnet eddy placeholders (speed-scaled)
    p_fe = 0.02 * abs(speed) * (psi_f**2) * 1000.0
    p_eddy = 0.005 * abs(speed) * (psi_f**2)
    p_elec = p_mech + p_cu + p_fe + p_eddy
    eta = (p_mech / p_elec) if p_elec > 1e-12 and p_mech > 0 else 0.0

    rms = i_mag * math.sqrt(2.0 / 3.0)  # rough phase RMS over six-step cycle

    result = {
        "mode": "bldc_square",
        "machineType": cfg.get("machineType") or cfg.get("machine_type") or "BLDC",
        "operatingPoint": {
            "speedRpm": speed,
            "torqueNm": t_avg,
            "tempC": temp,
        },
        "lossesW": empty_losses(
            copper=round(p_cu, 6),
            iron=round(p_fe, 6),
            magnetEddy=round(p_eddy, 6),
            bar=None,
            endRing=None,
        ),
        "currentsA": currents_a(rmsPhase=round(rms, 6), id=0.0, iq=round(i_mag, 6)),
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
            "iMagA": round(i_mag, 6),
        },
        # Internal aliases (kept for package tests / UI convenience)
        "losses": {
            "copper": round(p_cu, 6),
            "iron": round(p_fe, 6),
            "magnet_eddy": round(p_eddy, 6),
        },
        "meta": {
            "solver": "drive_bldc_square",
            "note": "Engineering six-step model — not an accuracy claim",
            "nSamples": n_pts,
            "elecPeriodS": elec_period,
        },
    }
    return result
