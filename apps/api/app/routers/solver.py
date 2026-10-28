"""Optional sync analytic solve stub (Q2). Returns 501 — MEC math lives in packages/solver-analytic / Wasm."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict

from app.deps.auth import require_bearer

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


@router.post(
    "/analytic/solve",
    summary="Optional sync analytic solve (Q2 stub → 501)",
)
def post_analytic_solve(
    body: AnalyticSolveRequest,
    _: Annotated[str, Depends(require_bearer)],
) -> None:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "code": "not_implemented",
            "message": (
                "POST /solver/analytic/solve is an optional Q2 stub. "
                "Interactive solve uses client Wasm; batch uses Jobs analytic. "
                "MEC math is not implemented in apps/api."
            ),
            "details": {
                "schema_version": body.schema_version,
                "topology": body.topology,
                "machine_type": body.machine_type,
            },
        },
    )
