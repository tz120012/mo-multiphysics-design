"""Derive MEC branch lengths/areas from SolveRequest geometry summary."""
from __future__ import annotations

import math
from typing import Any


def _f(d: dict, key: str, default: float) -> float:
    v = d.get(key, default)
    if v is None:
        return float(default)
    return float(v)


def derive_mec_geometry(geometry: dict[str, Any], notes: list[str]) -> dict[str, float]:
    """Map compact GeometrySummary → lengths/areas for a one-pole flux path.

    Missing optional fields get engineering defaults; reasons appended to ``notes``.
    """
    poles = max(int(geometry["poles"]), 2)
    slots = max(int(geometry["slots"]), 3)
    L = float(geometry["stack_length_m"])
    g = float(geometry["airgap_m"])
    rod = float(geometry["rotor_od_m"])
    sid = float(geometry["stator_id_m"])

    if "magnet_thickness_m" not in geometry or geometry["magnet_thickness_m"] is None:
        hm = max(0.003, 3.0 * g)
        notes.append(f"magnet_thickness_m defaulted to {hm:.4g} m")
    else:
        hm = float(geometry["magnet_thickness_m"])
        if hm <= 0:
            hm = max(0.003, 3.0 * g)
            notes.append(f"magnet_thickness_m non-positive; using {hm:.4g} m")

    if "turns_per_phase" not in geometry or geometry["turns_per_phase"] is None:
        turns = 48
        notes.append("turns_per_phase defaulted to 48")
    else:
        turns = max(int(geometry["turns_per_phase"]), 1)

    tau_p = math.pi * sid / poles
    tau_s = math.pi * sid / slots

    alpha_m = _f(geometry, "magnet_arc_ratio", 0.7)
    if "magnet_arc_ratio" not in geometry:
        notes.append("magnet_arc_ratio defaulted to 0.7")

    kg = _f(geometry, "carter_factor", 1.15)
    if "carter_factor" not in geometry:
        notes.append("carter_factor defaulted to 1.15")
    g_eff = g * kg

    w_m = alpha_m * tau_p
    A_pm = w_m * L
    A_g = w_m * L

    w_tooth = 0.5 * tau_s
    n_teeth = max(slots / poles, 0.5)
    A_tooth_one = w_tooth * L
    A_tooth = A_tooth_one * n_teeth

    # Tooth height: schema has no stator OD — scale with bore (slot depth)
    if "tooth_height_m" in geometry and geometry["tooth_height_m"]:
        ht = float(geometry["tooth_height_m"])
    else:
        ht = max(0.12 * sid, 0.55 * tau_p)
        notes.append(f"tooth_height_m estimated as {ht:.4g} m")

    # Yoke height from flux continuity: Φ ≈ Bg·αm·τp·L, By≈1.4 T
    # hy = Φ / (By · L) = Bg_des · αm · τp / By_des
    bg_des = 0.85
    by_des = 1.40
    hy_from_flux = bg_des * alpha_m * tau_p / by_des

    if "stator_yoke_height_m" in geometry and geometry["stator_yoke_height_m"]:
        hy_s = float(geometry["stator_yoke_height_m"])
    else:
        hy_s = max(0.06 * sid, hy_from_flux)
        notes.append(f"stator_yoke_height_m estimated as {hy_s:.4g} m")

    if "rotor_yoke_height_m" in geometry and geometry["rotor_yoke_height_m"]:
        hy_r = float(geometry["rotor_yoke_height_m"])
    else:
        hy_r = max(0.05 * sid, 0.85 * hy_from_flux)
        notes.append(f"rotor_yoke_height_m estimated as {hy_r:.4g} m")

    d_sy = sid + 2.0 * ht + hy_s
    d_ry = max(rod - 2.0 * hm - hy_r, 0.25 * rod)

    L_sy = math.pi * d_sy / poles
    L_ry = math.pi * d_ry / poles

    A_sy = hy_s * L
    A_ry = hy_r * L

    kw = _f(geometry, "winding_factor", 0.93)
    if "winding_factor" not in geometry:
        notes.append("winding_factor defaulted to 0.93")

    r_ag = 0.25 * (rod + sid)

    return {
        "poles": float(poles),
        "pole_pairs": float(poles) / 2.0,
        "slots": float(slots),
        "stack_length_m": L,
        "airgap_m": g,
        "airgap_eff_m": g_eff,
        "rotor_od_m": rod,
        "stator_id_m": sid,
        "magnet_thickness_m": hm,
        "turns_per_phase": float(turns),
        "tau_p_m": tau_p,
        "tau_s_m": tau_s,
        "alpha_m": alpha_m,
        "A_pm_m2": A_pm,
        "A_g_m2": A_g,
        "A_tooth_m2": A_tooth,
        "A_sy_m2": A_sy,
        "A_ry_m2": A_ry,
        "L_tooth_m": ht,
        "L_sy_m": L_sy,
        "L_ry_m": L_ry,
        "r_airgap_m": r_ag,
        "kw": kw,
        "n_teeth_per_pole": n_teeth,
    }
