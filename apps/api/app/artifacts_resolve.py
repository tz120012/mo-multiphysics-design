"""Resolve FEM/optimize thinned artifacts for Jobs GET (F1 / Q3-L4 / Q4-9).

Reads worker disk under MO_OPT_WORKDIR / MO_FEM_WORKDIR (mems-relative layout), optional
embedded job.payload.manifest, and optional .mems zip member. Does not
serve full-field VTU / Elmer .result by default path.
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


def work_roots() -> list[Path]:
    """Resolve roots: MO_OPT_WORKDIR then MO_FEM_WORKDIR (deduped, existing preferred)."""
    seen: set[str] = set()
    out: list[Path] = []
    for key in ("MO_OPT_WORKDIR", "MO_FEM_WORKDIR"):
        raw = os.environ.get(key)
        if not raw:
            continue
        path = Path(raw)
        key_s = str(path.resolve()) if path.exists() else str(path)
        if key_s in seen:
            continue
        seen.add(key_s)
        out.append(path)
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


def load_manifest_from_disk(job_id: str | UUID, job_type: str | None = None) -> dict[str, Any] | None:
    """Try optimize then fem manifest paths (or resultRef-shaped order by jobType)."""
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
    # Always allow the other path as fallback
    for extra in (
        f"solver/optimize/jobs/{jid}/manifest.json",
        f"solver/fem/jobs/{jid}/manifest.json",
    ):
        if extra not in rels:
            rels.append(extra)
    for rel in rels:
        raw = read_disk_bytes(rel)
        if raw is None:
            continue
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        if isinstance(data, dict):
            return data
    return None


def load_manifest(job: dict[str, Any]) -> dict[str, Any] | None:
    """Prefer disk manifest; fall back to payload-embedded (stub / complete_*)."""
    jid = job.get("id")
    if jid is not None:
        disk = load_manifest_from_disk(jid, job.get("jobType") or job.get("job_type"))
        if disk is not None:
            return disk
    # resultRef may point at optimize/fem manifest — try exact rel
    result_ref = job.get("resultRef")
    if isinstance(result_ref, str) and result_ref.endswith("manifest.json"):
        try:
            rel = normalize_rel_path(result_ref)
        except ValueError:
            rel = None
        if rel:
            raw = read_disk_bytes(rel)
            if raw is not None:
                try:
                    data = json.loads(raw.decode("utf-8"))
                    if isinstance(data, dict):
                        return data
                except (UnicodeDecodeError, json.JSONDecodeError):
                    pass
    return embedded_manifest(job)


def read_mems_member(project_id: UUID | None, rel: str) -> bytes | None:
    """Optional: read member from in-memory .mems zip; skip if absent (no big mems change)."""
    if project_id is None:
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
        stored = _mems.get(project_id)
        if stored is None:
            return None
        data = stored.get("data")
    if not data:
        return None
    try:
        with zipfile.ZipFile(BytesIO(data), "r") as zf:
            # zip members may use forward slashes
            names = set(zf.namelist())
            if rel_n in names:
                return zf.read(rel_n)
            # try without leading dirs quirks
            return None
    except (OSError, zipfile.BadZipFile, KeyError):
        return None


def resolve_artifact_bytes(
    job: dict[str, Any],
    rel: str,
) -> tuple[bytes, str] | None:
    """Return (bytes, media_type) or None.

    Order: MO_FEM_WORKDIR disk → embedded manifest.json from payload → mems zip.
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

    pid = job.get("projectId")
    if isinstance(pid, UUID):
        zipped = read_mems_member(pid, rel_n)
        if zipped is not None:
            return zipped, media_type_for(rel_n)

    return None
