"""Q1-4 / Q1-7 径向参数与网格描述测试。"""

from __future__ import annotations

import copy

from mo_geometry import (
    GEOMETRY_SCHEMA_VERSION,
    build_radial_mesh_descriptor,
    default_radial_acim,
    default_radial_bldc,
    default_radial_pmsm,
    to_mems_radial_fragment,
    validate_radial,
)


def _hard_errors(msgs: list[str]) -> list[str]:
    return [m for m in msgs if not m.startswith("warning:")]


def test_defaults_validate_clean():
    for builder in (default_radial_bldc, default_radial_pmsm, default_radial_acim):
        params = builder()
        errs = _hard_errors(validate_radial(params))
        assert errs == [], f"{builder.__name__}: {errs}"


def test_invalid_dims_fail():
    p = default_radial_pmsm()
    p["stator"]["outerDiameter"] = 10.0  # < ID
    p["airgap"] = -1
    errs = _hard_errors(validate_radial(p))
    assert any("outerDiameter" in e for e in errs)
    assert any("airgap" in e for e in errs)


def test_skewed_requires_angle():
    p = default_radial_bldc()
    p["stator"]["slotShape"] = "skewed"
    p["stator"]["skewAngle"] = None
    errs = _hard_errors(validate_radial(p))
    assert any("skewAngle" in e for e in errs)


def test_acim_block_required_when_acim():
    p = default_radial_acim()
    del p["acim"]
    errs = _hard_errors(validate_radial(p))
    assert any(e.startswith("acim:") for e in errs)

    # optional when not ACIM
    p2 = default_radial_pmsm()
    assert "acim" not in p2
    assert _hard_errors(validate_radial(p2)) == []


def test_acim_slot_fit_warning():
    p = default_radial_acim()
    p["stator"]["slotCount"] = 35  # not divisible by 2*cagePolePairs (default 4)
    msgs = validate_radial(p)
    hard = _hard_errors(msgs)
    assert hard == [], hard
    assert any("slotFit" in m for m in msgs)


def test_mems_fragment_stable_schema():
    frag = to_mems_radial_fragment(default_radial_pmsm())
    assert frag["schemaVersion"] == GEOMETRY_SCHEMA_VERSION
    assert frag["topology"] == "RF"
    assert "stator" in frag and "rotor" in frag


def test_mesh_descriptor_reacts_to_slot_count():
    a = default_radial_pmsm()
    b = copy.deepcopy(a)
    b["stator"]["slotCount"] = a["stator"]["slotCount"] + 6
    # keep airgap fit
    da = build_radial_mesh_descriptor(a)
    db = build_radial_mesh_descriptor(b)
    assert da["schemaVersion"]
    assert da["kind"] == "radial"
    assert da["meta"]["slotCount"] != db["meta"]["slotCount"]
    teeth_a = [p for p in da["primitives"] if p["name"].startswith("stator_tooth_")]
    teeth_b = [p for p in db["primitives"] if p["name"].startswith("stator_tooth_")]
    assert len(teeth_a) == a["stator"]["slotCount"]
    assert len(teeth_b) == b["stator"]["slotCount"]
    assert len(teeth_a) != len(teeth_b)


def test_mesh_reacts_to_od():
    a = default_radial_bldc()
    b = copy.deepcopy(a)
    b["stator"]["outerDiameter"] = a["stator"]["outerDiameter"] + 20
    da = build_radial_mesh_descriptor(a)
    db = build_radial_mesh_descriptor(b)
    yoke_a = next(p for p in da["primitives"] if p["name"] == "stator_yoke")
    yoke_b = next(p for p in db["primitives"] if p["name"] == "stator_yoke")
    assert yoke_b["outerRadius"] > yoke_a["outerRadius"]
