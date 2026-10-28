"""Material schemas aligned to openapi-v1 Material / MaterialCurves (Q2 tip 3c34f1c)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator


MATERIALS_SCHEMA_VERSION = "0.1.0-q2"


class MaterialCategory(str, Enum):
    steel = "steel"
    magnet = "magnet"
    coil = "coil"
    acim_bar = "acim_bar"


class CurveTable2D(BaseModel):
    xName: str
    yName: str
    xUnit: str | None = None
    yUnit: str | None = None
    points: list[list[float]] = Field(..., min_length=2)
    note: str | None = None


class SteelProps(BaseModel):
    bh: CurveTable2D | None = None
    bp: CurveTable2D | None = None
    lossCoefficients: dict[str, Any] | None = None


class MagnetDemagEntry(BaseModel):
    temperature_c: float | None = None
    curve: CurveTable2D


class MagnetProps(BaseModel):
    br_t: float
    hc_a_per_m: float
    demag: list[MagnetDemagEntry] | None = Field(None, min_length=1)
    alphaBr: float | None = None
    alphaHc: float | None = None


class CoilProps(BaseModel):
    resistivity_ohm_m: float = Field(..., gt=0)
    fillFactor: float | None = Field(None, ge=0, le=1)
    skin: dict[str, Any] | None = None


class AcimBarProps(BaseModel):
    conductivity_s_per_m: float = Field(..., gt=0)
    skin: dict[str, Any] | None = None


class MaterialCurves(BaseModel):
    steel: SteelProps | None = None
    magnet: MagnetProps | None = None
    coil: CoilProps | None = None
    acim_bar: AcimBarProps | None = None

    def branch_for(self, category: MaterialCategory | str) -> Any:
        cat = MaterialCategory(category) if not isinstance(category, MaterialCategory) else category
        return getattr(self, cat.value, None)


def _require_category_branch(curves: MaterialCurves, category: MaterialCategory) -> None:
    branch = curves.branch_for(category)
    if branch is None:
        raise ValueError(f"curves.{category.value} is required for category={category.value}")
    if category == MaterialCategory.steel:
        if branch.bh is None and branch.bp is None:
            raise ValueError("curves.steel requires bh and/or bp")
    elif category == MaterialCategory.magnet:
        if branch.demag is None or len(branch.demag) < 1:
            # OpenAPI requires br_t/hc; demag recommended (>=1). Allow without demag for thin custom.
            pass
    # coil / acim_bar required fields enforced by pydantic


class Material(BaseModel):
    id: str
    name: str
    category: MaterialCategory
    builtin: bool
    materialsSchemaVersion: str = MATERIALS_SCHEMA_VERSION
    curves: MaterialCurves | None = None
    meta: dict[str, Any] | None = None
    deletedAt: datetime | None = None
    createdAt: datetime | None = None
    updatedAt: datetime | None = None


class MaterialList(BaseModel):
    items: list[Material]


class MaterialCreate(BaseModel):
    id: str | None = None
    name: str = Field(..., min_length=1)
    category: MaterialCategory
    curves: MaterialCurves
    meta: dict[str, Any] | None = None
    materialsSchemaVersion: str = MATERIALS_SCHEMA_VERSION

    @model_validator(mode="after")
    def _check_curves(self) -> MaterialCreate:
        if self.materialsSchemaVersion != MATERIALS_SCHEMA_VERSION:
            raise ValueError(f"materialsSchemaVersion must be {MATERIALS_SCHEMA_VERSION}")
        _require_category_branch(self.curves, self.category)
        return self


class MaterialUpdate(BaseModel):
    name: str = Field(..., min_length=1)
    category: MaterialCategory
    curves: MaterialCurves
    meta: dict[str, Any] | None = None
    materialsSchemaVersion: str = MATERIALS_SCHEMA_VERSION

    @model_validator(mode="after")
    def _check_curves(self) -> MaterialUpdate:
        if self.materialsSchemaVersion != MATERIALS_SCHEMA_VERSION:
            raise ValueError(f"materialsSchemaVersion must be {MATERIALS_SCHEMA_VERSION}")
        _require_category_branch(self.curves, self.category)
        return self
