"""Materials library API (Q2-1): seed + list/get/filter; optional POST custom."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.deps.auth import require_bearer
from app.materials_store import materials_create, materials_get, materials_list
from app.schemas.common import Material, MaterialList

router = APIRouter(
    prefix="/api/v1/materials",
    tags=["Materials"],
    dependencies=[Depends(require_bearer)],
)


class MaterialCreate(BaseModel):
    name: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1, description="steel | magnet | coil | acim_bar")
    meta: dict[str, Any] | None = None
    id: str | None = Field(None, description="Optional explicit id; auto-generated if omitted")


@router.get(
    "",
    response_model=MaterialList,
    summary="List materials (Q2 seed; optional category filter)",
)
def list_materials(
    _: Annotated[str, Depends(require_bearer)],
    category: Annotated[
        str | None,
        Query(description="Filter by category: steel | magnet | coil | acim_bar"),
    ] = None,
) -> MaterialList:
    items = materials_list(category=category)
    return MaterialList(items=[Material.model_validate(m) for m in items])


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
    return Material.model_validate(item)


@router.post(
    "",
    response_model=Material,
    status_code=status.HTTP_201_CREATED,
    summary="Create custom material (Bearer)",
)
def create_material(
    body: MaterialCreate,
    _: Annotated[str, Depends(require_bearer)],
) -> Material:
    try:
        item = materials_create(
            name=body.name,
            category=body.category,
            meta=body.meta,
            material_id=body.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "conflict", "message": str(exc)},
        ) from exc
    return Material.model_validate(item)
