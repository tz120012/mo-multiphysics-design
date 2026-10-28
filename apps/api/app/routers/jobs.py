"""Jobs enqueue / poll (Q2-6: optional Celery for analytic)."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.deps.auth import require_bearer
from app.job_dispatch import try_enqueue_analytic
from app.jobs_store import job_create, job_get
from app.schemas.common import Job, JobCreate, JobType

router = APIRouter(
    prefix="/api/v1/jobs",
    tags=["Jobs"],
    dependencies=[Depends(require_bearer)],
)


@router.post(
    "",
    response_model=Job,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue job (analytic: Celery or in-process degrade)",
)
def create_job(
    body: JobCreate,
    _: Annotated[str, Depends(require_bearer)],
) -> Job:
    item = job_create(
        project_id=body.projectId,
        job_type=body.jobType.value,
        payload=body.payload,
        status="queued",
    )
    if body.jobType == JobType.analytic:
        try_enqueue_analytic(item["id"], body.payload)
    # fem / optimize: remain queued placeholders until Q3/Q4
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
