"""PWM carrier / modulation + dead-time engineering corrections (Q4-4)."""

from __future__ import annotations

import math
from enum import Enum
from typing import Any


class PwmScheme(str, Enum):
    spwm = "spwm"
    svpwm = "svpwm"


def parse_pwm(cfg: dict[str, Any]) -> dict[str, Any]:
    pwm = cfg.get("pwm") if isinstance(cfg.get("pwm"), dict) else {}
    dead = cfg.get("deadTime") or cfg.get("dead_time") or {}
    if not isinstance(dead, dict):
        dead = {}
    scheme_raw = str(pwm.get("scheme") or pwm.get("modulation") or "svpwm").lower()
    try:
        scheme = PwmScheme(scheme_raw)
    except ValueError:
        scheme = PwmScheme.svpwm
    carrier = float(pwm.get("carrierHz") or pwm.get("carrier_hz") or 10000.0)
    mod = float(pwm.get("modIndex") or pwm.get("mod_index") or pwm.get("m") or 0.9)
    mod = max(0.0, min(mod, 1.15))
    tdead_us = float(
        dead.get("tdeadUs")
        or dead.get("tdead_us")
        or dead.get("deadTimeUs")
        or dead.get("us")
        or 0.0
    )
    return {
        "scheme": scheme.value,
        "carrierHz": carrier,
        "modIndex": mod,
        "tdeadUs": tdead_us,
    }


def apply_corrections(result: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    """Mutate-copy: dead time reduces avg torque & adds current distortion factor."""
    pwm = parse_pwm(cfg)
    out = dict(result)
    metrics = dict(out.get("metrics") or {})
    losses_w = dict(out.get("lossesW") or {})
    currents = dict(out.get("currentsA") or {})
    waveforms = dict(out.get("waveforms") or {})

    carrier = pwm["carrierHz"]
    tdead_s = pwm["tdeadUs"] * 1e-6
    # Dead-time distortion ~ 4*tdead*f_c * Vdc effect → current/torque derate
    dist = min(0.25, 4.0 * tdead_s * carrier) if carrier > 0 else 0.0
    # SVPWM slightly better DC utilization → milder torque loss vs SPWM
    scheme_factor = 0.85 if pwm["scheme"] == "svpwm" else 1.0
    torque_scale = max(0.5, 1.0 - dist * scheme_factor)
    # Modulation index below 1 reduces available voltage headroom (mild)
    m = pwm["modIndex"]
    if m < 1.0:
        torque_scale *= 0.95 + 0.05 * m

    t_avg = float(metrics.get("torqueAvgNm") or 0.0) * torque_scale
    t_pp = float(metrics.get("torqueRipplePpNm") or 0.0) * (1.0 + 0.5 * dist)
    metrics["torqueAvgNm"] = round(t_avg, 6)
    metrics["torqueRipplePpNm"] = round(t_pp, 6)
    metrics["deadTimeDistortion"] = round(dist, 6)
    metrics["pwm"] = pwm

    # Scale torque waveform
    if "torque_nm" in waveforms and isinstance(waveforms["torque_nm"], list):
        waveforms["torque_nm"] = [float(x) * torque_scale for x in waveforms["torque_nm"]]

    # Extra copper from distortion harmonics (placeholder)
    cu = losses_w.get("copper")
    if isinstance(cu, (int, float)):
        losses_w["copper"] = round(float(cu) * (1.0 + 0.5 * dist), 6)

    # Current THD-ish bump
    rms = currents.get("rmsPhase")
    if isinstance(rms, (int, float)):
        currents["rmsPhase"] = round(float(rms) * (1.0 + 0.2 * dist), 6)

    # Recompute efficiency if powers present
    p_mech = t_avg * (
        float((out.get("operatingPoint") or {}).get("speedRpm") or 0.0) * 2.0 * math.pi / 60.0
    )
    loss_sum = 0.0
    for k in ("copper", "iron", "magnetEddy", "bar", "endRing"):
        v = losses_w.get(k)
        if isinstance(v, (int, float)):
            loss_sum += float(v)
    p_elec = p_mech + loss_sum
    metrics["pMechW"] = round(p_mech, 6)
    metrics["pElecW"] = round(p_elec, 6)
    metrics["efficiency"] = round((p_mech / p_elec) if p_elec > 1e-12 and p_mech > 0 else 0.0, 6)

    op = dict(out.get("operatingPoint") or {})
    op["torqueNm"] = t_avg
    out["operatingPoint"] = op
    out["metrics"] = metrics
    out["lossesW"] = losses_w
    out["currentsA"] = currents
    out["waveforms"] = waveforms
    out["pwm"] = pwm

    # Keep losses alias in sync if present
    if "losses" in out:
        alias = dict(out["losses"])
        if losses_w.get("copper") is not None:
            alias["copper"] = losses_w["copper"]
        out["losses"] = alias

    meta = dict(out.get("meta") or {})
    meta["pwmApplied"] = True
    out["meta"] = meta
    return out
