"""Jobs enqueue / poll thin stubs (Q1; body → Q2/Q3)."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.deps.auth import require_bearer
from app.jobs_store import job_create, job_get
from app.schemas.common import Job, JobCreate

router = APIRouter(
    prefix="/api/v1/jobs",
    tags=["Jobs"],
    dependencies=[Depends(require_bearer)],
)


@router.post(
    "",
    response_model=Job,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue job stub",
)
def create_job(
    body: JobCreate,
    _: Annotated[str, Depends(require_bearer)],
) -> Job:
    item = job_create(
        project_id=body.projectId,
        job_type=body.jobType.value,
        payload=body.payload,
    )
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
