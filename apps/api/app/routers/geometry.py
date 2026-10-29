"""Q6/D1 thin geometry rebuild — sync HTTP over mo_geometry (not a Celery Job).

Prefer ``rebuild_viewport_payload`` (geometry tip ``05180e2``) so the Response
includes §2.3 min set **plus** ``paramsHash`` / ``schemaVersion`` / ``meta`` when
the viewport helpers are available. Fallback: ``rebuild_live_geometry`` (tip
``e659e0a``) when viewport import fails.

Never return FE public/mesh fixtures. Full recompute every request.
Motor tip be6ed88 / cc3b2d1; arch lock 55b1255 (A1+B1+C2+D1; from 6dafa91).
Contract: docs/drafts/Q6-UEM与几何rebuild契约.md §2.
OpenAPI primary request schema: ``GeometryRebuildRequest`` in
``docs/drafts/openapi-v1.yaml`` (``{topology, machineType?, params}``).
Handler accepts a JSON object so viewport unwrap / compat bare-params still work.
"""

from __future__ import annotations

import os
import sys
from copy import deepcopy
from pathlib import Path
from typing import Annotated, Any, Callable, Literal

from fastapi import APIRouter, Depends, HTTPException, status

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


def _geometry_unavailable(exc: BaseException) -> HTTPException:
    return HTTPException(
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
    )


def _load_rebuild_live() -> Callable[[dict[str, Any]], dict[str, Any]]:
    try:
        from mo_geometry import rebuild_live_geometry  # type: ignore
    except ImportError:
        try:
            from mo_geometry.summary import rebuild_live_geometry  # type: ignore
        except ImportError as exc:
            raise _geometry_unavailable(exc) from exc
    return rebuild_live_geometry


def _load_rebuild_fn() -> tuple[
    Literal["viewport", "live"],
    Callable[[dict[str, Any]], dict[str, Any]],
]:
    """Prefer viewport supersets; ImportError → live min-set path (e659e0a)."""
    try:
        from mo_geometry.viewport import rebuild_viewport_payload  # type: ignore

        return "viewport", rebuild_viewport_payload
    except ImportError:
        return "live", _load_rebuild_live()


router = APIRouter(
    prefix="/api/v1/geometry",
    tags=["Geometry"],
    dependencies=[Depends(require_bearer)],
)


def normalize_rebuild_params(body: dict[str, Any]) -> dict[str, Any]:
    """Build the dict passed to ``rebuild_live_geometry`` (live fallback path).

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
    responses={
        200: {
            "description": (
                "§2.3 min set: params, meshDescriptor, geometrySummary[, pipelineEntry]. "
                "Optional extras (ignore-unknown for FE): paramsHash (16-char hex), "
                "schemaVersion, meta — present when viewport helpers are available "
                "(geometry tip 05180e2)."
            ),
        },
        400: {"description": "Validation failed (invalid params / topology mismatch)."},
        401: {"description": "Missing or invalid bearer token."},
        503: {
            "description": (
                "mo_geometry package unavailable in this deployment "
                "(set MO_GEOMETRY_PATH / pip install -e packages/geometry). "
                "Package-missing is 503 (not 501); 501 remains reserved for future "
                "unsupported topology/machineType."
            ),
        },
    },
)
def post_geometry_rebuild(
    body: dict[str, Any],
    _: Annotated[str, Depends(require_bearer)],
) -> dict[str, Any]:
    """Sync full recompute; no cache/fixture. Not a Job.

    Request (primary OpenAPI): ``{ topology, machineType?, params }`` per arch
    ``55b1255`` / ``GeometryRebuildRequest`` in openapi-v1.yaml.

    Prefer ``mo_geometry.viewport.rebuild_viewport_payload(body)`` so the 200 body
    includes §2.3 min set **plus** ``paramsHash`` / ``schemaVersion`` / ``meta``
    when present. On ``ImportError`` for viewport helpers, fall back to
    ``normalize_rebuild_params`` + ``rebuild_live_geometry`` (min set only).
    ``ValueError`` → 400. Package missing → 503.
    """
    mode, rebuild_fn = _load_rebuild_fn()

    if mode == "viewport":
        try:
            return rebuild_fn(body)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "bad_request", "message": str(exc)},
            ) from exc

    # Live fallback (pre-viewport / ImportError path — tip e659e0a)
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

    try:
        return rebuild_fn(params)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "bad_request", "message": str(exc)},
        ) from exc
