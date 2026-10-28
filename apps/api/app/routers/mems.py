"""Mems package download / upload / import / export + member GET (Q5-1).

Boundary: whole-zip I/O and GET .../mems/files/{path} for arbitrary package
members (e.g. geometry/params.json after workdir GC). Thinned FEM/optimize
products stay on Jobs artifacts (L4 / Q4+-3 canonical) — not a /field substitute.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import Response

from app.artifacts_resolve import media_type_for, normalize_rel_path, read_mems_member
from app.config import get_settings
from app.db import db_get_project, is_db_ready
from app.deps.auth import require_bearer
from app.mems_store import mems_get_or_build, mems_put, validate_mems_bytes
from app.schemas.common import MemsMeta
from app.store import mem_get

router = APIRouter(
    prefix="/api/v1/projects",
    tags=["Mems"],
    dependencies=[Depends(require_bearer)],
)


def _get_project(project_id: UUID) -> dict | None:
    if is_db_ready():
        return db_get_project(project_id)
    return mem_get(project_id)


def _require_project(project_id: UUID) -> dict:
    item = _get_project(project_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Project not found"},
        )
    return item


def _zip_response(data: bytes, meta: dict, project_id: UUID) -> Response:
    return Response(
        content=data,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{project_id}.mems"',
            "X-Mems-Schema-Version": str(meta.get("memsSchemaVersion", "")),
        },
    )


def _download_mems(project_id: UUID) -> Response:
    """Shared GET /mems and /mems/export download path."""
    project = _require_project(project_id)
    data, meta = mems_get_or_build(project_id, project)
    return _zip_response(data, meta, project_id)


def _put_mems_bytes(project_id: UUID, data: bytes) -> MemsMeta:
    """Shared PUT /mems and POST /mems/import validation + store."""
    _require_project(project_id)
    try:
        validate_mems_bytes(data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "bad_request", "message": str(exc)},
        ) from exc
    settings = get_settings()
    meta = mems_put(project_id, data, settings.mems_schema_version)
    return MemsMeta.model_validate(meta)


@router.get(
    "/{project_id}/mems",
    summary="Download .mems package",
    response_class=Response,
)
def download_mems(
    project_id: UUID,
    _: Annotated[str, Depends(require_bearer)],
) -> Response:
    return _download_mems(project_id)


@router.put(
    "/{project_id}/mems",
    response_model=MemsMeta,
    summary="Upload / replace .mems package",
)
async def upload_mems(
    project_id: UUID,
    request: Request,
    _: Annotated[str, Depends(require_bearer)],
) -> MemsMeta:
    content_type = (request.headers.get("content-type") or "").lower()
    if "multipart/form-data" in content_type:
        form = await request.form()
        file = form.get("file")
        if file is None or not hasattr(file, "read"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "bad_request", "message": "multipart field 'file' required"},
            )
        data = await file.read()  # type: ignore[union-attr]
    else:
        data = await request.body()
    return _put_mems_bytes(project_id, data)


@router.post(
    "/{project_id}/mems/import",
    response_model=MemsMeta,
    summary="Import .mems into project",
)
async def import_mems(
    project_id: UUID,
    _: Annotated[str, Depends(require_bearer)],
    file: UploadFile = File(...),
) -> MemsMeta:
    data = await file.read()
    return _put_mems_bytes(project_id, data)


@router.get(
    "/{project_id}/mems/export",
    summary="Export .mems (download alias)",
    response_class=Response,
)
def export_mems(
    project_id: UUID,
    _: Annotated[str, Depends(require_bearer)],
) -> Response:
    return _download_mems(project_id)


@router.get(
    "/{project_id}/mems/files/{member_path:path}",
    summary="Get one .mems zip member by relative path (Q5-1)",
    response_class=Response,
)
def get_mems_file(
    project_id: UUID,
    member_path: str,
    _: Annotated[str, Depends(require_bearer)],
) -> Response:
    """Serve bytes of one zip member from the project's stored `.mems`.

    Path is zip-relative; reject `..`, absolute, or empty (400). Missing
    project / mems / member → 404. Content-Type inferred from extension;
    unknown → application/octet-stream.

    Not a replacement for Jobs artifacts thinned FEM/optimize (/field) channel.
    """
    project = _require_project(project_id)
    try:
        rel = normalize_rel_path(member_path)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "bad_path", "message": str(exc)},
        ) from exc

    # Ensure a zip exists (minimal build if never uploaded) so default members
    # like geometry/params.json are readable after project create.
    mems_get_or_build(project_id, project)
    data = read_mems_member(project_id, rel)
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "mems_member_not_found",
                "message": f"Member not found in project .mems: {rel}",
            },
        )
    return Response(
        content=data,
        media_type=media_type_for(rel),
        headers={"X-Mo-Mems-Path": rel},
    )
