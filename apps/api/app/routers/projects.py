"""Project CRUD aligned with openapi-v1 (PUT primary; PATCH kept for compat)."""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.config import get_settings
from app.db import (
    db_create_project,
    db_delete_project,
    db_get_project,
    db_list_projects,
    db_update_project,
    is_db_ready,
)
from app.deps.auth import require_bearer
from app.mems_store import mems_delete
from app.schemas.project import Project, ProjectCreate, ProjectList, ProjectUpdate
from app.store import mem_create, mem_delete, mem_get, mem_list, mem_update

router = APIRouter(
    prefix="/api/v1/projects",
    tags=["Projects"],
    dependencies=[Depends(require_bearer)],
)


def _not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "not_found", "message": "Project not found"},
    )


def _create(body: ProjectCreate) -> dict[str, Any]:
    settings = get_settings()
    kwargs = dict(
        name=body.name,
        topology=body.topology.value,
        machine_type=body.machineType.value,
        mems_schema_version=settings.mems_schema_version,
    )
    if is_db_ready():
        return db_create_project(**kwargs)
    return mem_create(**kwargs)


def _list() -> list[dict[str, Any]]:
    if is_db_ready():
        return db_list_projects()
    return mem_list()


def _get(project_id: UUID) -> dict[str, Any] | None:
    if is_db_ready():
        return db_get_project(project_id)
    return mem_get(project_id)


def _apply_fields(project_id: UUID, fields: dict[str, Any]) -> dict[str, Any] | None:
    if is_db_ready():
        return db_update_project(project_id, fields)
    return mem_update(project_id, fields)


def _put(project_id: UUID, body: ProjectCreate) -> dict[str, Any] | None:
    fields = {
        "name": body.name,
        "topology": body.topology.value,
        "machineType": body.machineType.value,
    }
    return _apply_fields(project_id, fields)


def _patch(project_id: UUID, body: ProjectUpdate) -> dict[str, Any] | None:
    fields = body.model_dump(exclude_unset=True)
    if "topology" in fields and fields["topology"] is not None:
        fields["topology"] = fields["topology"].value
    if "machineType" in fields and fields["machineType"] is not None:
        fields["machineType"] = fields["machineType"].value
    return _apply_fields(project_id, fields)


def _delete(project_id: UUID) -> bool:
    ok = db_delete_project(project_id) if is_db_ready() else mem_delete(project_id)
    if ok:
        mems_delete(project_id)
    return ok


@router.get(
    "",
    response_model=ProjectList,
    summary="List projects",
)
def list_projects(
    _: Annotated[str, Depends(require_bearer)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ProjectList:
    all_items = _list()
    total = len(all_items)
    page = all_items[offset : offset + limit]
    items = [Project.model_validate(p) for p in page]
    return ProjectList(items=items, total=total)


@router.post(
    "",
    response_model=Project,
    status_code=status.HTTP_201_CREATED,
    summary="Create project",
)
def create_project(
    body: ProjectCreate,
    _: Annotated[str, Depends(require_bearer)],
) -> Project:
    return Project.model_validate(_create(body))


@router.get(
    "/{project_id}",
    response_model=Project,
    summary="Get project",
)
def get_project(
    project_id: UUID,
    _: Annotated[str, Depends(require_bearer)],
) -> Project:
    item = _get(project_id)
    if item is None:
        raise _not_found()
    return Project.model_validate(item)


@router.put(
    "/{project_id}",
    response_model=Project,
    summary="Update project metadata (full replace of ProjectCreate fields)",
)
def put_project(
    project_id: UUID,
    body: ProjectCreate,
    _: Annotated[str, Depends(require_bearer)],
) -> Project:
    item = _put(project_id, body)
    if item is None:
        raise _not_found()
    return Project.model_validate(item)


@router.patch(
    "/{project_id}",
    response_model=Project,
    summary="Partial update (compat; OpenAPI prefers PUT)",
    deprecated=True,
)
def patch_project(
    project_id: UUID,
    body: ProjectUpdate,
    _: Annotated[str, Depends(require_bearer)],
) -> Project:
    item = _patch(project_id, body)
    if item is None:
        raise _not_found()
    return Project.model_validate(item)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete project",
)
def delete_project(
    project_id: UUID,
    _: Annotated[str, Depends(require_bearer)],
) -> None:
    if not _delete(project_id):
        raise _not_found()
