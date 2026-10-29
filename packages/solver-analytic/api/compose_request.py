"""Assemble SolveRequest from UEM / rebuild slices (Q6 closed-loop).

Does **not** invent geometry: callers pass GeometrySummary (snake SI) from
``packages/geometry.export_geometry_summary`` / rebuild_live, plus materials + OP.
No second geometry truth; no core algorithm change.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

SOLVE_SCHEMA_VERSION = "0.0.0-gate0"

_REQUIRED_GEOM = (
    "poles",
    "slots",
    "stack_length_m",
    "airgap_m",
    "rotor_od_m",
    "stator_id_m",
)


def compose_solve_request(
    *,
    topology: str,
    machine_type: str,
    geometry: dict[str, Any],
    materials: dict[str, Any],
    operating_point: dict[str, Any],
    schema_version: str = SOLVE_SCHEMA_VERSION,
    solver: str | None = None,
) -> dict[str, Any]:
    """Build a SolveRequest dict ready for ``solve()`` / sync POST.

    Parameters
    ----------
    topology:
        ``RF`` or ``AF``.
    machine_type:
        ``PMSM`` | ``BLDC`` | ``ACIM``.
    geometry:
        Compact GeometrySummary (SI metres, snake_case). Required RF keys in
        ``_REQUIRED_GEOM``; AF may add ``n_planes`` / radii (see solve.schema.json).
    materials:
        Inline and/or catalog ids (see materials_adapter).
    operating_point:
        At least machine-appropriate fields (e.g. PMSM: speed_rpm + current_a_peak).
    schema_version:
        Default ``0.0.0-gate0``.
    solver:
        Optional ``mec`` | ``mock`` hint for HTTP query / body; omitted from body
        when None (sync router defaults to mec).
    """
    if not isinstance(geometry, dict):
        raise TypeError("geometry must be a dict (GeometrySummary)")
    if not isinstance(materials, dict):
        raise TypeError("materials must be a dict")
    if not isinstance(operating_point, dict):
        raise TypeError("operating_point must be a dict")

    topo = str(topology).strip().upper()
    mtype = str(machine_type).strip().upper()
    if topo not in ("RF", "AF"):
        raise ValueError(f"topology must be RF|AF, got {topology!r}")
    if mtype not in ("PMSM", "BLDC", "ACIM"):
        raise ValueError(f"machine_type must be PMSM|BLDC|ACIM, got {machine_type!r}")

    missing = [k for k in _REQUIRED_GEOM if k not in geometry]
    if missing:
        raise ValueError(f"geometry missing required keys: {missing}")

    req: dict[str, Any] = {
        "schema_version": schema_version,
        "topology": topo,
        "machine_type": mtype,
        "geometry": deepcopy(geometry),
        "materials": deepcopy(materials),
        "operating_point": deepcopy(operating_point),
    }
    if solver is not None:
        kind = str(solver).strip().lower()
        if kind not in ("mec", "mock"):
            raise ValueError(f"solver must be mec|mock, got {solver!r}")
        req["solver"] = kind
    return req


__all__ = ["SOLVE_SCHEMA_VERSION", "compose_solve_request"]
