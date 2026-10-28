"""Q1-5 轴向 AF-PMSM 测试；非 PMSM 仅枚举预留。"""

from __future__ import annotations

import copy

from mo_geometry import (
    GEOMETRY_SCHEMA_VERSION,
    build_axial_mesh_descriptor,
    default_axial_af_pmsm,
    to_mems_axial_fragment,
    validate_axial,
)
from mo_geometry.constants import GEOMETRY_SCHEMA_VERSION as SV
from mo_geometry.units import default_units


def test_default_af_pmsm_validates():
    for cfg in ("RFMR", "FRMF"):
        p = default_axial_af_pmsm(config=cfg)
        assert validate_axial(p) == []


def test_invalid_dims_fail():
    p = default_axial_af_pmsm()
    p["pmsm"]["outerDiameter"] = 10.0
    p["pmsm"]["magnetSectorAngle"] = 200
    errs = validate_axial(p)
    assert any("outerDiameter" in e for e in errs)
    assert any("magnetSectorAngle" in e for e in errs)


def test_af_non_pmsm_enum_reserve_no_full_tree():
    # 允许枚举预留，无 pmsm 树
    reserved = {
        "schemaVersion": SV,
        "topology": "AF",
        "machineType": "BLDC",
        "config": "RFMR",
        "units": default_units(),
    }
    assert validate_axial(reserved) == []

    # 若展开完整树则失败
    bad = copy.deepcopy(reserved)
    bad["pmsm"] = default_axial_af_pmsm()["pmsm"]
    errs = validate_axial(bad)
    assert any("enum-reserved" in e or "pmsm:" in e for e in errs)

    reserved_acim = {**reserved, "machineType": "ACIM"}
    assert validate_axial(reserved_acim) == []


def test_af_pmsm_requires_tree():
    p = default_axial_af_pmsm()
    del p["pmsm"]
    errs = validate_axial(p)
    assert any("pmsm:" in e for e in errs)


def test_mems_and_mesh():
    p = default_axial_af_pmsm(config="FRMF")
    frag = to_mems_axial_fragment(p)
    assert frag["schemaVersion"] == GEOMETRY_SCHEMA_VERSION
    assert frag["topology"] == "AF"

    mesh = build_axial_mesh_descriptor(p)
    assert mesh["kind"] == "axial"
    assert mesh["meta"]["diskCount"] == p["pmsm"]["diskCount"]
    disks = [x for x in mesh["primitives"] if "disk" in x["name"]]
    assert len(disks) == p["pmsm"]["diskCount"]

    # slot count changes descriptor
    q = copy.deepcopy(p)
    q["pmsm"]["slotCount"] = p["pmsm"]["slotCount"] + 6
    m2 = build_axial_mesh_descriptor(q)
    marks1 = [x for x in mesh["primitives"] if x["name"].startswith("stator_slot_mark_")]
    marks2 = [x for x in m2["primitives"] if x["name"].startswith("stator_slot_mark_")]
    assert len(marks2) > len(marks1)


def test_non_pmsm_mesh_empty_primitives():
    reserved = {
        "schemaVersion": SV,
        "topology": "AF",
        "machineType": "BLDC",
        "config": "RFMR",
        "units": default_units(),
    }
    mesh = build_axial_mesh_descriptor(reserved)
    assert mesh["primitives"] == []
