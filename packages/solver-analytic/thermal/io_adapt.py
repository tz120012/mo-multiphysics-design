"""Normalize drive / FEM / analytic loss & OP payloads to FEM-locked keys (tip 864ec20).

Canonical lossesW: total, iron, copper, pmEddy, rotorBar, endRing
Drive aliases: bar→rotorBar, magnetEddy→pmEddy; speedRpm→rpm
"""
from __future__ import annotations

from typing import Any

CANON_LOSS_KEYS = ("total", "iron", "copper", "pmEddy", "rotorBar", "endRing")

# drive / legacy → canonical
_LOSS_ALIASES = {
    "bar": "rotorBar",
    "rotor_bar": "rotorBar",
    "magnetEddy": "pmEddy",
    "magnet_eddy": "pmEddy",
    "pm_eddy": "pmEddy",
    "end_ring": "endRing",
    "endring": "endRing",
}


def _num(v: Any) -> float | None:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def normalize_losses_w(raw: Any) -> dict[str, float | None]:
    """Return canonical lossesW dict (all keys present; missing → None)."""
    out: dict[str, float | None] = {k: None for k in CANON_LOSS_KEYS}
    if not isinstance(raw, dict):
        return out
    for k, v in raw.items():
        key = str(k)
        canon = _LOSS_ALIASES.get(key, key)
        if canon in out:
            out[canon] = _num(v)
    # fill total if absent but parts present
    if out["total"] is None:
        parts = [out[k] for k in ("iron", "copper", "pmEddy", "rotorBar", "endRing") if out[k] is not None]
        if parts:
            out["total"] = sum(parts)
    return out


def normalize_operating_point(raw: Any) -> dict[str, float | None]:
    """Canonical operatingPoint: rpm, torqueNm, T_ambientC (+ passthrough extras)."""
    op: dict[str, float | None] = {"rpm": None, "torqueNm": None, "T_ambientC": None}
    if not isinstance(raw, dict):
        return op
    rpm = raw.get("rpm", raw.get("speedRpm", raw.get("speed_rpm")))
    tq = raw.get("torqueNm", raw.get("torque_nm"))
    tamb = raw.get("T_ambientC", raw.get("t_ambient_c", raw.get("ambient_c")))
    op["rpm"] = _num(rpm)
    op["torqueNm"] = _num(tq)
    op["T_ambientC"] = _num(tamb)
    # magnet/winding temp hypothesis (demag) — not ambient
    temp_c = raw.get("tempC", raw.get("temp_c", raw.get("temperature_c")))
    if _num(temp_c) is not None:
        op["tempC"] = _num(temp_c)
    for extra in ("idA", "iqA", "id_a", "iq_a"):
        if extra in raw and _num(raw[extra]) is not None:
            op[extra] = _num(raw[extra])
    return op


def resolve_source(payload: dict[str, Any], *, default: str = "analytic") -> str:
    s = payload.get("source")
    if isinstance(s, str) and s.strip().lower() in ("fem", "analytic", "drive"):
        return s.strip().lower()
    lb = payload.get("lossBreakdown")
    if isinstance(lb, dict):
        ls = lb.get("source")
        if isinstance(ls, str) and ls.strip().lower() in ("fem", "analytic", "drive"):
            return ls.strip().lower()
    return default


def machine_type_of(payload: dict[str, Any]) -> str | None:
    mt = payload.get("machineType", payload.get("machine_type"))
    return str(mt) if mt is not None else None


def adapt_thermal_request(payload: dict[str, Any]) -> dict[str, Any]:
    """Flatten a mixed drive/FEM/analytic request into a normalized dict."""
    losses_raw = payload.get("lossesW", payload.get("losses_w"))
    # also accept nested under electromagnetic / drive
    if losses_raw is None and isinstance(payload.get("drive"), dict):
        losses_raw = payload["drive"].get("lossesW")
    op_raw = payload.get("operatingPoint", payload.get("operating_point"))
    adapted = {
        "lossesW": normalize_losses_w(losses_raw),
        "lossBreakdown": payload.get("lossBreakdown") if isinstance(payload.get("lossBreakdown"), dict) else None,
        "operatingPoint": normalize_operating_point(op_raw if op_raw is not None else {}),
        "source": resolve_source(payload),
        "jobId": payload.get("jobId", payload.get("job_id")),
        "resultRef": payload.get("resultRef", payload.get("result_ref")),
        "pending_calibration": True,
        "machineType": machine_type_of(payload),
        "materials": payload.get("materials") if isinstance(payload.get("materials"), dict) else {},
        "geometry": payload.get("geometry") if isinstance(payload.get("geometry"), dict) else {},
        "currentsA": payload.get("currentsA", payload.get("currents_a")),
        "notes": payload.get("notes"),
        "thermal": payload.get("thermal") if isinstance(payload.get("thermal"), dict) else {},
        "demag": payload.get("demag") if isinstance(payload.get("demag"), dict) else {},
        "raw": payload,
    }
    return adapted
