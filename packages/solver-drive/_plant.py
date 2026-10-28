"""Shared plant / operating-point helpers for drive models."""

from __future__ import annotations

import math
from typing import Any


DEFAULT_PLANT: dict[str, float] = {
    "Rs": 0.05,  # ohm phase
    "Ld": 1.0e-3,  # H
    "Lq": 1.2e-3,  # H
    "Lsigma": 2.0e-3,  # H (ACIM leakage aggregate)
    "Lm": 0.08,  # H magnetizing (ACIM)
    "Rr": 0.04,  # ohm rotor referred (ACIM)
    "psi_f": 0.08,  # Wb PM flux
    "p": 4.0,  # pole pairs
    "Vdc": 48.0,  # V DC bus
    "J": 1.0e-4,  # kg m^2 (unused in steady models)
}


def merge_plant(raw: dict[str, Any] | None) -> dict[str, float]:
    out = dict(DEFAULT_PLANT)
    if not raw:
        return out
    for k, v in raw.items():
        if v is None:
            continue
        try:
            out[str(k)] = float(v)
        except (TypeError, ValueError):
            continue
    return out


def op_from_config(cfg: dict[str, Any]) -> dict[str, float | None]:
    """Normalize operatingPoint to camelCase public fields."""
    op = cfg.get("operatingPoint") or cfg.get("operating_point") or {}
    if not isinstance(op, dict):
        op = {}

    def _get(*keys: str, default: float | None = None) -> float | None:
        for k in keys:
            if k in op and op[k] is not None:
                try:
                    return float(op[k])
                except (TypeError, ValueError):
                    return default
        return default

    speed = _get("speedRpm", "speed_rpm", "n_rpm", default=3000.0)
    torque = _get("torqueNm", "torque_nm", "T_nm", default=None)
    temp = _get("tempC", "temp_c", "temperature_c", default=80.0)
    i_peak = _get("currentAPeak", "current_a_peak", "i_peak", default=None)
    id_ref = _get("idA", "id_a", "id", default=None)
    iq_ref = _get("iqA", "iq_a", "iq", default=None)
    gamma = _get("gammaDeg", "gamma_deg", default=0.0)
    slip = _get("slip", "s", default=None)
    freq = _get("freqHz", "freq_hz", "f_hz", default=None)
    v_peak = _get("voltageVPeak", "voltage_v_peak", default=None)

    return {
        "speedRpm": speed if speed is not None else 3000.0,
        "torqueNm": torque,
        "tempC": temp if temp is not None else 80.0,
        "currentAPeak": i_peak,
        "idA": id_ref,
        "iqA": iq_ref,
        "gammaDeg": gamma if gamma is not None else 0.0,
        "slip": slip,
        "freqHz": freq,
        "voltageVPeak": v_peak,
    }


def empty_losses(
    *,
    copper: float | None = None,
    iron: float | None = None,
    magnetEddy: float | None = None,
    bar: float | None = None,
    endRing: float | None = None,
) -> dict[str, float | None]:
    return {
        "copper": copper,
        "iron": iron,
        "magnetEddy": magnetEddy,
        "bar": bar,
        "endRing": endRing,
    }


def currents_a(
    *,
    rmsPhase: float | None = None,
    id: float | None = None,
    iq: float | None = None,
) -> dict[str, float | None]:
    return {"rmsPhase": rmsPhase, "id": id, "iq": iq}


def omega_mech(speed_rpm: float) -> float:
    return speed_rpm * 2.0 * math.pi / 60.0


def downsample(series: list[float], max_n: int = 360) -> list[float]:
    if len(series) <= max_n:
        return series
    step = max(1, len(series) // max_n)
    return series[::step][:max_n]


def apply_pwm_deadtime(
    result: dict[str, Any],
    cfg: dict[str, Any],
) -> dict[str, Any]:
    """Optional PWM/dead-time engineering correction on an existing case result."""
    from pwm_deadtime import apply_corrections

    return apply_corrections(result, cfg)
