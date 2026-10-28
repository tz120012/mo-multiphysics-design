"""Resolve FEM/optimize thinned artifacts for Jobs GET (F1 / L4 / Q4+-3).

Canonical single-file channel for thinned FEM/optimize products (Q4+-3 / Motor F5=A):
GET /jobs/{id}/artifacts and .../artifacts/{path}. Whole-zip mems stays package I/O;
GET .../mems/files/{path} is deferred (Q4+-3b).

Resolve order: MO_OPT/FEM workdir mems_shadow → workdir → payload embed → optional
project .mems zip member (read_mems_member). Does not serve full-field VTU by default.
"""

from __future__ import annotations

import json
import os
import zipfile
from io import BytesIO
from pathlib import Path, PurePosixPath
from typing import Any
from uuid import UUID

# Content types for thinned F1 artifacts (not full-field VTK).
_MEDIA_TYPES: dict[str, str] = {
    ".json": "application/json",
    ".gltf": "model/gltf+json",
    ".glb": "model/gltf-binary",
    ".png": "image/png",
    ".webp": "image/webp",
}


def normalize_rel_path(raw: str) -> str:
    """Normalize mems-relative path; reject empty, absolute, or `..` traversal."""
    s = (raw or "").strip().replace("\\", "/")
    if not s or s.startswith("/"):
        raise ValueError("invalid artifact path")
    parts = PurePosixPath(s).parts
    if ".." in parts or any(p == "" for p in parts):
        raise ValueError("path traversal rejected")
    # Collapse . and normalize
    norm = PurePosixPath(*[p for p in parts if p != "."])
    out = str(norm)
    if not out or out.startswith("..") or "/../" in f"/{out}/":
        raise ValueError("path traversal rejected")
    return out


def media_type_for(path: str) -> str:
    ext = Path(path).suffix.lower()
    return _MEDIA_TYPES.get(ext, "application/octet-stream")


def fem_workdir() -> Path | None:
    """Backward-compatible single root (FEM). Prefer work_roots() for resolve."""
    root = os.environ.get("MO_FEM_WORKDIR")
    if not root:
        return None
    return Path(root)


# Defaults aligned with tasks/optimize.py (_work_root → /tmp/mo-opt) and tasks/fem.py (/tmp/mo-fem).
# Used when MO_OPT_WORKDIR / MO_FEM_WORKDIR are unset (in-process CELERY_ENABLED=0).
DEFAULT_OPT_WORKDIR = Path("/tmp/mo-opt")
DEFAULT_FEM_WORKDIR = Path("/tmp/mo-fem")


def work_roots() -> list[Path]:
    """Resolve roots: MO_OPT_WORKDIR then MO_FEM_WORKDIR; else /tmp/mo-opt + /tmp/mo-fem.

    Env roots win when set. With no env (compose api historically omitted workdir),
    fall back to the same defaults writers use so artifacts GET finds in-process files.
    Fallback dirs are included when they exist or are creatable.
    """
    seen: set[str] = set()
    out: list[Path] = []

    def _add(path: Path) -> None:
        key_s = str(path.resolve()) if path.exists() else str(path)
        if key_s in seen:
            return
        seen.add(key_s)
        out.append(path)

    for key in ("MO_OPT_WORKDIR", "MO_FEM_WORKDIR"):
        raw = os.environ.get(key)
        if not raw:
            continue
        _add(Path(raw))
    if out:
        return out
    for path in (DEFAULT_OPT_WORKDIR, DEFAULT_FEM_WORKDIR):
        try:
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
        except OSError:
            if not path.exists():
                continue
        _add(path)
    return out


def _is_under(root: Path, candidate: Path) -> bool:
    try:
        candidate.resolve().relative_to(root.resolve())
        return True
    except (ValueError, OSError):
        return False


def candidate_disk_paths(rel: str, work_root: Path) -> list[Path]:
    """F1 resolution order under MO_FEM_WORKDIR."""
    rel_n = normalize_rel_path(rel)
    out: list[Path] = [
        work_root / "mems_shadow" / rel_n,
        work_root / rel_n,
    ]
    # If rel already starts with solver/ or results/, also try as-is under root
    # (covered by work_root/rel). Extra: work_root/solver/... when rel embeds solver.
    if rel_n.startswith("solver/") or rel_n.startswith("results/"):
        pass
    else:
        out.append(work_root / "solver" / rel_n)
    return out


def read_disk_bytes(rel: str) -> bytes | None:
    roots = work_roots()
    if not roots:
        # Fall back to legacy fem_workdir only
        root = fem_workdir()
        roots = [root] if root is not None else []
    try:
        for root in roots:
            for cand in candidate_disk_paths(rel, root):
                if not cand.is_file():
                    continue
                if not _is_under(root, cand):
                    continue
                return cand.read_bytes()
    except (OSError, ValueError):
        return None
    return None


def embedded_manifest(job: dict[str, Any]) -> dict[str, Any] | None:
    payload = job.get("payload")
    if not isinstance(payload, dict):
        return None
    man = payload.get("manifest")
    if isinstance(man, dict) and "artifacts" in man:
        return man
    return None


def _manifest_rel_candidates(job_id: str | UUID, job_type: str | None = None) -> list[str]:
    jid = str(job_id)
    rels: list[str] = []
    if job_type == "optimize":
        rels.append(f"solver/optimize/jobs/{jid}/manifest.json")
    elif job_type == "fem":
        rels.append(f"solver/fem/jobs/{jid}/manifest.json")
    else:
        rels.extend(
            [
                f"solver/optimize/jobs/{jid}/manifest.json",
                f"solver/fem/jobs/{jid}/manifest.json",
            ]
        )
    for extra in (
        f"solver/optimize/jobs/{jid}/manifest.json",
        f"solver/fem/jobs/{jid}/manifest.json",
    ):
        if extra not in rels:
            rels.append(extra)
    return rels


def _parse_manifest_bytes(raw: bytes) -> dict[str, Any] | None:
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def load_manifest_from_disk(job_id: str | UUID, job_type: str | None = None) -> dict[str, Any] | None:
    """Try optimize then fem manifest paths (or resultRef-shaped order by jobType)."""
    for rel in _manifest_rel_candidates(job_id, job_type):
        raw = read_disk_bytes(rel)
        if raw is None:
            continue
        parsed = _parse_manifest_bytes(raw)
        if parsed is not None:
            return parsed
    return None


def load_manifest_from_mems(
    job: dict[str, Any],
    job_id: str | UUID | None = None,
    job_type: str | None = None,
) -> dict[str, Any] | None:
    """Optional: read manifest.json from stored project `.mems` zip (Q4+-3 zip fallback)."""
    pid = job.get("projectId")
    jid = job_id if job_id is not None else job.get("id")
    if jid is None:
        return None
    jt = job_type if job_type is not None else (job.get("jobType") or job.get("job_type"))
    rels = _manifest_rel_candidates(jid, jt)
    result_ref = job.get("resultRef")
    if isinstance(result_ref, str) and result_ref.endswith("manifest.json"):
        try:
            rel = normalize_rel_path(result_ref)
        except ValueError:
            rel = None
        if rel and rel not in rels:
            rels.insert(0, rel)
    for rel in rels:
        raw = read_mems_member(pid, rel)
        if raw is None:
            continue
        parsed = _parse_manifest_bytes(raw)
        if parsed is not None:
            return parsed
    return None


def load_manifest(job: dict[str, Any]) -> dict[str, Any] | None:
    """Prefer disk; then optional .mems zip member; then payload-embedded (stub)."""
    jid = job.get("id")
    jt = job.get("jobType") or job.get("job_type")
    if jid is not None:
        disk = load_manifest_from_disk(jid, jt)
        if disk is not None:
            return disk
    # resultRef may point at optimize/fem manifest — try exact rel on disk
    result_ref = job.get("resultRef")
    if isinstance(result_ref, str) and result_ref.endswith("manifest.json"):
        try:
            rel = normalize_rel_path(result_ref)
        except ValueError:
            rel = None
        if rel:
            raw = read_disk_bytes(rel)
            if raw is not None:
                parsed = _parse_manifest_bytes(raw)
                if parsed is not None:
                    return parsed
    zipped = load_manifest_from_mems(job, jid, jt)
    if zipped is not None:
        return zipped
    return embedded_manifest(job)


def _as_project_uuid(project_id: UUID | str | None) -> UUID | None:
    """Coerce job.projectId (UUID or str) for mems zip lookup."""
    if project_id is None:
        return None
    if isinstance(project_id, UUID):
        return project_id
    try:
        return UUID(str(project_id))
    except (ValueError, TypeError, AttributeError):
        return None


def read_mems_member(project_id: UUID | str | None, rel: str) -> bytes | None:
    """Optional: read member from stored project `.mems` zip when disk miss.

    Used by Jobs artifacts GET (Q4+-3); does not add a public mems/files route.
    """
    pid = _as_project_uuid(project_id)
    if pid is None:
        return None
    try:
        from app.mems_store import _lock, _mems  # noqa: PLC0415 — optional path
    except ImportError:
        return None
    try:
        rel_n = normalize_rel_path(rel)
    except ValueError:
        return None
    with _lock:
        stored = _mems.get(pid)
        if stored is None:
            return None
        data = stored.get("data")
    if not data:
        return None
    try:
        with zipfile.ZipFile(BytesIO(data), "r") as zf:
            names = set(zf.namelist())
            # Exact mems-relative path first; tolerate leading "./" in zip writers
            candidates = (rel_n, f"./{rel_n}")
            for name in candidates:
                if name in names:
                    return zf.read(name)
            return None
    except (OSError, zipfile.BadZipFile, KeyError):
        return None


def resolve_artifact_bytes(
    job: dict[str, Any],
    rel: str,
) -> tuple[bytes, str] | None:
    """Return (bytes, media_type) or None.

    Order: MO_OPT/FEM workdir mems_shadow → workdir → payload embed → optional .mems zip.
    """
    try:
        rel_n = normalize_rel_path(rel)
    except ValueError as exc:
        raise ValueError(str(exc)) from exc

    disk = read_disk_bytes(rel_n)
    if disk is not None:
        return disk, media_type_for(rel_n)

    # Embedded manifest.json itself may be serialized from payload
    if rel_n == f"solver/fem/jobs/{job.get('id')}/manifest.json" or rel_n.endswith(
        f"/jobs/{job.get('id')}/manifest.json"
    ):
        man = embedded_manifest(job)
        if man is not None:
            body = (json.dumps(man, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
            return body, "application/json"
    # Also accept resultRef exact match
    result_ref = job.get("resultRef")
    if isinstance(result_ref, str) and rel_n == normalize_rel_path(result_ref):
        man = embedded_manifest(job)
        if man is not None:
            body = (json.dumps(man, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
            return body, "application/json"

    pid = _as_project_uuid(job.get("projectId"))
    if pid is not None:
        zipped = read_mems_member(pid, rel_n)
        if zipped is not None:
            return zipped, media_type_for(rel_n)

    return None
