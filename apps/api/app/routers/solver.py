"""Optional sync analytic solve — thin wrapper around packages/solver-analytic."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.deps.auth import require_bearer

# mo-platform/packages/solver-analytic
_REPO_ROOT = Path(__file__).resolve().parents[4]
_SOLVER_PKG = _REPO_ROOT / "packages" / "solver-analytic"
if _SOLVER_PKG.is_dir() and str(_SOLVER_PKG) not in sys.path:
    sys.path.insert(0, str(_SOLVER_PKG))

router = APIRouter(
    prefix="/api/v1/solver",
    tags=["Solver"],
    dependencies=[Depends(require_bearer)],
)


class AnalyticSolveRequest(BaseModel):
    """Mirror of packages/solver-analytic SolveRequest (snake_case); not a second FE DTO."""

    model_config = ConfigDict(extra="allow")

    schema_version: str
    topology: str
    machine_type: str
    geometry: dict[str, Any]
    materials: dict[str, Any]
    operating_point: dict[str, Any]
    materials_catalog: dict[str, Any] | list[Any] | None = None
    solver: Literal["mec", "mock"] | None = None


def _load_solve():
    try:
        from solve import solve as analytic_solve  # type: ignore
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "solver_unavailable",
                "message": f"packages/solver-analytic not importable: {exc}",
                "details": {"path": str(_SOLVER_PKG)},
            },
        ) from exc
    return analytic_solve


@router.post(
    "/analytic/solve",
    summary="Sync analytic solve (Python golden via packages/solver-analytic)",
)
def post_analytic_solve(
    body: AnalyticSolveRequest,
    _: Annotated[str, Depends(require_bearer)],
    solver: Literal["mec", "mock"] | None = Query(
        default=None,
        description="Override solver; default mec (or body.solver)",
    ),
) -> dict[str, Any]:
    """Call Python ``solve()``. Query ``solver=mec|mock`` wins over body.solver."""
    analytic_solve = _load_solve()
    req = body.model_dump(exclude_none=True)
    kind = (solver or req.get("solver") or "mec").strip().lower()
    if kind not in ("mec", "mock"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": f"solver must be mec|mock, got {kind!r}",
            },
        )
    try:
        return analytic_solve(req, solver=kind)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "bad_request", "message": str(exc)},
        ) from exc
    except NotImplementedError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "not_implemented", "message": str(exc)},
        ) from exc
    except Exception as exc:  # noqa: BLE001 — surface as 400 for solve failures
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "solve_error", "message": str(exc)},
        ) from exc
