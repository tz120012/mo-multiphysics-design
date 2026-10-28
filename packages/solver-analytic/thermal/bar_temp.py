"""ACIM rotor bar / end-ring temperature rise (Q4-6 MVP).

ΔT = P * R_th. Not calibrated.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

_PKG = Path(__file__).resolve().parents[1]
if str(_PKG) not in sys.path:
    sys.path.insert(0, str(_PKG))

from .io_adapt import adapt_thermal_request, normalize_losses_w  # noqa: E402

_DEFAULT_RTH_BAR = 0.35  # K/W
_DEFAULT_RTH_END = 0.50  # K/W
_DEFAULT_AMBIENT_C = 40.0


def evaluate_bar_temp_acim(request: dict[str, Any]) -> dict[str, Any]:
    t0 = time.perf_counter()
    notes: list[str] = []
    adapted = adapt_thermal_request(request)
    source = adapted["source"]
    losses = dict(adapted["lossesW"])

    # Optional: pull from embedded SolveResult-like losses_w.rotor_bar
    raw = adapted.get("raw") or request
    lw = raw.get("losses_w")
    if isinstance(lw, dict):
        if losses.get("rotorBar") is None and lw.get("rotor_bar") is not None:
            losses["rotorBar"] = float(lw["rotor_bar"])
            notes.append("rotorBar from losses_w.rotor_bar")
        if losses.get("endRing") is None and lw.get("end_ring") is not None:
            losses["endRing"] = float(lw["end_ring"])
            notes.append("endRing from losses_w.end_ring")

    # Optional: run acim_equiv if solve request present and bar loss still missing
    if losses.get("rotorBar") is None and raw.get("machine_type") == "ACIM" and raw.get("topology") == "RF":
        try:
            from solve import solve  # noqa: WPS433

            em = solve(raw, solver="mec")
            rb = em.get("losses_w", {}).get("rotor_bar")
            if rb is not None:
                losses["rotorBar"] = float(rb)
                notes.append("rotorBar from acim_equiv solve()")
                if source == "analytic":
                    pass
                source = em.get("meta", {}).get("source", source) or "analytic"
        except Exception as exc:  # noqa: BLE001
            notes.append(f"acim_equiv solve skipped: {exc}")

    th = adapted.get("thermal") or {}
    r_bar = th.get("r_th_bar_k_per_w", request.get("r_th_bar_k_per_w", _DEFAULT_RTH_BAR))
    r_end = th.get("r_th_endring_k_per_w", request.get("r_th_endring_k_per_w", _DEFAULT_RTH_END))
    r_bar = float(r_bar)
    r_end = float(r_end)
    if th.get("r_th_bar_k_per_w") is None and request.get("r_th_bar_k_per_w") is None:
        notes.append(f"r_th_bar_k_per_w defaulted to {r_bar}")
    if th.get("r_th_endring_k_per_w") is None and request.get("r_th_endring_k_per_w") is None:
        notes.append(f"r_th_endring_k_per_w defaulted to {r_end}")

    op = adapted["operatingPoint"]
    ambient = op.get("T_ambientC")
    if ambient is None:
        ambient = th.get("ambient_c", _DEFAULT_AMBIENT_C)
        notes.append(f"T_ambientC defaulted to {ambient}")
    ambient = float(ambient)

    p_bar = float(losses["rotorBar"] or 0.0)
    p_end = float(losses["endRing"] or 0.0)
    if losses["rotorBar"] is None:
        notes.append("rotorBar loss missing → 0 W")
    if losses["endRing"] is None:
        notes.append("endRing loss missing → 0 W")

    dT_bar = p_bar * r_bar
    dT_end = p_end * r_end
    losses_out = normalize_losses_w(
        {"rotorBar": p_bar, "endRing": p_end, "copper": losses.get("copper"), "iron": losses.get("iron")}
    )

    elapsed = round((time.perf_counter() - t0) * 1000.0, 3)
    return {
        "meta": {
            "solver": "bar_temp_acim",
            "source": source,
            "pending_calibration": True,
            "mock": False,
            "elapsed_ms": elapsed,
            "note": "; ".join(notes) if notes else "Q4-6 bar_temp MVP",
        },
        "barDeltaT_K": round(dT_bar, 4),
        "endRingDeltaT_K": round(dT_end, 4),
        "bar_temp": {
            "lossesW": {
                "rotorBar": round(p_bar, 6),
                "endRing": round(p_end, 6),
            },
            "r_th_bar_k_per_w": r_bar,
            "r_th_endring_k_per_w": r_end,
            "ambient_c": ambient,
            "bar_temp_c": round(ambient + dT_bar, 4),
            "end_ring_temp_c": round(ambient + dT_end, 4),
        },
        "lossesW": {k: (None if v is None else round(float(v), 6)) for k, v in losses_out.items()},
        "pending_calibration": True,
        "source": source,
    }
