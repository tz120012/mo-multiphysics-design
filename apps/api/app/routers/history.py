"""History list / undo / redo stubs (Q1-6)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.db import db_get_project, is_db_ready
from app.deps.auth import require_bearer
from app.schemas.common import HistoryCursorResponse, HistoryEntry, HistoryList
from app.store import mem_get

router = APIRouter(
    prefix="/api/v1/projects",
    tags=["History"],
    dependencies=[Depends(require_bearer)],
)


def _require_project(project_id: UUID) -> None:
    item = db_get_project(project_id) if is_db_ready() else mem_get(project_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Project not found"},
        )


def _placeholder_entry() -> HistoryEntry:
    return HistoryEntry(
        id="stub-0",
        commandType="noop",
        summary="Q1 history stub (empty)",
        createdAt=datetime.now(timezone.utc),
        payload={},
    )


@router.get(
    "/{project_id}/history",
    response_model=HistoryList,
    summary="List history entries (Q1-6 stub)",
)
def list_history(
    project_id: UUID,
    _: Annotated[str, Depends(require_bearer)],
) -> HistoryList:
    _require_project(project_id)
    return HistoryList(entries=[], cursor=0)


@router.post(
    "/{project_id}/history/undo",
    response_model=HistoryCursorResponse,
    summary="Undo stub (Q1-6)",
)
def history_undo(
    project_id: UUID,
    _: Annotated[str, Depends(require_bearer)],
) -> HistoryCursorResponse:
    _require_project(project_id)
    return HistoryCursorResponse(cursor=0, entry=_placeholder_entry())


@router.post(
    "/{project_id}/history/redo",
    response_model=HistoryCursorResponse,
    summary="Redo stub (Q1-6)",
)
def history_redo(
    project_id: UUID,
    _: Annotated[str, Depends(require_bearer)],
) -> HistoryCursorResponse:
    _require_project(project_id)
    return HistoryCursorResponse(cursor=0, entry=_placeholder_entry())
