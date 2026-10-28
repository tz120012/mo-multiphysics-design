"""Stretch: spot FEM for elite individuals (NOT MVP gate).

Q4-9: analytic+fem is stretch; absence must not block analytic Pareto demo.
"""
from __future__ import annotations

from typing import Any


def maybe_spot_fem(individual: dict[str, Any], *, enabled: bool = False) -> dict[str, Any]:
    """No-op stub. When enabled, would enqueue jobType=fem for elite x only."""
    if not enabled:
        return {**individual, "femSpot": None, "note": "spot FEM disabled (MVP analytic-only)"}
    return {**individual, "femSpot": "not_implemented", "note": "stretch hook only"}
