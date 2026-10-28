"""Materials library API (Q2-1): typed curves CRUD; builtin seed read-only."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.deps.auth import require_bearer
from app.materials_store import (
    materials_create,
    materials_get,
    materials_list,
    materials_replace,
    materials_soft_delete,
)
from app.schemas.materials import (
    Material,
    MaterialCreate,
    MaterialList,
    MaterialUpdate,
)

router = APIRouter(
    prefix="/api/v1/materials",
    tags=["Materials"],
    dependencies=[Depends(require_bearer)],
)


def _to_model(item: dict[str, Any]) -> Material:
    return Material.model_validate(item)


@router.get(
    "",
    response_model=MaterialList,
    summary="List materials (Q2-1; seed + custom)",
)
def list_materials(
    _: Annotated[str, Depends(require_bearer)],
    category: Annotated[
        str | None,
        Query(description="Filter by category: steel | magnet | coil | acim_bar"),
    ] = None,
    includeDeleted: Annotated[
        bool,
        Query(description="Include soft-deleted custom materials"),
    ] = False,
) -> MaterialList:
    items = materials_list(category=category, include_deleted=includeDeleted)
    return MaterialList(items=[_to_model(m) for m in items])


@router.get(
    "/{material_id}",
    response_model=Material,
    summary="Get material by id",
)
def get_material(
    material_id: str,
    _: Annotated[str, Depends(require_bearer)],
) -> Material:
    item = materials_get(material_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Material not found"},
        )
    return _to_model(item)


@router.post(
    "",
    response_model=Material,
    status_code=status.HTTP_201_CREATED,
    summary="Create custom material (builtin forced false)",
)
def create_material(
    body: MaterialCreate,
    _: Annotated[str, Depends(require_bearer)],
) -> Material:
    try:
        item = materials_create(
            name=body.name,
            category=body.category.value,
            curves=body.curves.model_dump(exclude_none=True),
            meta=body.meta,
            material_id=body.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "conflict", "message": str(exc)},
        ) from exc
    return _to_model(item)


@router.put(
    "/{material_id}",
    response_model=Material,
    summary="Replace custom material (builtin → 403)",
)
def put_material(
    material_id: str,
    body: MaterialUpdate,
    _: Annotated[str, Depends(require_bearer)],
) -> Material:
    try:
        item = materials_replace(
            material_id,
            name=body.name,
            category=body.category.value,
            curves=body.curves.model_dump(exclude_none=True),
            meta=body.meta,
        )
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Material not found"},
        ) from None
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "forbidden", "message": str(exc)},
        ) from exc
    return _to_model(item)


@router.delete(
    "/{material_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete custom material (builtin → 403)",
    response_class=Response,
)
def delete_material(
    material_id: str,
    _: Annotated[str, Depends(require_bearer)],
) -> Response:
    try:
        materials_soft_delete(material_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Material not found"},
        ) from None
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "forbidden", "message": str(exc)},
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
