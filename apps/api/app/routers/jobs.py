"""Jobs enqueue / poll (Q2-6 analytic; Q3 fem Celery / in-process degrade).

L4: GET artifacts list + single-file (F1 worker disk / resultRef; thinned only).
"""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from pydantic import ValidationError

from app.artifacts_resolve import (
    load_manifest,
    media_type_for,
    normalize_rel_path,
    resolve_artifact_bytes,
)
from app.deps.auth import require_bearer
from app.job_dispatch import try_enqueue_analytic, try_enqueue_fem
from app.jobs_store import job_create, job_get
from app.schemas.common import (
    FemArtifact,
    FemJobPayload,
    Job,
    JobArtifactsList,
    JobCreate,
    JobType,
)

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


def _require_job(job_id: UUID) -> dict[str, Any]:
    item = job_get(job_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Job not found"},
        )
    return item


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
    item = _require_job(job_id)
    return Job.model_validate(item)


@router.get(
    "/{job_id}/artifacts",
    response_model=JobArtifactsList,
    summary="List thinned FEM artifacts (F1; from manifest)",
)
def list_job_artifacts(
    job_id: UUID,
    _: Annotated[str, Depends(require_bearer)],
) -> JobArtifactsList:
    """Return artifacts[] from job manifest.

    Prefer disk under MO_FEM_WORKDIR (mems_shadow / mems layout); else
    payload-embedded manifest (stub). Job missing → 404 not_found.
    Manifest unlocatable → 404 manifest_not_found.
    Stub dry-run with artifacts=[] → 200 + empty list (not an error).
    """
    job = _require_job(job_id)
    manifest = load_manifest(job)
    if manifest is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "manifest_not_found",
                "message": (
                    "No FEM manifest on worker disk or in job payload; "
                    "set MO_FEM_WORKDIR (shared volume) or wait for succeeded FEM job"
                ),
            },
        )
    raw_arts = manifest.get("artifacts") or []
    artifacts: list[FemArtifact] = []
    if isinstance(raw_arts, list):
        for a in raw_arts:
            if not isinstance(a, dict):
                continue
            try:
                artifacts.append(FemArtifact.model_validate(a))
            except ValidationError:
                continue
    return JobArtifactsList(
        jobId=job_id,
        resultRef=job.get("resultRef"),
        artifacts=artifacts,
    )


@router.get(
    "/{job_id}/artifacts/{artifact_path:path}",
    summary="Get one thinned artifact by mems-relative path (F1)",
    response_class=Response,
)
def get_job_artifact(
    job_id: UUID,
    artifact_path: str,
    _: Annotated[str, Depends(require_bearer)],
) -> Response:
    """Serve file bytes for a mems-relative path (e.g. results/fem/{id}/slice.gltf).

    Resolution: MO_FEM_WORKDIR/mems_shadow/{rel} → MO_FEM_WORKDIR/{rel} →
    payload-embedded manifest.json → optional mems zip member.
    Path traversal (`..`) rejected. Full-field VTU is not the default path.
    """
    job = _require_job(job_id)
    try:
        rel = normalize_rel_path(artifact_path)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "bad_path", "message": str(exc)},
        ) from exc

    try:
        resolved = resolve_artifact_bytes(job, rel)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "bad_path", "message": str(exc)},
        ) from exc

    if resolved is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "artifact_not_found",
                "message": (
                    f"Artifact not found: {rel}. "
                    "Needs MO_FEM_WORKDIR shared volume / mems member, "
                    "or embedded manifest.json for that path alone."
                ),
            },
        )
    body, media = resolved
    return Response(
        content=body,
        media_type=media or media_type_for(rel),
        headers={"X-Mo-Artifact-Path": rel},
    )
