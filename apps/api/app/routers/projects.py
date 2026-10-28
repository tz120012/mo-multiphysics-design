"""Project CRUD shell (auth required). Persists to Postgres when available, else memory."""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

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
from app.schemas.project import Project, ProjectCreate, ProjectList, ProjectUpdate
from app.store import mem_create, mem_delete, mem_get, mem_list, mem_update

router = APIRouter(
    prefix="/api/v1/projects",
    tags=["projects"],
    dependencies=[Depends(require_bearer)],
)


def _create(body: ProjectCreate) -> dict[str, Any]:
    settings = get_settings()
    version = body.memsSchemaVersion or settings.mems_schema_version
    kwargs = dict(
        name=body.name,
        topology=body.topology.value,
        machine_type=body.machineType.value,
        mems_schema_version=version,
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


def _patch(project_id: UUID, body: ProjectUpdate) -> dict[str, Any] | None:
    fields = body.model_dump(exclude_unset=True)
    if "topology" in fields and fields["topology"] is not None:
        fields["topology"] = fields["topology"].value
    if "machineType" in fields and fields["machineType"] is not None:
        fields["machineType"] = fields["machineType"].value
    if is_db_ready():
        return db_update_project(project_id, fields)
    return mem_update(project_id, fields)


def _delete(project_id: UUID) -> bool:
    if is_db_ready():
        return db_delete_project(project_id)
    return mem_delete(project_id)


@router.get(
    "",
    response_model=ProjectList,
    summary="List projects",
    description="Return all projects (empty shell store until real persistence expands).",
)
def list_projects(_: Annotated[str, Depends(require_bearer)]) -> ProjectList:
    items = [Project.model_validate(p) for p in _list()]
    return ProjectList(items=items, total=len(items))


@router.post(
    "",
    response_model=Project,
    status_code=status.HTTP_201_CREATED,
    summary="Create project",
    description="Create a project with .mems minimal fields (topology × machineType).",
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
    description="Fetch one project by UUID.",
)
def get_project(
    project_id: UUID,
    _: Annotated[str, Depends(require_bearer)],
) -> Project:
    item = _get(project_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return Project.model_validate(item)


@router.patch(
    "/{project_id}",
    response_model=Project,
    summary="Update project",
    description="Partial update of project metadata fields.",
)
def update_project(
    project_id: UUID,
    body: ProjectUpdate,
    _: Annotated[str, Depends(require_bearer)],
) -> Project:
    item = _patch(project_id, body)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return Project.model_validate(item)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete project",
    description="Delete a project by UUID.",
)
def delete_project(
    project_id: UUID,
    _: Annotated[str, Depends(require_bearer)],
) -> None:
    if not _delete(project_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
