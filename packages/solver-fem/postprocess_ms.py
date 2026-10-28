"""Magnetostatic postprocess: parse Elmer SaveScalars → axialForceN (Maxwell).

Reads ``scalars.dat`` + ``scalars.dat.names`` produced by SaveData/SaveScalars
with Component ``Calculate Magnetic Force``. Column ``magnetic force 3`` is Fz
for AF axial pull. Never invents calibrated values; caller keeps
``pending_calibration=true``.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any


_FORCE_RE = re.compile(
    r"^\s*(\d+):\s*(?:component\s+\d+:\s*)?res:\s*magnetic force\s+(\d+)\s*$",
    re.IGNORECASE,
)
_ENERGY_RE = re.compile(
    r"^\s*(\d+):\s*res:\s*electromagnetic field energy\s*$",
    re.IGNORECASE,
)


def parse_elmer_scalars_dat(
    dat_path: Path,
    names_path: Path | None = None,
) -> dict[str, Any]:
    """Parse Elmer SaveScalars matrix + names into force/energy fields."""
    dat_path = Path(dat_path)
    if names_path is None:
        names_path = dat_path.with_suffix(dat_path.suffix + ".names")
        if not names_path.is_file():
            names_path = Path(str(dat_path) + ".names")

    out: dict[str, Any] = {
        "postprocess": "maxwell",
        "axialForceN": None,
        "forceXN": None,
        "forceYN": None,
        "magneticEnergyJ": None,
        "rawColumns": {},
        "notes": "",
    }

    if not dat_path.is_file():
        out["notes"] = f"missing SaveScalars file: {dat_path}"
        return out

    text = dat_path.read_text(encoding="utf-8", errors="replace").strip()
    if not text:
        out["notes"] = "empty scalars.dat"
        return out
    # Last non-empty line = values
    last = [ln for ln in text.splitlines() if ln.strip()][-1]
    values = [float(x) for x in last.split()]

    col_force: dict[int, int] = {}  # force_comp (1..3) -> 0-based index
    col_energy: int | None = None
    if names_path.is_file():
        for ln in names_path.read_text(encoding="utf-8", errors="replace").splitlines():
            m = _FORCE_RE.match(ln.strip())
            if m:
                col_force[int(m.group(2))] = int(m.group(1)) - 1
                continue
            m = _ENERGY_RE.match(ln.strip())
            if m:
                col_energy = int(m.group(1)) - 1

    def _get(idx: int | None) -> float | None:
        if idx is None or idx < 0 or idx >= len(values):
            return None
        return float(values[idx])

    fx = _get(col_force.get(1))
    fy = _get(col_force.get(2))
    fz = _get(col_force.get(3))
    # Fallback: if names missing but 5-col layout from our case.sif
    if fz is None and len(values) >= 5 and not col_force:
        fx, fy, fz = values[2], values[3], values[4]
        if col_energy is None and len(values) >= 2:
            col_energy = 1

    out["forceXN"] = fx
    out["forceYN"] = fy
    out["axialForceN"] = fz
    out["magneticEnergyJ"] = _get(col_energy)
    out["rawColumns"] = {
        "values": values,
        "forceColIndex1based": {str(k): v + 1 for k, v in col_force.items()},
        "energyColIndex1based": (col_energy + 1) if col_energy is not None else None,
    }
    out["notes"] = (
        "Maxwell/nodal magnetic force from Elmer Component SaveScalars "
        "(magnetic force 3 = Fz → axialForceN); uncalibrated — "
        "pending_calibration; do NOT claim FEM ≤3%"
    )
    return out


def postprocess_magnetostatic_job(solve_dir: Path) -> dict[str, Any]:
    """Locate scalars.dat under solve_dir and parse force scalars."""
    solve_dir = Path(solve_dir)
    candidates = [
        solve_dir / "scalars.dat",
        solve_dir / "mesh" / "scalars.dat",
    ]
    # Also accept VTU-sidecar naming
    for p in sorted(solve_dir.glob("**/scalars.dat")):
        if p not in candidates:
            candidates.append(p)

    for dat in candidates:
        if dat.is_file():
            return parse_elmer_scalars_dat(dat)

    return {
        "postprocess": "maxwell",
        "axialForceN": None,
        "forceXN": None,
        "forceYN": None,
        "magneticEnergyJ": None,
        "rawColumns": {},
        "notes": f"no scalars.dat under {solve_dir}; Maxwell postprocess skipped",
    }
