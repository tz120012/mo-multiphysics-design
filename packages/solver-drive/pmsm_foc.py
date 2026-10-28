"""PMSM dq FOC — steady current / sinusoidal phase currents (Q4-2)."""

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


def solve_pmsm_foc(cfg: dict[str, Any]) -> dict[str, Any]:
    plant = merge_plant(cfg.get("plant") if isinstance(cfg.get("plant"), dict) else None)
    op = op_from_config(cfg)
    speed = float(op["speedRpm"] or 3000.0)
    p = max(1.0, float(plant["p"]))
    Rs = float(plant["Rs"])
    Ld = float(plant["Ld"])
    Lq = float(plant["Lq"])
    psi_f = float(plant["psi_f"])
    temp = float(op["tempC"] or 80.0)
    gamma = math.radians(float(op["gammaDeg"] or 0.0))

    # Resolve id/iq
    if op.get("idA") is not None or op.get("iqA") is not None:
        id_a = float(op["idA"] if op.get("idA") is not None else 0.0)
        iq_a = float(op["iqA"] if op.get("iqA") is not None else 0.0)
    elif op.get("currentAPeak") is not None:
        i_pk = abs(float(op["currentAPeak"]))
        # peak phase ≈ |Is|; Is angle from gamma (MTPA-ish: id=Is*sinγ, iq=Is*cosγ)
        id_a = -i_pk * math.sin(gamma)
        iq_a = i_pk * math.cos(gamma)
    elif op.get("torqueNm") is not None:
        t_req = float(op["torqueNm"])
        # Neglect reluctance first; then one Newton step for (Ld-Lq) term
        iq_a = t_req / max(1.5 * p * psi_f, 1e-12)
        id_a = 0.0
        for _ in range(3):
            te = 1.5 * p * (psi_f * iq_a + (Ld - Lq) * id_a * iq_a)
            # simple: keep id=0, scale iq
            if abs(te) > 1e-12:
                iq_a *= t_req / te
            else:
                iq_a = t_req / max(1.5 * p * psi_f, 1e-12)
    else:
        id_a = 0.0
        iq_a = 10.0

    te = 1.5 * p * (psi_f * iq_a + (Ld - Lq) * id_a * iq_a)
    is_mag = math.hypot(id_a, iq_a)
    rms = is_mag / math.sqrt(2.0)

    n_pts = int(cfg.get("nSamples") or cfg.get("n_samples") or 360)
    n_pts = max(36, min(n_pts, 3600))
    elec_period = 1.0 / max((speed / 60.0) * p, 1e-9)
    dt = elec_period / n_pts
    # Phase angle of current vector in dq
    beta = math.atan2(iq_a, id_a) if is_mag > 1e-12 else 0.0

    t_s: list[float] = []
    ia: list[float] = []
    ib: list[float] = []
    ic: list[float] = []
    torque: list[float] = []

    # Mild cogging / slot ripple placeholder on torque
    for i in range(n_pts):
        t = i * dt
        theta_e = 2.0 * math.pi * (t / elec_period)
        # Inverse Park at theta_e (rotor) with current angle beta in dq
        # ia = Is * cos(theta_e + beta) with Is peak = is_mag
        ang = theta_e + beta
        a = is_mag * math.cos(ang)
        b = is_mag * math.cos(ang - 2.0 * math.pi / 3.0)
        c = is_mag * math.cos(ang + 2.0 * math.pi / 3.0)
        ripple = 1.0 + 0.03 * math.sin(6.0 * theta_e)
        t_s.append(t)
        ia.append(a)
        ib.append(b)
        ic.append(c)
        torque.append(te * ripple)

    t_avg = sum(torque) / len(torque)
    t_pp = max(torque) - min(torque)
    p_cu = 1.5 * (rms**2) * Rs * 2.0  # 3/2 * Is_peak^2 * Rs = 3 * Irms^2 * Rs
    # Use standard: Pcu = 3 * Irms^2 * Rs with Irms = Is/√2
    p_cu = 3.0 * (rms**2) * Rs
    omega = omega_mech(speed)
    p_mech = t_avg * omega
    p_fe = 0.015 * abs(speed) * (psi_f**2) * 1000.0
    p_eddy = 0.004 * abs(speed) * (psi_f**2) * (1.0 + 0.1 * is_mag)
    p_elec = p_mech + p_cu + p_fe + p_eddy
    eta = (p_mech / p_elec) if p_elec > 1e-12 and p_mech > 0 else 0.0

    return {
        "mode": "pmsm_foc",
        "machineType": cfg.get("machineType") or cfg.get("machine_type") or "PMSM",
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
            "ldH": Ld,
            "lqH": Lq,
            "psiFWb": psi_f,
        },
        "losses": {
            "copper": round(p_cu, 6),
            "iron": round(p_fe, 6),
            "magnet_eddy": round(p_eddy, 6),
        },
        "meta": {
            "solver": "drive_pmsm_foc",
            "note": "Engineering dq FOC steady model — not an accuracy claim",
            "nSamples": n_pts,
        },
    }
