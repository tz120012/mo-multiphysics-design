"""Q6/D1 thin geometry rebuild — sync wrap of mo_geometry.rebuild_live_geometry.

Not a Celery Job. Full recompute every request; never return FE public/mesh fixtures.
Motor tip be6ed88 / cc3b2d1; arch lock 55b1255 (A1+B1+C2+D1; from 6dafa91).
Contract: docs/drafts/Q6-UEM与几何rebuild契约.md §2.
"""

from __future__ import annotations

import os
import sys
from copy import deepcopy
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from app.deps.auth import require_bearer


def _resolve_geometry_src() -> tuple[Path | None, list[str]]:
    """Locate packages/geometry/src for mo_geometry import (mirrors solver path resolve)."""
    tried: list[str] = []

    for env_key in ("MO_GEOMETRY_PATH", "GEOMETRY_PATH"):
        raw = (os.environ.get(env_key) or "").strip()
        if not raw:
            continue
        candidate = Path(raw).expanduser().resolve()
        tried.append(f"{env_key}={candidate}")
        src = candidate / "src" if (candidate / "src" / "mo_geometry").is_dir() else candidate
        if (src / "mo_geometry").is_dir():
            return src, tried
        if candidate.name == "mo_geometry" and candidate.is_dir():
            return candidate.parent, tried

    here = Path(__file__).resolve()
    for parent in here.parents:
        pkg = parent / "packages" / "geometry"
        src = pkg / "src"
        tried.append(str(src))
        if (src / "mo_geometry").is_dir():
            return src, tried

    return None, tried


_GEOMETRY_SRC, _GEOMETRY_TRIED = _resolve_geometry_src()
if _GEOMETRY_SRC is not None and str(_GEOMETRY_SRC) not in sys.path:
    sys.path.insert(0, str(_GEOMETRY_SRC))


def _load_rebuild():
    try:
        from mo_geometry import rebuild_live_geometry  # type: ignore
    except ImportError:
        try:
            from mo_geometry.summary import rebuild_live_geometry  # type: ignore
        except ImportError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "code": "geometry_unavailable",
                    "message": (
                        "mo_geometry not importable "
                        "(pip install -e packages/geometry or set MO_GEOMETRY_PATH)"
                    ),
                    "details": {
                        "path": str(_GEOMETRY_SRC) if _GEOMETRY_SRC else None,
                        "tried": _GEOMETRY_TRIED,
                        "error": str(exc),
                    },
                },
            ) from exc
    return rebuild_live_geometry


router = APIRouter(
    prefix="/api/v1/geometry",
    tags=["Geometry"],
    dependencies=[Depends(require_bearer)],
)


class GeometryRebuildRequest(BaseModel):
    """Primary OpenAPI / FE envelope (arch 55b1255 §2.2).

    ``{ topology, machineType?, params }`` where params = geometry/params.json.
    """

    model_config = ConfigDict(extra="allow")

    topology: str = Field(..., description="RF | AF — must match params.topology")
    machineType: str | None = Field(
        default=None,
        description="BLDC | PMSM | ACIM — optional; merged into params when set",
    )
    params: dict[str, Any] = Field(
        ...,
        description="geometry/params.json object (schemaVersion 0.1.0-q1)",
    )


def normalize_rebuild_params(body: dict[str, Any]) -> dict[str, Any]:
    """Build the dict passed to ``rebuild_live_geometry``.

    **Primary (FE / OpenAPI):** ``{ topology, machineType?, params }`` —
    merge envelope topology/machineType into a copy of ``params`` (envelope wins).
    If both sides set topology and they differ → ValueError.

    **Compat:** ``{ params: <geometry params with topology> }`` only when nested
    params already carries ``topology``.

    **Tooling alternate (not OpenAPI primary):** bare geometry/params.json at root
    (has topology + stator|rotor|pmsm).
    """
    if not isinstance(body, dict):
        raise ValueError("rebuild body must be a JSON object")

    nested = body.get("params")
    has_nested_params = isinstance(nested, dict)
    root_topology = body.get("topology")

    # Primary FE envelope
    if has_nested_params and root_topology is not None:
        params = deepcopy(nested)
        nested_topo = params.get("topology")
        if nested_topo is not None and nested_topo != root_topology:
            raise ValueError(
                f"rebuild: topology mismatch envelope={root_topology!r} "
                f"vs params.topology={nested_topo!r}"
            )
        params["topology"] = root_topology
        if body.get("machineType") is not None:
            params["machineType"] = body["machineType"]
        return params

    # Compat unwrap {params} only if topology present inside
    if has_nested_params and root_topology is None:
        if nested.get("topology") is None:
            raise ValueError(
                "rebuild: expected primary {topology, machineType?, params}; "
                "compat {params} requires params.topology"
            )
        return deepcopy(nested)

    # Tooling: bare params root
    if root_topology is not None and (
        "stator" in body or "rotor" in body or "pmsm" in body
    ):
        return deepcopy(body)

    raise ValueError(
        "rebuild: expected primary {topology, machineType?, params} "
        "(params = geometry/params.json)"
    )


@router.post(
    "/rebuild",
    summary="Sync live geometry rebuild (Q6/D1; not a Job)",
    response_model=None,
)
def post_geometry_rebuild(
    body: dict[str, Any],
    _: Annotated[str, Depends(require_bearer)],
) -> dict[str, Any]:
    """Call ``mo_geometry.rebuild_live_geometry`` — full recompute; no cache/fixture.

    Request (primary): ``{ topology, machineType?, params }`` per arch ``55b1255``.
    200: ``{ params, meshDescriptor, geometrySummary[, pipelineEntry] }``.
    """
    try:
        params = normalize_rebuild_params(body)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "bad_request", "message": str(exc)},
        ) from exc

    if not params.get("topology"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "bad_request",
                "message": "rebuild: topology required (RF|AF)",
            },
        )

    rebuild = _load_rebuild()
    try:
        return rebuild(params)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "bad_request", "message": str(exc)},
        ) from exc
