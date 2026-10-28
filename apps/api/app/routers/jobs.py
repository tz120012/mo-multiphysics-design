"""Jobs enqueue / poll (Q2-6 analytic; Q3 fem Celery / in-process degrade)."""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError

from app.deps.auth import require_bearer
from app.job_dispatch import try_enqueue_analytic, try_enqueue_fem
from app.jobs_store import job_create, job_get
from app.schemas.common import FemJobPayload, Job, JobCreate, JobType

router = APIRouter(
    prefix="/api/v1/jobs",
    tags=["Jobs"],
    dependencies=[Depends(require_bearer)],
)


def _validate_fem_payload(payload: dict[str, Any] | None) -> FemJobPayload:
    """Progressive required-field check; 422 on missing/invalid FemJobPayload fields."""
    try:
        return FemJobPayload.model_validate(payload or {})
    except ValidationError as exc:
        missing = []
        for err in exc.errors():
            loc = ".".join(str(x) for x in err.get("loc", ()))
            if err.get("type") == "missing":
                missing.append(loc or "?")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": "FemJobPayload validation failed",
                "details": {
                    "missing": missing,
                    "errors": exc.errors(),
                },
            },
        ) from exc


@router.post(
    "",
    response_model=Job,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue job (analytic/fem: Celery or in-process degrade; optimize placeholder)",
)
def create_job(
    body: JobCreate,
    _: Annotated[str, Depends(require_bearer)],
) -> Job:
    if body.jobType == JobType.fem:
        _validate_fem_payload(body.payload)

    item = job_create(
        project_id=body.projectId,
        job_type=body.jobType.value,
        payload=body.payload,
        status="queued",
    )
    if body.jobType == JobType.analytic:
        try_enqueue_analytic(item["id"], body.payload)
    elif body.jobType == JobType.fem:
        try_enqueue_fem(item["id"], body.payload)
    # optimize: remain queued placeholder until Q4
    return Job.model_validate(item)


@router.get(
    "/{job_id}",
    response_model=Job,
    summary="Poll job status",
)
def get_job(
    job_id: UUID,
    _: Annotated[str, Depends(require_bearer)],
) -> Job:
    item = job_get(job_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Job not found"},
        )
    return Job.model_validate(item)
