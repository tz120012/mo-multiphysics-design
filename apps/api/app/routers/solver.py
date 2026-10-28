"""Optional sync analytic solve (Q2): thin wrap of packages/solver-analytic."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict

from app.deps.auth import require_bearer

router = APIRouter(
    prefix="/api/v1/solver",
    tags=["Solver"],
    dependencies=[Depends(require_bearer)],
)

_REPO_ROOT = Path(__file__).resolve().parents[4]
_SOLVER_PKG = _REPO_ROOT / "packages" / "solver-analytic"
if _SOLVER_PKG.is_dir() and str(_SOLVER_PKG) not in sys.path:
    sys.path.insert(0, str(_SOLVER_PKG))


class AnalyticSolveRequest(BaseModel):
    """Mirror of packages/solver-analytic SolveRequest; not a second FE DTO."""

    model_config = ConfigDict(extra="allow")

    schema_version: str
    topology: str
    machine_type: str
    geometry: dict[str, Any]
    materials: dict[str, Any]
    operating_point: dict[str, Any]


def _load_solve():
    try:
        from solve import solve as _solve  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "solver_unavailable",
                "message": f"packages/solver-analytic not importable: {exc}",
                "details": {"path": str(_SOLVER_PKG)},
            },
        ) from exc
    return _solve


@router.post(
    "/analytic/solve",
    summary="Sync analytic solve (Python golden)",
)
def post_analytic_solve(
    body: AnalyticSolveRequest,
    _: Annotated[str, Depends(require_bearer)],
    solver: Annotated[str | None, Query(description="mec|mock; default mec")] = None,
) -> dict[str, Any]:
    solve_fn = _load_solve()
    payload = body.model_dump()
    kind = (solver or payload.get("solver") or "mec").strip().lower()
    try:
        return solve_fn(payload, solver=kind)
    except NotImplementedError as exc:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={"code": "not_implemented", "message": str(exc)},
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "invalid_request", "message": str(exc)},
        ) from exc
    except Exception as exc:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "solve_failed", "message": str(exc)},
        ) from exc
