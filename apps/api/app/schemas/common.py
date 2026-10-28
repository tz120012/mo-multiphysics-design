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


class Material(BaseModel):
    id: str
    name: str
    category: str
    meta: dict[str, Any] | None = None


class MaterialList(BaseModel):
    items: list[Material]


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
