"""Jobs enqueue / poll (Q2-6 analytic; Q3 fem; Q4 drive/optimize).

L4: GET artifacts list + single-file (F1 worker disk / resultRef; thinned only).
Optimize: Celery queue `optimize` or in-process daemon — never NSGA on request thread.
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
from app.job_dispatch import (
    try_enqueue_analytic,
    try_enqueue_drive,
    try_enqueue_fem,
    try_enqueue_optimize,
)
from app.jobs_store import job_create, job_get, job_update
from app.schemas.common import (
    DriveJobPayload,
    FemArtifact,
    FemJobPayload,
    Job,
    JobArtifactsList,
    JobCreate,
    JobType,
    OptimizeJobPayload,
)

router = APIRouter(
    prefix="/api/v1/jobs",
    tags=["Jobs"],
    dependencies=[Depends(require_bearer)],
)


def _validation_http(message: str, exc: ValidationError) -> HTTPException:
    missing = []
    for err in exc.errors():
        loc = ".".join(str(x) for x in err.get("loc", ()))
        if err.get("type") == "missing":
            missing.append(loc or "?")
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={
            "code": "validation_error",
            "message": message,
            "details": {
                "missing": missing,
                "errors": exc.errors(),
            },
        },
    )


def _validate_fem_payload(payload: dict[str, Any] | None) -> FemJobPayload:
    """Progressive required-field check; 422 on missing/invalid FemJobPayload fields."""
    try:
        return FemJobPayload.model_validate(payload or {})
    except ValidationError as exc:
        raise _validation_http("FemJobPayload validation failed", exc) from exc


def _validate_drive_payload(payload: dict[str, Any] | None) -> DriveJobPayload:
    """Require mode + machineType; 422 on missing/invalid DriveJobPayload fields."""
    try:
        return DriveJobPayload.model_validate(payload or {})
    except ValidationError as exc:
        raise _validation_http("DriveJobPayload validation failed", exc) from exc


def _validate_optimize_payload(payload: dict[str, Any] | None) -> OptimizeJobPayload:
    """Require variables/objectives/nsga/evaluatorProfile (baseSolveRequest optional)."""
    try:
        return OptimizeJobPayload.model_validate(payload or {})
    except ValidationError as exc:
        raise _validation_http("OptimizeJobPayload validation failed", exc) from exc


def _require_job(job_id: UUID) -> dict[str, Any]:
    item = job_get(job_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Job not found"},
        )
    return item


def _artifact_from_manifest_entry(a: dict[str, Any]) -> FemArtifact | None:
    """Map solver-opt `kind` → FemArtifact.role when role absent."""
    data = dict(a)
    if "role" not in data and "kind" in data:
        data["role"] = str(data["kind"])
    if "format" not in data:
        path = str(data.get("path") or "")
        if path.endswith(".json"):
            data["format"] = "json"
        elif path.endswith(".gltf"):
            data["format"] = "gltf"
        else:
            data["format"] = "bin"
    try:
        return FemArtifact.model_validate(data)
    except ValidationError:
        return None


@router.post(
    "",
    response_model=Job,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue job (analytic/fem/drive/optimize: Celery or in-process degrade)",
)
def create_job(
    body: JobCreate,
    _: Annotated[str, Depends(require_bearer)],
) -> Job:
    if body.jobType == JobType.fem:
        _validate_fem_payload(body.payload)
    elif body.jobType == JobType.drive:
        _validate_drive_payload(body.payload)
    elif body.jobType == JobType.optimize:
        _validate_optimize_payload(body.payload)

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
    elif body.jobType == JobType.drive:
        try_enqueue_drive(item["id"], body.payload)
    elif body.jobType == JobType.optimize:
        try_enqueue_optimize(item["id"], body.payload)
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


@router.post(
    "/{job_id}/cancel",
    response_model=Job,
    summary="Cancel job (idempotent; optimize/fem/drive/analytic)",
)
def cancel_job(
    job_id: UUID,
    _: Annotated[str, Depends(require_bearer)],
) -> Job:
    """Mark job cancelled. Idempotent 200 if already cancelled.

    Worker checks status between phases; in-flight NSGA may still finish writing
    but will not flip succeeded after cancel wins the store update race.
    """
    item = _require_job(job_id)
    st = item.get("status")
    if st == "cancelled":
        return Job.model_validate(item)
    if st in ("succeeded", "failed"):
        # Already terminal: leave status; 200 with current job (late cancel is no-op).
        return Job.model_validate(item)
    updated = job_update(job_id, status="cancelled")
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Job not found"},
        )
    return Job.model_validate(updated)


@router.get(
    "/{job_id}/artifacts",
    response_model=JobArtifactsList,
    summary="List thinned artifacts (F1; from FEM/optimize manifest)",
)
def list_job_artifacts(
    job_id: UUID,
    _: Annotated[str, Depends(require_bearer)],
) -> JobArtifactsList:
    """Return artifacts[] from job manifest.

    Prefer disk under MO_OPT_WORKDIR / MO_FEM_WORKDIR (mems_shadow / mems layout); else
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
                    "No manifest on worker disk or in job payload; "
                    "set MO_OPT_WORKDIR / MO_FEM_WORKDIR (shared volume) or wait for succeeded job"
                ),
            },
        )
    raw_arts = manifest.get("artifacts") or []
    artifacts: list[FemArtifact] = []
    if isinstance(raw_arts, list):
        for a in raw_arts:
            if not isinstance(a, dict):
                continue
            art = _artifact_from_manifest_entry(a)
            if art is not None:
                artifacts.append(art)
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
    """Serve file bytes for a mems-relative path (e.g. results/optimize/{id}/pareto.json).

    Resolution: workdir/mems_shadow/{rel} → workdir/{rel} →
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
                    "Needs MO_OPT_WORKDIR / MO_FEM_WORKDIR shared volume / mems member, "
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
