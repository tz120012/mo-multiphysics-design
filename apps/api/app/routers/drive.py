"""Optional sync drive solve — single operating point only (not efficiency_map)."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from app.deps.auth import require_bearer
router = APIRouter(
    prefix="/api/v1/drive",
    tags=["Drive"],
    dependencies=[Depends(require_bearer)],
)


class DriveSolveRequest(BaseModel):
    """Single-case drive preview; rejects efficiency_map."""

    model_config = ConfigDict(extra="allow")

    mode: str = Field(..., pattern="^(bldc_square|pmsm_foc|acim_vf|acim_foc)$")
    machineType: str = Field(..., pattern="^(BLDC|PMSM|ACIM)$")
    operatingPoint: dict[str, Any] = Field(default_factory=dict)
    pwm: dict[str, Any] | None = None
    deadTime: dict[str, Any] | None = None
    plant: dict[str, Any] | None = None
    nSamples: int | None = None


def _import_run_case():
    solver_path = os.environ.get("SOLVER_DRIVE_PATH")
    if not solver_path:
        repo_root = Path(__file__).resolve().parents[4]
        solver_path = str(repo_root / "packages" / "solver-drive")
    sp = Path(solver_path).resolve()
    if not (sp / "solve.py").is_file():
        raise FileNotFoundError(f"solver-drive not found under {sp}")
    if str(sp) not in sys.path:
        sys.path.insert(0, str(sp))
    from solve import run_drive_case  # type: ignore[import-not-found]

    return run_drive_case


@router.post(
    "/solve",
    summary="Sync single-case drive preview (not efficiency_map; maps use Jobs)",
)
def drive_solve(
    body: DriveSolveRequest,
    _: Annotated[str, Depends(require_bearer)],
) -> dict[str, Any]:
    if body.mode == "efficiency_map":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "map_requires_jobs",
                "message": "efficiency_map must use POST /api/v1/jobs with jobType=drive",
            },
        )
    try:
        run_case = _import_run_case()
        return run_case(body.model_dump(exclude_none=True))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "drive_bad_request", "message": str(exc)},
        ) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "drive_failed", "message": str(exc)},
        ) from exc
