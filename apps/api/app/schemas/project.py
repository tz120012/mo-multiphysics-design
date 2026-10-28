"""Project schemas aligned with openapi-v1.yaml / .mems project.json."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class Topology(str, Enum):
    """Magnetic topology: radial (RF) or axial (AF)."""

    RF = "RF"
    AF = "AF"


class MachineType(str, Enum):
    """Machine type enum (ACIM is first-class)."""

    BLDC = "BLDC"
    PMSM = "PMSM"
    ACIM = "ACIM"


class ProjectCreate(BaseModel):
    """Create / full-replace (PUT) project body (OpenAPI ProjectCreate)."""

    name: str = Field(..., min_length=1, max_length=200, description="Display name")
    topology: Topology = Field(..., description="RF | AF")
    machineType: MachineType = Field(..., description="BLDC | PMSM | ACIM")
    units: dict[str, Any] | None = Field(
        default=None,
        description="Optional units object (stored client-side in .mems; accepted on create)",
    )


class ProjectUpdate(BaseModel):
    """Partial update for PATCH compatibility."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    topology: Topology | None = None
    machineType: MachineType | None = None
    memsSchemaVersion: str | None = None


class Project(BaseModel):
    """Project resource (.mems project.json minimal set)."""

    id: UUID = Field(..., description="Stable project UUID")
    name: str
    topology: Topology
    machineType: MachineType
    memsSchemaVersion: str
    createdAt: datetime
    updatedAt: datetime

    model_config = {"from_attributes": True}


class ProjectList(BaseModel):
    """List wrapper for projects."""

    items: list[Project]
    total: int
