"""Derive concentric-ring MEC geometry from AF SolveRequest geometry summary.

Field mapping (aligned with FE stub / radial schema reuse):
- ``rotor_od_m``  → outer **diameter** of active annulus
- ``stator_id_m`` → inner **diameter** of active annulus
- ``stack_length_m`` → disk / axial iron thickness (not RF stack)
- optional ``outer_radius_m`` / ``inner_radius_m`` override diameters
- ``n_planes`` → number of concentric rings (default 4)
"""
from __future__ import annotations

import math
from typing import Any


DEFAULT_N_PLANES = 4


def _f(d: dict, key: str, default: float) -> float:
    v = d.get(key, default)
    if v is None:
        return float(default)
    return float(v)


def resolve_annulus_radii(geometry: dict[str, Any], notes: list[str]) -> tuple[float, float]:
    """Return (inner_radius_m, outer_radius_m)."""
    if geometry.get("inner_radius_m") is not None and geometry.get("outer_radius_m") is not None:
        ri = float(geometry["inner_radius_m"])
        ro = float(geometry["outer_radius_m"])
        notes.append("annulus from inner_radius_m / outer_radius_m")
    elif geometry.get("rotor_id_m") is not None and geometry.get("rotor_od_m") is not None:
        ri = float(geometry["rotor_id_m"]) / 2.0
        ro = float(geometry["rotor_od_m"]) / 2.0
        notes.append("annulus from rotor_id_m / rotor_od_m (diameters→radii)")
    else:
        # Stub / RF-schema reuse: rotor_od_m = outer Ø, stator_id_m = inner Ø
        if "rotor_od_m" not in geometry or "stator_id_m" not in geometry:
            raise ValueError(
                "AF geometry needs outer/inner radii: provide outer_radius_m+inner_radius_m, "
                "or rotor_od_m+rotor_id_m, or rotor_od_m+stator_id_m (stub mapping)"
            )
        ro = float(geometry["rotor_od_m"]) / 2.0
        ri = float(geometry["stator_id_m"]) / 2.0
        notes.append(
            "annulus from rotor_od_m (outer Ø) / stator_id_m (inner Ø) — AF stub mapping"
        )

    if ri <= 0 or ro <= ri:
        raise ValueError(f"invalid AF annulus: inner_r={ri}, outer_r={ro}")
    return ri, ro


def derive_plane_geometry(
    geometry: dict[str, Any],
    notes: list[str],
    *,
    n_planes: int | None = None,
) -> tuple[dict[str, float], list[dict[str, float]]]:
    """Map AF GeometrySummary → common params + per-plane branch lengths/areas.

    Returns
    -------
    common : shared scalars (poles, turns, …)
    planes : list of dicts with A_pm, A_g, lengths, r_mean_m, dr_m, …
    """
    poles = max(int(geometry["poles"]), 2)
    slots = max(int(geometry.get("slots") or max(poles + 2, 3)), 3)
    if "slots" not in geometry or geometry["slots"] is None:
        notes.append(f"slots defaulted to {slots}")

    g = float(geometry["airgap_m"])
    ri, ro = resolve_annulus_radii(geometry, notes)

    if n_planes is None:
        raw = geometry.get("n_planes", DEFAULT_N_PLANES)
        n_planes = int(raw) if raw is not None else DEFAULT_N_PLANES
    n_planes = max(int(n_planes), 1)
    if "n_planes" not in geometry:
        notes.append(f"n_planes defaulted to {n_planes}")

    if "magnet_thickness_m" not in geometry or geometry["magnet_thickness_m"] is None:
        hm = max(0.003, 3.0 * g)
        notes.append(f"magnet_thickness_m defaulted to {hm:.4g} m")
    else:
        hm = float(geometry["magnet_thickness_m"])
        if hm <= 0:
            hm = max(0.003, 3.0 * g)
            notes.append(f"magnet_thickness_m non-positive; using {hm:.4g} m")

    if geometry.get("disk_thickness_m") is not None:
        disk_t = float(geometry["disk_thickness_m"])
    elif geometry.get("stack_length_m") is not None:
        disk_t = float(geometry["stack_length_m"])
        notes.append("disk_thickness_m taken from stack_length_m (AF axial thickness)")
    else:
        disk_t = max(0.006, 2.0 * hm)
        notes.append(f"disk_thickness_m defaulted to {disk_t:.4g} m")

    if "turns_per_phase" not in geometry or geometry["turns_per_phase"] is None:
        turns = 36
        notes.append("turns_per_phase defaulted to 36")
    else:
        turns = max(int(geometry["turns_per_phase"]), 1)

    alpha_m = _f(geometry, "magnet_arc_ratio", 0.7)
    if "magnet_arc_ratio" not in geometry:
        notes.append("magnet_arc_ratio defaulted to 0.7")

    kg = _f(geometry, "carter_factor", 1.15)
    if "carter_factor" not in geometry:
        notes.append("carter_factor defaulted to 1.15")
    g_eff = g * kg

    kw = _f(geometry, "winding_factor", 0.93)
    if "winding_factor" not in geometry:
        notes.append("winding_factor defaulted to 0.93")

    # Axial tooth / yoke thicknesses along flux (z); missing → estimate from disk
    if geometry.get("tooth_height_m"):
        ht = float(geometry["tooth_height_m"])
    else:
        ht = max(0.35 * disk_t, 0.002)
        notes.append(f"tooth_height_m (axial) estimated as {ht:.4g} m")

    r_mean_ann = 0.5 * (ri + ro)
    tau_p_mean = 2.0 * math.pi * r_mean_ann / poles
    bg_des, by_des = 0.85, 1.40
    hy_from_flux = bg_des * alpha_m * tau_p_mean / by_des

    if geometry.get("stator_yoke_height_m"):
        hy_s = float(geometry["stator_yoke_height_m"])
    else:
        hy_s = max(0.25 * disk_t, 0.5 * hy_from_flux, 0.002)
        notes.append(f"stator_yoke_height_m (axial) estimated as {hy_s:.4g} m")

    if geometry.get("rotor_yoke_height_m"):
        hy_r = float(geometry["rotor_yoke_height_m"])
    else:
        hy_r = max(0.2 * disk_t, 0.45 * hy_from_flux, 0.002)
        notes.append(f"rotor_yoke_height_m (axial) estimated as {hy_r:.4g} m")

    disk_count = int(geometry["disk_count"]) if geometry.get("disk_count") else 1
    if "disk_count" not in geometry:
        notes.append("disk_count defaulted to 1 (single airgap equivalent)")

    dr = (ro - ri) / float(n_planes)
    planes: list[dict[str, float]] = []
    for i in range(n_planes):
        r_in = ri + i * dr
        r_out = r_in + dr
        r_m = 0.5 * (r_in + r_out)
        tau_p = 2.0 * math.pi * r_m / poles
        tau_s = 2.0 * math.pi * r_m / slots
        w_m = alpha_m * tau_p
        A_pm = w_m * dr
        A_g = A_pm
        w_tooth = 0.5 * tau_s
        n_teeth = max(slots / poles, 0.5)
        A_tooth = w_tooth * dr * n_teeth
        # Circumferential yoke path length per pole at this ring
        L_sy = math.pi * r_m / poles
        L_ry = L_sy
        A_sy = hy_s * dr
        A_ry = hy_r * dr
        planes.append(
            {
                "index": float(i),
                "r_inner_m": r_in,
                "r_outer_m": r_out,
                "r_mean_m": r_m,
                "dr_m": dr,
                "tau_p_m": tau_p,
                "tau_s_m": tau_s,
                "A_pm_m2": A_pm,
                "A_g_m2": A_g,
                "A_tooth_m2": A_tooth,
                "A_sy_m2": A_sy,
                "A_ry_m2": A_ry,
                "magnet_thickness_m": hm,
                "airgap_eff_m": g_eff,
                "L_tooth_m": ht,
                "L_sy_m": L_sy,
                "L_ry_m": L_ry,
                "n_teeth_per_pole": n_teeth,
            }
        )

    common = {
        "poles": float(poles),
        "pole_pairs": float(poles) / 2.0,
        "slots": float(slots),
        "airgap_m": g,
        "airgap_eff_m": g_eff,
        "inner_radius_m": ri,
        "outer_radius_m": ro,
        "magnet_thickness_m": hm,
        "disk_thickness_m": disk_t,
        "disk_count": float(disk_count),
        "turns_per_phase": float(turns),
        "alpha_m": alpha_m,
        "kw": kw,
        "n_planes": float(n_planes),
        "r_mean_annulus_m": r_mean_ann,
    }
    return common, planes


def plane_to_mec_geo(plane: dict[str, float]) -> dict[str, float]:
    """Adapt one plane dict to keys expected by ``build_spm_branches``."""
    return {
        "magnet_thickness_m": plane["magnet_thickness_m"],
        "airgap_eff_m": plane["airgap_eff_m"],
        "A_pm_m2": plane["A_pm_m2"],
        "A_g_m2": plane["A_g_m2"],
        "A_tooth_m2": plane["A_tooth_m2"],
        "A_sy_m2": plane["A_sy_m2"],
        "A_ry_m2": plane["A_ry_m2"],
        "L_tooth_m": plane["L_tooth_m"],
        "L_sy_m": plane["L_sy_m"],
        "L_ry_m": plane["L_ry_m"],
    }
