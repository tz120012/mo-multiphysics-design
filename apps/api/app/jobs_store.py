"""In-memory jobs stub store (Q1 thin stub)."""

from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from typing import Any
from uuid import UUID, uuid4

_lock = Lock()
_jobs: dict[UUID, dict[str, Any]] = {}


def job_create(*, project_id: UUID, job_type: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    jid = uuid4()
    item = {
        "id": jid,
        "projectId": project_id,
        "jobType": job_type,
        "status": "queued",
        "resultRef": None,
        "error": None,
        "createdAt": now,
        "updatedAt": now,
        "payload": payload,
    }
    with _lock:
        _jobs[jid] = item
        return dict(item)


def job_get(job_id: UUID) -> dict[str, Any] | None:
    with _lock:
        item = _jobs.get(job_id)
        return dict(item) if item else None
