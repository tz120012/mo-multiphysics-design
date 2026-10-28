"""Q5-1: GET /projects/{id}/mems/files/{path} — member read + path safety."""

from __future__ import annotations

import io
import json
import sys
import zipfile
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("CELERY_ENABLED", "0")
    from app.jobs_store import _jobs, _lock as jlock
    from app.mems_store import _mems, _lock as mlock
    from app.store import _projects, _lock as plock

    with jlock:
        _jobs.clear()
    with mlock:
        _mems.clear()
    try:
        with plock:
            _projects.clear()
    except Exception:
        pass

    from app.main import create_app

    app = create_app()
    with TestClient(app) as c:
        yield c


def _auth(c: TestClient) -> dict[str, str]:
    r = c.post("/api/v1/auth/login", json={"username": "t", "password": "t"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['accessToken']}"}


def _create_project(c: TestClient, headers: dict) -> str:
    r = c.post(
        "/api/v1/projects",
        headers=headers,
        json={"name": "q5-1-mems-files", "topology": "RF", "machineType": "PMSM"},
    )
    assert r.status_code in (200, 201), r.text
    body = r.json()
    return body["id"] if "id" in body else body["item"]["id"]


def test_get_mems_file_member_200(client):
    c = client
    headers = _auth(c)
    pid = _create_project(c, headers)

    # Put zip with a known nested member
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "project.json",
            json.dumps(
                {
                    "id": pid,
                    "name": "q5-1",
                    "memsSchemaVersion": "1.0.0",
                    "topology": "RF",
                    "machineType": "PMSM",
                }
            ),
        )
        zf.writestr("geometry/params.json", '{"poleCount":6,"ok":true}\n')
    put = c.put(
        f"/api/v1/projects/{pid}/mems",
        headers={**headers, "Content-Type": "application/zip"},
        content=buf.getvalue(),
    )
    assert put.status_code == 200, put.text

    r = c.get(f"/api/v1/projects/{pid}/mems/files/geometry/params.json", headers=headers)
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("application/json")
    assert r.json() == {"poleCount": 6, "ok": True}
    assert r.headers.get("X-Mo-Mems-Path") == "geometry/params.json"


def test_get_mems_file_missing_member_404(client):
    c = client
    headers = _auth(c)
    pid = _create_project(c, headers)
    # Ensure minimal mems exists via download
    assert c.get(f"/api/v1/projects/{pid}/mems", headers=headers).status_code == 200

    r = c.get(
        f"/api/v1/projects/{pid}/mems/files/does/not/exist.json",
        headers=headers,
    )
    assert r.status_code == 404, r.text
    assert r.json().get("code") == "mems_member_not_found"


def test_get_mems_file_path_traversal_400(client):
    c = client
    headers = _auth(c)
    pid = _create_project(c, headers)
    assert c.get(f"/api/v1/projects/{pid}/mems", headers=headers).status_code == 200

    # httpx/TestClient collapses literal `..` in URLs; use percent-encoding so
    # the path param still reaches normalize_rel_path (same-strict as artifacts).
    for enc in ("..%2Fetc%2Fpasswd", "geometry/%2e%2e/secret.json"):
        r = c.get(f"/api/v1/projects/{pid}/mems/files/{enc}", headers=headers)
        assert r.status_code == 400, (enc, r.text)
        assert r.json().get("code") == "bad_path"


def test_get_mems_file_empty_and_absolute_path_400(client):
    """Arch nit on 8d9fc3b: empty + absolute paths → 400 (same normalize as artifacts)."""
    c = client
    headers = _auth(c)
    pid = _create_project(c, headers)
    assert c.get(f"/api/v1/projects/{pid}/mems", headers=headers).status_code == 200

    # Trailing slash → empty {member_path:path}; %2F… → absolute leading /.
    cases = (
        f"/api/v1/projects/{pid}/mems/files/",
        f"/api/v1/projects/{pid}/mems/files/%2Fetc%2Fpasswd",
        f"/api/v1/projects/{pid}/mems/files/%20",  # whitespace-only → empty after strip
    )
    for url in cases:
        r = c.get(url, headers=headers)
        assert r.status_code == 400, (url, r.text)
        assert r.json().get("code") == "bad_path"


def test_get_mems_file_project_missing_404(client):
    c = client
    headers = _auth(c)
    missing = uuid4()
    r = c.get(f"/api/v1/projects/{missing}/mems/files/project.json", headers=headers)
    assert r.status_code == 404


def test_mems_schema_dual_accept_draft_and_pin(client):
    """Q5-5: PUT accepts 1.0.0-draft; new project meta emits 1.0.0."""
    c = client
    headers = _auth(c)
    pid = _create_project(c, headers)

    # New project should write 1.0.0
    meta_proj = c.get(f"/api/v1/projects/{pid}", headers=headers)
    assert meta_proj.status_code == 200
    assert meta_proj.json()["memsSchemaVersion"] == "1.0.0"

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "project.json",
            json.dumps(
                {
                    "id": pid,
                    "name": "draft-accept",
                    "memsSchemaVersion": "1.0.0-draft",
                }
            ),
        )
    put = c.put(
        f"/api/v1/projects/{pid}/mems",
        headers={**headers, "Content-Type": "application/zip"},
        content=buf.getvalue(),
    )
    assert put.status_code == 200, put.text
    # API meta for new write uses settings → 1.0.0
    assert put.json()["memsSchemaVersion"] == "1.0.0"

    # Reject unknown version
    buf2 = io.BytesIO()
    with zipfile.ZipFile(buf2, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "project.json",
            json.dumps({"id": pid, "name": "bad", "memsSchemaVersion": "9.9.9"}),
        )
    bad = c.put(
        f"/api/v1/projects/{pid}/mems",
        headers={**headers, "Content-Type": "application/zip"},
        content=buf2.getvalue(),
    )
    assert bad.status_code == 400, bad.text
