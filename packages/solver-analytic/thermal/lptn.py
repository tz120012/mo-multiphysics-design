"""Simplified LPTN + temperature-feedback loop (Q4-7 MVP).

Output iters[] shape locked to FEM thermal-loop-iter-v0 (tip 864ec20).
heat-proxy temperatures must NOT be used as tempsOut.
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

from .io_adapt import adapt_thermal_request, normalize_losses_w  # noqa: E402

# Default thermal conductances (W/K) between node pairs
_DEFAULT_G = {
    "copper_iron": 8.0,
    "iron_ambient": 4.0,
    "copper_ambient": 1.5,
    "magnet_iron": 6.0,
    "magnet_ambient": 1.0,
    "bar_iron": 6.0,  # alias when ACIM uses magnet_or_bar as bar
}
_DEFAULT_C = {  # J/K — used only for short transient smoothing (optional)
    "copper": 200.0,
    "iron": 800.0,
    "magnet_or_bar": 150.0,
}
_ALPHA_BR = -0.0012  # 1/K relative to 20 C
_ALPHA_CU = 0.0039  # 1/K copper resistivity
_T_REF = 20.0


def _steady_temps(
    losses: dict[str, float | None],
    *,
    ambient_c: float,
    g: dict[str, float],
    machine: str | None,
) -> dict[str, float]:
    """4-node resistive network steady-state (linear solve by successive substitution)."""
    p_cu = float(losses.get("copper") or 0.0)
    p_fe = float(losses.get("iron") or 0.0)
    p_pm = float(losses.get("pmEddy") or 0.0)
    p_bar = float(losses.get("rotorBar") or 0.0) + float(losses.get("endRing") or 0.0)
    # magnet_or_bar node gets pmEddy for PM, bar+endRing for ACIM
    is_acim = (machine or "").upper() == "ACIM"
    p_mob = p_bar if is_acim else p_pm

    g_ci = g.get("copper_iron", _DEFAULT_G["copper_iron"])
    g_ia = g.get("iron_ambient", _DEFAULT_G["iron_ambient"])
    g_ca = g.get("copper_ambient", _DEFAULT_G["copper_ambient"])
    g_mi = g.get("magnet_iron", _DEFAULT_G["magnet_iron"])
    g_ma = g.get("magnet_ambient", _DEFAULT_G["magnet_ambient"])

    # Unknowns: Tc, Ti, Tm  (Ta fixed)
    # Power balance:
    # Pcu + Gci(Ti-Tc) + Gca(Ta-Tc) = 0  →  Tc*(Gci+Gca) - Ti*Gci = Pcu + Gca*Ta
    # Pfe + Gci(Tc-Ti) + Gmi(Tm-Ti) + Gia(Ta-Ti) = 0
    # Pmob + Gmi(Ti-Tm) + Gma(Ta-Tm) = 0
    ta = ambient_c
    a11, a12, a13 = g_ci + g_ca, -g_ci, 0.0
    a21, a22, a23 = -g_ci, g_ci + g_mi + g_ia, -g_mi
    a31, a32, a33 = 0.0, -g_mi, g_mi + g_ma
    b1 = p_cu + g_ca * ta
    b2 = p_fe + g_ia * ta
    b3 = p_mob + g_ma * ta

    # 3x3 Cramer's / elimination
    det = (
        a11 * (a22 * a33 - a23 * a32)
        - a12 * (a21 * a33 - a23 * a31)
        + a13 * (a21 * a32 - a22 * a31)
    )
    if abs(det) < 1e-18:
        return {"copper": ta + 1.0, "iron": ta + 1.0, "magnet_or_bar": ta + 1.0, "ambient": ta}

    def det_repl(c1, c2, c3) -> float:
        return (
            c1[0] * (c2[1] * c3[2] - c2[2] * c3[1])
            - c1[1] * (c2[0] * c3[2] - c2[2] * c3[0])
            + c1[2] * (c2[0] * c3[1] - c2[1] * c3[0])
        )

    tc = det_repl((b1, a12, a13), (b2, a22, a23), (b3, a32, a33)) / det
    ti = det_repl((a11, b1, a13), (a21, b2, a23), (a31, b3, a33)) / det
    tm = det_repl((a11, a12, b1), (a21, a22, b2), (a31, a32, b3)) / det
    return {
        "copper": float(tc),
        "iron": float(ti),
        "magnet_or_bar": float(tm),
        "ambient": float(ta),
    }


def evaluate_lptn_loop(request: dict[str, Any]) -> dict[str, Any]:
    t0 = time.perf_counter()
    notes: list[str] = []
    adapted = adapt_thermal_request(request)
    source = adapted["source"]
    losses0 = normalize_losses_w(adapted["lossesW"])
    th = adapted.get("thermal") or {}
    g = {**_DEFAULT_G, **(th.get("conductance_w_per_k") or {})}
    max_iter = int(th.get("max_iter", request.get("max_iter", 8)))
    tol = float(th.get("tol", request.get("tol", 0.05)))  # residual on temps C

    op = adapted["operatingPoint"]
    ambient = op.get("T_ambientC")
    if ambient is None:
        ambient = float(th.get("ambient_c", 25.0))
        notes.append(f"T_ambientC defaulted to {ambient}")
    ambient = float(ambient)

    machine = adapted["machineType"]
    # Seed losses from acim/mec solve if empty
    raw = adapted.get("raw") or request
    if all(losses0.get(k) is None for k in ("iron", "copper", "pmEddy", "rotorBar", "endRing")):
        if raw.get("topology") and raw.get("machine_type"):
            try:
                from solve import solve  # noqa: WPS433

                em = solve(raw, solver="mec")
                lw = em.get("losses_w") or {}
                losses0 = normalize_losses_w(
                    {
                        "copper": lw.get("copper"),
                        "iron": lw.get("iron"),
                        "pmEddy": lw.get("magnet_eddy"),
                        "rotorBar": lw.get("rotor_bar"),
                        "endRing": lw.get("end_ring"),
                    }
                )
                notes.append("seeded lossesW from analytic solve()")
                source = "analytic"
            except Exception as exc:  # noqa: BLE001
                notes.append(f"solve() seed skipped: {exc}")
                # demo defaults
                losses0 = normalize_losses_w({"copper": 80.0, "iron": 40.0, "pmEddy": 5.0})
                notes.append("lossesW demo defaults copper=80 iron=40 pmEddy=5")
        else:
            losses0 = normalize_losses_w({"copper": 80.0, "iron": 40.0, "pmEddy": 5.0})
            notes.append("lossesW demo defaults (no EM request)")

    br_factor = 1.0
    res_factor = 1.0
    iters: list[dict[str, Any]] = []
    losses = dict(losses0)
    temps = _steady_temps(losses, ambient_c=ambient, g=g, machine=machine)
    converged = False
    residual: float | None = None

    for k in range(max_iter):
        temps = _steady_temps(losses, ambient_c=ambient, g=g, machine=machine)
        t_w = temps["copper"]
        t_m = temps["magnet_or_bar"]
        # Material updates vs 20 C ref
        br_factor = 1.0 + _ALPHA_BR * (t_m - _T_REF)
        res_factor = 1.0 + _ALPHA_CU * (t_w - _T_REF)
        br_factor = max(0.5, min(br_factor, 1.2))
        res_factor = max(0.8, min(res_factor, 2.5))

        # Scale losses: copper ~ resistivity; iron mild; pmEddy ~ Br^2
        new_losses = normalize_losses_w(
            {
                "copper": (losses0.get("copper") or 0.0) * res_factor,
                "iron": (losses0.get("iron") or 0.0) * (0.85 + 0.15 * res_factor),
                "pmEddy": (losses0.get("pmEddy") or 0.0) * (br_factor**2),
                "rotorBar": (losses0.get("rotorBar") or 0.0) * res_factor,
                "endRing": (losses0.get("endRing") or 0.0) * res_factor,
            }
        )

        # residual: max |ΔT| vs previous after recompute with new losses
        temps_new = _steady_temps(new_losses, ambient_c=ambient, g=g, machine=machine)
        residual = max(
            abs(temps_new["copper"] - temps["copper"]),
            abs(temps_new["iron"] - temps["iron"]),
            abs(temps_new["magnet_or_bar"] - temps["magnet_or_bar"]),
        )

        iters.append(
            {
                "iter": k,
                "lossesIn": {
                    "source": source,
                    "lossesW": {
                        "iron": None if losses.get("iron") is None else round(float(losses["iron"]), 6),
                        "copper": None if losses.get("copper") is None else round(float(losses["copper"]), 6),
                        "pmEddy": None if losses.get("pmEddy") is None else round(float(losses["pmEddy"]), 6),
                        "rotorBar": None if losses.get("rotorBar") is None else round(float(losses["rotorBar"]), 6),
                        "endRing": None if losses.get("endRing") is None else round(float(losses["endRing"]), 6),
                    },
                },
                "tempsOut": {
                    "windingC": round(temps["copper"], 4),
                    "magnetC": round(temps["magnet_or_bar"], 4),
                    "ambientC": round(ambient, 4),
                },
                "materialUpdate": {
                    "BrFactor": round(br_factor, 6),
                    "resistivityFactor": round(res_factor, 6),
                },
                "residual": round(residual, 6),
            }
        )

        losses = new_losses
        temps = temps_new
        if residual is not None and residual < tol:
            converged = True
            break

    # Optional torque rough estimate via solve with scaled Br note only (no FEM)
    torque_nm = op.get("torqueNm")
    if torque_nm is None and raw.get("topology") and raw.get("machine_type"):
        try:
            from solve import solve  # noqa: WPS433

            req2 = dict(raw)
            mats = dict(req2.get("materials") or {})
            if "br_t" in mats and mats["br_t"] is not None:
                mats["br_t"] = float(mats["br_t"]) * br_factor
            req2["materials"] = mats
            em2 = solve(req2, solver="mec")
            torque_nm = em2.get("torque_nm")
            notes.append("torque_nm from solve() with BrFactor applied to inline br_t")
        except Exception as exc:  # noqa: BLE001
            notes.append(f"torque re-solve skipped: {exc}")

    elapsed = round((time.perf_counter() - t0) * 1000.0, 3)
    losses_final = normalize_losses_w(losses)

    return {
        "schemaVersion": "thermal-loop-iter-v0",
        "pending_calibration": True,
        "source": source,
        "jobId": adapted.get("jobId"),
        "resultRef": adapted.get("resultRef"),
        "lossBreakdown": adapted.get("lossBreakdown"),
        "lossesW": losses_final,
        "operatingPoint": {
            "rpm": op.get("rpm"),
            "torqueNm": torque_nm if torque_nm is not None else op.get("torqueNm"),
            "T_ambientC": ambient,
        },
        "meta": {
            "solver": "lptn_loop",
            "source": source,
            "pending_calibration": True,
            "converged": converged,
            "elapsed_ms": elapsed,
            "mock": False,
            "note": "; ".join(notes) if notes else "Q4-7 LPTN MVP",
            "nodes_c": {k: round(v, 4) for k, v in temps.items()},
            "tol": tol,
            "max_iter": max_iter,
        },
        "iters": iters,
        "fem_compare_hook": None,
    }
