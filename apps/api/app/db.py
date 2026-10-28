"""SQLAlchemy engine / session helpers. Optional: falls back when DB unreachable."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, create_engine, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


class TopologyCol(str, PyEnum):
    RF = "RF"
    AF = "AF"


class MachineTypeCol(str, PyEnum):
    BLDC = "BLDC"
    PMSM = "PMSM"
    ACIM = "ACIM"


class ProjectRow(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    topology: Mapped[str] = mapped_column(String(8), nullable=False)
    machine_type: Mapped[str] = mapped_column(String(8), nullable=False)
    mems_schema_version: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


_engine = None
_SessionLocal: sessionmaker[Session] | None = None
_db_ready = False
_db_error: str | None = None


def init_db() -> bool:
    """Try to connect and create tables. Returns True if Postgres is usable."""
    global _engine, _SessionLocal, _db_ready, _db_error
    settings = get_settings()
    try:
        engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,
            pool_size=2,
            max_overflow=0,
        )
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        Base.metadata.create_all(bind=engine)
        _engine = engine
        _SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        _db_ready = True
        _db_error = None
        return True
    except Exception as exc:  # noqa: BLE001 — surface clear connect failure
        _engine = None
        _SessionLocal = None
        _db_ready = False
        _db_error = f"{type(exc).__name__}: {exc}"
        return False


def db_status() -> dict[str, Any]:
    return {
        "ok": _db_ready,
        "error": _db_error,
        "url_host_hint": "127.0.0.1:5433 (host) or postgres:5432 (compose)",
    }


def is_db_ready() -> bool:
    return _db_ready


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    if _SessionLocal is None:
        raise RuntimeError(_db_error or "database not initialized")
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def probe_db() -> dict[str, Any]:
    """Non-fatal probe for /health."""
    if not _db_ready or _engine is None:
        return {"ok": False, "error": _db_error or "not connected"}
    try:
        with _engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"ok": True}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def row_to_dict(row: ProjectRow) -> dict[str, Any]:
    return {
        "id": UUID(row.id),
        "name": row.name,
        "topology": row.topology,
        "machineType": row.machine_type,
        "memsSchemaVersion": row.mems_schema_version,
        "createdAt": row.created_at,
        "updatedAt": row.updated_at,
    }


def db_list_projects() -> list[dict[str, Any]]:
    with session_scope() as s:
        rows = s.scalars(select(ProjectRow).order_by(ProjectRow.created_at)).all()
        return [row_to_dict(r) for r in rows]


def db_get_project(project_id: UUID) -> dict[str, Any] | None:
    with session_scope() as s:
        row = s.get(ProjectRow, str(project_id))
        return row_to_dict(row) if row else None


def db_create_project(
    *,
    name: str,
    topology: str,
    machine_type: str,
    mems_schema_version: str,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    pid = str(uuid4())
    row = ProjectRow(
        id=pid,
        name=name,
        topology=topology,
        machine_type=machine_type,
        mems_schema_version=mems_schema_version,
        created_at=now,
        updated_at=now,
    )
    with session_scope() as s:
        s.add(row)
        s.flush()
        return row_to_dict(row)


def db_update_project(project_id: UUID, fields: dict[str, Any]) -> dict[str, Any] | None:
    with session_scope() as s:
        row = s.get(ProjectRow, str(project_id))
        if row is None:
            return None
        if "name" in fields and fields["name"] is not None:
            row.name = fields["name"]
        if "topology" in fields and fields["topology"] is not None:
            row.topology = fields["topology"]
        if "machineType" in fields and fields["machineType"] is not None:
            row.machine_type = fields["machineType"]
        if "memsSchemaVersion" in fields and fields["memsSchemaVersion"] is not None:
            row.mems_schema_version = fields["memsSchemaVersion"]
        row.updated_at = datetime.now(timezone.utc)
        s.flush()
        return row_to_dict(row)


def db_delete_project(project_id: UUID) -> bool:
    with session_scope() as s:
        row = s.get(ProjectRow, str(project_id))
        if row is None:
            return False
        s.delete(row)
        return True
