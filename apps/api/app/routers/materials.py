"""Materials list/get thin stubs (Q1; full CRUD → Q2)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.deps.auth import require_bearer
from app.schemas.common import Material, MaterialList

router = APIRouter(
    prefix="/api/v1/materials",
    tags=["Materials"],
    dependencies=[Depends(require_bearer)],
)

_SEED: list[Material] = [
    Material(id="mat-steel-m19", name="M19 Steel", category="steel", meta={"grade": "M19"}),
    Material(id="mat-ndfeb-n42", name="NdFeB N42", category="magnet", meta={"grade": "N42"}),
    Material(id="mat-copper", name="Copper", category="coil", meta={}),
]


@router.get(
    "",
    response_model=MaterialList,
    summary="List materials (Q1 stub)",
)
def list_materials(_: Annotated[str, Depends(require_bearer)]) -> MaterialList:
    return MaterialList(items=list(_SEED))


@router.get(
    "/{material_id}",
    response_model=Material,
    summary="Get material (Q1 stub)",
)
def get_material(
    material_id: str,
    _: Annotated[str, Depends(require_bearer)],
) -> Material:
    for m in _SEED:
        if m.id == material_id:
            return m
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "not_found", "message": "Material not found"},
    )
