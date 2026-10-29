"""Q6/D1: POST /api/v1/geometry/rebuild — thin wrap of rebuild_live_geometry."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

API_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = API_ROOT.parents[1]
EXAMPLES = REPO_ROOT / "packages" / "geometry" / "examples"

if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

# Ensure mo_geometry importable in test env (editable or src path)
_geo_src = REPO_ROOT / "packages" / "geometry" / "src"
if _geo_src.is_dir() and str(_geo_src) not in sys.path:
    sys.path.insert(0, str(_geo_src))


@pytest.fixture()
def client():
    from app.main import create_app

    app = create_app()
    with TestClient(app) as c:
        yield c


def _auth(c: TestClient) -> dict[str, str]:
    r = c.post("/api/v1/auth/login", json={"username": "t", "password": "t"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['accessToken']}"}


def _load_example(name: str) -> dict:
    path = EXAMPLES / name
    assert path.is_file(), f"missing gold example {path}"
    return json.loads(path.read_text())


def test_rebuild_fe_envelope_rf_pmsm_200(client):
    """Primary FE shape: { topology, machineType, params }."""
    c = client
    headers = _auth(c)
    params = _load_example("radial_pmsm_params.json")
    r = c.post(
        "/api/v1/geometry/rebuild",
        headers=headers,
        json={"topology": "RF", "machineType": "PMSM", "params": params},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "params" in body
    assert "meshDescriptor" in body
    assert "geometrySummary" in body
    md = body["meshDescriptor"]
    assert isinstance(md, dict)
    for key in ("schemaVersion", "kind", "units", "primitives"):
        assert key in md, f"meshDescriptor missing {key}"
    gs = body["geometrySummary"]
    for key in ("poles", "slots", "stack_length_m", "airgap_m", "rotor_od_m", "stator_id_m"):
        assert key in gs
    assert "pipelineEntry" not in body


def test_rebuild_fe_envelope_af_pmsm_pipeline_entry(client):
    c = client
    headers = _auth(c)
    params = _load_example("axial_af_pmsm_rfmr_params.json")
    r = c.post(
        "/api/v1/geometry/rebuild",
        headers=headers,
        json={"topology": "AF", "machineType": "PMSM", "params": params},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "meshDescriptor" in body and "primitives" in body["meshDescriptor"]
    assert "geometrySummary" in body
    assert "pipelineEntry" in body
    assert isinstance(body["pipelineEntry"], dict)


def test_rebuild_bare_params_root_alternate(client):
    c = client
    headers = _auth(c)
    params = _load_example("radial_pmsm_creator_4p6s_params.json")
    r = c.post("/api/v1/geometry/rebuild", headers=headers, json=params)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "meshDescriptor" in body and "geometrySummary" in body


def test_rebuild_nested_params_only_unwrap(client):
    c = client
    headers = _auth(c)
    params = _load_example("radial_pmsm_params.json")
    r = c.post(
        "/api/v1/geometry/rebuild",
        headers=headers,
        json={"params": params},
    )
    assert r.status_code == 200, r.text
    assert "meshDescriptor" in r.json()


def test_rebuild_bad_topology_400(client):
    c = client
    headers = _auth(c)
    r = c.post(
        "/api/v1/geometry/rebuild",
        headers=headers,
        json={"topology": "XX", "params": {"schemaVersion": "0.1.0-q1"}},
    )
    assert r.status_code == 400, r.text
    assert r.json().get("code") == "bad_request"


def test_rebuild_invalid_rf_params_400(client):
    c = client
    headers = _auth(c)
    r = c.post(
        "/api/v1/geometry/rebuild",
        headers=headers,
        json={
            "topology": "RF",
            "machineType": "PMSM",
            "params": {"topology": "RF", "machineType": "PMSM"},
        },
    )
    assert r.status_code == 400, r.text


def test_rebuild_unauthorized_401(client):
    c = client
    params = _load_example("radial_pmsm_params.json")
    r = c.post(
        "/api/v1/geometry/rebuild",
        json={"topology": "RF", "machineType": "PMSM", "params": params},
    )
    assert r.status_code == 401


def test_fem_payload_accepts_geometry_summary(client):
    """Jobs FEM still enqueues when payload carries rebuild geometrySummary."""
    from uuid import uuid4

    c = client
    headers = _auth(c)
    payload = {
        "topology": "RF",
        "machineType": "PMSM",
        "dim": "2d",
        "solverKernel": "elmer",
        "meshProfile": "rf_pmsm_2d_default",
        "operatingPoint": {"rpm": 1000},
        "materials": {"magnet": "N42"},
        "geometrySummary": {
            "poles": 6,
            "slots": 18,
            "stack_length_m": 0.025,
            "airgap_m": 0.0005,
            "rotor_od_m": 0.05,
            "stator_id_m": 0.051,
        },
        "uemExtraHint": {"note": "forward-compat"},
    }
    r = c.post(
        "/api/v1/jobs",
        headers=headers,
        json={
            "projectId": str(uuid4()),
            "jobType": "fem",
            "payload": payload,
        },
    )
    assert r.status_code == 202, r.text


def test_rebuild_topology_mismatch_400(client):
    c = client
    headers = _auth(c)
    params = _load_example("radial_pmsm_params.json")
    r = c.post(
        "/api/v1/geometry/rebuild",
        headers=headers,
        json={"topology": "AF", "machineType": "PMSM", "params": params},
    )
    assert r.status_code == 400, r.text
