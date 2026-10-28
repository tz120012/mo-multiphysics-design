"""Torque–speed efficiency map scan (Q4-4). Default grid 20×20."""

from __future__ import annotations

from typing import Any, Callable


def _grid_cfg(cfg: dict[str, Any]) -> dict[str, float | int]:
    g = cfg.get("mapGrid") or cfg.get("map_grid") or {}
    if not isinstance(g, dict):
        g = {}
    nx = int(g.get("nx") or g.get("nSpeed") or 20)
    ny = int(g.get("ny") or g.get("nTorque") or 20)
    nx = max(2, min(nx, 64))
    ny = max(2, min(ny, 64))
    return {
        "nx": nx,
        "ny": ny,
        "speedRpmMin": float(g.get("speedRpmMin") or g.get("speed_rpm_min") or 500.0),
        "speedRpmMax": float(g.get("speedRpmMax") or g.get("speed_rpm_max") or 6000.0),
        "torqueNmMin": float(g.get("torqueNmMin") or g.get("torque_nm_min") or 0.5),
        "torqueNmMax": float(g.get("torqueNmMax") or g.get("torque_nm_max") or 10.0),
    }


def _lin(a: float, b: float, n: int) -> list[float]:
    if n == 1:
        return [a]
    return [a + (b - a) * i / (n - 1) for i in range(n)]


def run_map(
    cfg: dict[str, Any],
    case_fn: Callable[[dict[str, Any]], dict[str, Any]],
) -> dict[str, Any]:
    """Scan speed×torque; efficiency = Pmech/Pelec; OOB → null."""
    g = _grid_cfg(cfg)
    nx, ny = int(g["nx"]), int(g["ny"])
    speeds = _lin(float(g["speedRpmMin"]), float(g["speedRpmMax"]), nx)
    torques = _lin(float(g["torqueNmMin"]), float(g["torqueNmMax"]), ny)

    # Base mode for point solves
    mode = cfg.get("mode") or "pmsm_foc"
    if mode == "efficiency_map":
        mode = cfg.get("mapMode") or cfg.get("driveMode") or "pmsm_foc"

    eff: list[list[float | None]] = []
    torque_out: list[list[float | None]] = []
    valid = 0
    for j, tq in enumerate(torques):
        row_e: list[float | None] = []
        row_t: list[float | None] = []
        for i, sp in enumerate(speeds):
            point_cfg = {
                **{k: v for k, v in cfg.items() if k not in ("mapGrid", "map_grid", "mode")},
                "mode": mode,
                "operatingPoint": {
                    **(cfg.get("operatingPoint") or {}),
                    "speedRpm": sp,
                    "torqueNm": tq,
                },
            }
            try:
                r = case_fn(point_cfg)
                metrics = r.get("metrics") or {}
                eta = metrics.get("efficiency")
                t_avg = metrics.get("torqueAvgNm")
                # Mark invalid if efficiency non-positive or NaN-like
                if eta is None or not isinstance(eta, (int, float)) or eta <= 0 or eta > 1.05:
                    row_e.append(None)
                    row_t.append(None)
                else:
                    row_e.append(round(float(eta), 6))
                    row_t.append(round(float(t_avg), 6) if isinstance(t_avg, (int, float)) else None)
                    valid += 1
            except Exception:  # noqa: BLE001 — map cell failure → null
                row_e.append(None)
                row_t.append(None)
        eff.append(row_e)
        torque_out.append(row_t)

    return {
        "mode": "efficiency_map",
        "machineType": cfg.get("machineType") or cfg.get("machine_type") or "PMSM",
        "driveMode": mode,
        "axes": {
            "speedRpm": [round(s, 4) for s in speeds],
            "torqueNm": [round(t, 6) for t in torques],
        },
        "efficiency": eff,
        "torqueNm": torque_out,
        "meta": {
            "nx": nx,
            "ny": ny,
            "validCells": valid,
            "totalCells": nx * ny,
            "note": "Engineering efficiency map — not an accuracy claim",
            "grid": g,
        },
    }
