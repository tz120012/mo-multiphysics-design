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

# Re-export typed Material schemas (Q2 openapi MaterialCurves)
from app.schemas.materials import Material, MaterialList  # noqa: E402,F401
