"""Shared response / auth / stub schemas (openapi-v1)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class Health(BaseModel):
    status: str = Field(..., examples=["ok"])
    version: str | None = None
    time: datetime | None = None


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    accessToken: str
    tokenType: str = "Bearer"


class MeResponse(BaseModel):
    id: str
    username: str
    displayName: str | None = None


class MemsMeta(BaseModel):
    projectId: UUID
    memsSchemaVersion: str
    sizeBytes: int = Field(..., ge=0)
    checksumSha256: str
    updatedAt: datetime


class HistoryEntry(BaseModel):
    id: str
    commandType: str
    summary: str
    createdAt: datetime
    payload: dict[str, Any] | None = None


class HistoryList(BaseModel):
    entries: list[HistoryEntry]
    cursor: int


class HistoryCursorResponse(BaseModel):
    cursor: int
    entry: HistoryEntry


# Re-export for older imports.


class JobType(str, Enum):
    analytic = "analytic"
    fem = "fem"
    optimize = "optimize"
    drive = "drive"


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"


class FemJobPayload(BaseModel):
    """Q3 FEM job payload — aligns packages/solver-fem/api/fem-job-payload.schema.json."""

    topology: str = Field(..., pattern="^(RF|AF)$")
    machineType: str = Field(..., pattern="^(BLDC|PMSM|ACIM)$")
    dim: str = Field(..., pattern="^(2d|3d)$")
    solverKernel: str = Field(..., pattern="^(elmer|getdp)$")
    meshProfile: str = Field(..., min_length=1)
    operatingPoint: dict[str, Any]
    # Materials stay typed as object|array (Q2 materials / .mems) — no reshape.
    materials: dict[str, Any] | list[Any]
    projectId: UUID | None = None
    templateId: str | None = None



class DriveJobPayload(BaseModel):
    """Q4 drive job payload — packages/solver-drive (single-case or efficiency_map)."""

    mode: str = Field(
        ...,
        pattern="^(bldc_square|pmsm_foc|acim_vf|acim_foc|efficiency_map)$",
    )
    machineType: str = Field(..., pattern="^(BLDC|PMSM|ACIM)$")
    operatingPoint: dict[str, Any] = Field(default_factory=dict)
    pwm: dict[str, Any] | None = None
    deadTime: dict[str, Any] | None = None
    plant: dict[str, Any] | None = None
    mapGrid: dict[str, Any] | None = None
    mapMode: str | None = None
    nSamples: int | None = None
    projectId: UUID | None = None



class OptimizeNsgaParams(BaseModel):
    """NSGA-II control knobs (packages/solver-opt api schema)."""

    popSize: int = Field(..., ge=2, le=64)
    generations: int = Field(..., ge=1, le=100)
    seed: int


class OptimizeVariable(BaseModel):
    model_config = {"extra": "allow"}

    id: str
    bounds: list[float] = Field(..., min_length=2, max_length=2)
    path: str | None = None
    type: str | None = None


class OptimizeObjective(BaseModel):
    model_config = {"extra": "allow"}

    id: str
    sense: str = Field(..., pattern="^(minimize|maximize)$")
    metricId: str


class OptimizeJobPayload(BaseModel):
    """Q4-9 optimize payload — packages/solver-opt/api/optimize-job-payload.schema.json.

    baseSolveRequest is optional at enqueue: worker fills seed42 fixture default when omitted.
    """

    model_config = {"extra": "allow"}

    variables: list[OptimizeVariable] = Field(..., min_length=1)
    objectives: list[OptimizeObjective] = Field(..., min_length=2)
    nsga: OptimizeNsgaParams
    evaluatorProfile: str = Field(
        ...,
        pattern=r"^(analytic|analytic\+drive|analytic\+fem)$",
    )
    baseSolveRequest: dict[str, Any] | None = None
    constraints: list[dict[str, Any]] | None = None
    memsRef: str | None = None
    projectId: UUID | None = None


class FemArtifact(BaseModel):
    """Thinned FEM artifact pointer (F1; relative to .mems root)."""

    path: str
    role: str
    format: str
    bytes: int | None = None


class JobArtifactsList(BaseModel):
    """GET /jobs/{jobId}/artifacts response."""

    jobId: UUID
    resultRef: str | None = None
    artifacts: list[FemArtifact] = Field(default_factory=list)


class JobCreate(BaseModel):
    projectId: UUID
    jobType: JobType
    payload: dict[str, Any] | None = None


class Job(BaseModel):
    id: UUID
    projectId: UUID
    jobType: JobType
    status: JobStatus
    resultRef: str | None = None
    error: ErrorBody | None = None
    createdAt: datetime
    updatedAt: datetime | None = None
    # Drive/analytic may embed input+result for FE poll (not in minimal OpenAPI Job)
    payload: dict[str, Any] | None = None

# Re-export typed Material schemas (Q2 openapi MaterialCurves)
from app.schemas.materials import Material, MaterialList  # noqa: E402,F401
