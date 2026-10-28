"""PM demagnetization working-point margin (Q4-6 MVP).

Not calibrated. Always sets pending_calibration=True.
"""
from __future__ import annotations

import math
import sys
import time
from pathlib import Path
from typing import Any

_PKG = Path(__file__).resolve().parents[1]
if str(_PKG) not in sys.path:
    sys.path.insert(0, str(_PKG))

from materials_adapter import resolve_from_request  # noqa: E402

from .io_adapt import adapt_thermal_request  # noqa: E402

MU0 = 4.0 * math.pi * 1e-7
_DEFAULT_KNEE_FRAC = 0.45  # knee_b ≈ frac * Br_at_temp when no curve
_DEFAULT_ALPHA_BR = -0.0012  # 1/K
_T_REF_C = 20.0


def _knee_from_demag_blob(demag: Any, br_at_temp: float, notes: list[str]) -> float:
    """Extract knee B (T) from demag list/curve or engineering default."""
    if isinstance(demag, list) and demag:
        # Prefer explicit kneeB / bKnee; else min B on curve points
        bs: list[float] = []
        for row in demag:
            if not isinstance(row, dict):
                continue
            for k in ("knee_b_t", "kneeBT", "bKnee", "b_t", "bT"):
                if k in row and row[k] is not None:
                    try:
                        bs.append(float(row[k]))
                    except (TypeError, ValueError):
                        pass
            curve = row.get("curve")
            if isinstance(curve, list):
                for p in curve:
                    if isinstance(p, dict):
                        for k in ("b_t", "bT", "B"):
                            if k in p:
                                try:
                                    bs.append(float(p[k]))
                                except (TypeError, ValueError):
                                    pass
        if bs:
            knee = min(bs)
            notes.append(f"knee_b_t from demag blob min={knee:.4g} T")
            return knee
    knee = _DEFAULT_KNEE_FRAC * br_at_temp
    notes.append(f"knee_b_t defaulted to {_DEFAULT_KNEE_FRAC}*Br_at_temp={knee:.4g} T")
    return knee


def evaluate_demag_pm(request: dict[str, Any]) -> dict[str, Any]:
    """Compute demagMargin + workingPoint summary for PM machines."""
    t0 = time.perf_counter()
    notes: list[str] = []
    adapted = adapt_thermal_request(request)
    source = adapted["source"]

    # Build a minimal SolveRequest-shaped dict for materials_adapter when possible
    mats_req = {
        "materials": adapted["materials"] or request.get("materials") or {},
        "materials_catalog": request.get("materials_catalog"),
    }
    resolved = None
    try:
        if mats_req["materials"] or request.get("topology"):
            # Prefer full request if it looks like SolveRequest
            if request.get("topology") and request.get("machine_type"):
                resolved = resolve_from_request(request)
            else:
                resolved = resolve_from_request(
                    {
                        "topology": "RF",
                        "machine_type": adapted["machineType"] or "PMSM",
                        "geometry": adapted["geometry"] or {"poles": 10, "slots": 12, "stack_length_m": 0.04,
                                                            "airgap_m": 0.001, "rotor_od_m": 0.05, "stator_id_m": 0.052},
                        "materials": mats_req["materials"],
                        "materials_catalog": mats_req["materials_catalog"],
                        "operating_point": {"speed_rpm": adapted["operatingPoint"].get("rpm") or 0.0},
                    }
                )
    except Exception as exc:  # noqa: BLE001 — MVP fallback
        notes.append(f"materials_adapter skipped: {exc}")

    br_ref = 1.2
    alpha = _DEFAULT_ALPHA_BR
    demag_blob = None
    if resolved is not None:
        br_ref = float(resolved.br_t)
        if resolved.temp_coeff_br is not None:
            alpha = float(resolved.temp_coeff_br)
        demag_blob = resolved.magnet_demag_curve
        notes.extend(resolved.notes)
        notes.append(f"br_t source={resolved.sources.get('br_t', 'resolved')}")
    else:
        inline = adapted["materials"]
        if inline.get("br_t") is not None:
            br_ref = float(inline["br_t"])
            notes.append("br_t from inline materials")
        else:
            notes.append("br_t engineering default 1.2 T")
        for k in ("temp_coeff_br", "tempCoeffBr", "alphaBr", "alpha_br"):
            if inline.get(k) is not None:
                alpha = float(inline[k])
                break
        else:
            notes.append(f"temp_coeff_br defaulted to {alpha}")

    demag_in = adapted["demag"] or {}
    if demag_blob is None:
        demag_blob = demag_in.get("demag") or demag_in.get("demagCurve") or request.get("demagCurve")

    op = adapted["operatingPoint"]
    temp_c = op.get("tempC")
    if temp_c is None:
        temp_c = demag_in.get("temperature_c", demag_in.get("tempC"))
    if temp_c is None:
        temp_c = 100.0
        notes.append("temperature_c defaulted to 100 C for demag MVP")
    temp_c = float(temp_c)

    br_at_temp = br_ref * (1.0 + alpha * (temp_c - _T_REF_C))
    if br_at_temp <= 0:
        br_at_temp = 0.01
        notes.append("br_t_at_temp floored to 0.01 T")

    if demag_in.get("knee_b_t") is not None:
        knee = float(demag_in["knee_b_t"])
        notes.append("knee_b_t from request.demag")
    else:
        knee = _knee_from_demag_blob(demag_blob, br_at_temp, notes)

    # Working point B
    b_wp = demag_in.get("working_point_b_t", request.get("working_point_b_t"))
    load_line_pc = demag_in.get("load_line_pc", request.get("load_line_pc"))
    if b_wp is not None:
        b_wp = float(b_wp)
    elif load_line_pc is not None:
        # B = Br * Pc / (Pc + μr) with μr≈1.05
        pc = float(load_line_pc)
        mur = 1.05
        b_wp = br_at_temp * pc / (pc + mur)
        notes.append(f"working_point_b_t from load_line_pc={pc}")
    else:
        # Crude: ~0.7 * Br_at_temp for SPM-ish
        b_wp = 0.70 * br_at_temp
        load_line_pc = 4.0
        notes.append("working_point_b_t defaulted to 0.70*Br_at_temp; load_line_pc~4")

    # H on recoil: H ≈ (B - Br) / (μ0 μr)
    mur = 1.05
    h_wp = (b_wp - br_at_temp) / (MU0 * mur)

    margin_ref = str(demag_in.get("margin_ref", "knee"))
    if margin_ref == "br":
        demag_margin = (b_wp - 0.0) / br_at_temp if br_at_temp else 0.0
    else:
        demag_margin = (b_wp - knee) / br_at_temp if br_at_temp else 0.0
        margin_ref = "knee"

    if load_line_pc is None and br_at_temp > b_wp > 0:
        # invert B = Br * Pc/(Pc+mur)
        load_line_pc = mur * b_wp / max(br_at_temp - b_wp, 1e-9)

    elapsed = round((time.perf_counter() - t0) * 1000.0, 3)
    return {
        "meta": {
            "solver": "demag_pm",
            "source": source,
            "pending_calibration": True,
            "mock": False,
            "elapsed_ms": elapsed,
            "note": "; ".join(notes) if notes else "Q4-6 demag MVP",
        },
        "demagMargin": round(demag_margin, 6),
        "workingPoint": {
            "b_t": round(b_wp, 6),
            "h_a_per_m": round(h_wp, 3),
            "temperature_c": temp_c,
        },
        "demag": {
            "br_t_ref": round(br_ref, 6),
            "br_t_at_temp": round(br_at_temp, 6),
            "knee_b_t": round(knee, 6),
            "load_line_pc": round(float(load_line_pc), 4) if load_line_pc is not None else None,
            "margin_ref": margin_ref,
            "demag_margin": round(demag_margin, 6),
        },
        "pending_calibration": True,
        "source": source,
    }
