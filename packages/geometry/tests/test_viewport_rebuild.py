"""Q6：rebuild_viewport_payload 契约 + 参数→mesh 一致性矩阵。"""

from __future__ import annotations

import copy

import pytest

from mo_geometry import (
    creator_radial_pmsm_4p6s,
    default_axial_af_pmsm,
    default_radial_acim,
    default_radial_bldc,
    default_radial_pmsm,
    params_hash,
    rebuild_live_geometry,
    rebuild_viewport_payload,
    unwrap_rebuild_params,
)
from mo_geometry.constants import GEOMETRY_SCHEMA_VERSION


def _magnet_sectors(mesh: dict) -> list[dict]:
    return [
        p
        for p in mesh["primitives"]
        if p["type"] == "sector" and ("magnet" in p["name"])
    ]


def _tooth_sectors(mesh: dict) -> list[dict]:
    return [
        p
        for p in mesh["primitives"]
        if p["type"] == "sector" and ("tooth" in p["name"] or "slot_mark" in p["name"])
    ]


def _min_set_keys() -> set[str]:
    """Arch tip 55b1255 §2.3 / rebuild_live_geometry."""
    return {"params", "meshDescriptor", "geometrySummary"}


def _superset_extra_rf() -> set[str]:
    return {
        "schemaVersion",
        "topology",
        "machineType",
        "paramsHash",
        "meta",
    }


# ---------------------------------------------------------------------------
# Envelope shape / hash
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "factory",
    [default_radial_bldc, default_radial_pmsm, default_radial_acim, creator_radial_pmsm_4p6s],
)
def test_viewport_envelope_rf_shape(factory):
    p = factory()
    env = rebuild_viewport_payload(p)
    assert _min_set_keys() <= set(env.keys())
    assert _superset_extra_rf() <= set(env.keys())
    assert "pipelineEntry" not in env
    assert env["schemaVersion"] == GEOMETRY_SCHEMA_VERSION
    assert env["topology"] == "RF"
    assert env["machineType"] == p["machineType"]
    assert env["meta"]["rebuildPolicy"] == "full"
    assert len(env["paramsHash"]) == 16
    assert env["paramsHash"] == params_hash(env["params"])
    live = rebuild_live_geometry(p)
    assert env["meshDescriptor"] == live["meshDescriptor"]
    assert env["geometrySummary"] == live["geometrySummary"]
    # 超集 ⊇ 金标最小集
    for k in _min_set_keys():
        assert env[k] == live[k]


def test_viewport_envelope_af_includes_pipeline():
    af = default_axial_af_pmsm(config="RFMR")
    env = rebuild_viewport_payload(af)
    assert env["topology"] == "AF"
    assert env["machineType"] == "PMSM"
    assert "pipelineEntry" in env
    assert env["meta"]["rebuildPolicy"] == "full"
    assert env["pipelineEntry"]["geometrySummary"] == env["geometrySummary"]


def test_unwrap_arch_envelope_primary():
    """权威 Request：{ topology, machineType?, params } @ tip 55b1255 §2.2。"""
    rf = default_radial_pmsm()
    envelope = {
        "topology": "RF",
        "machineType": "PMSM",
        "params": rf,
    }
    unwrapped = unwrap_rebuild_params(envelope)
    assert unwrapped["topology"] == "RF"
    assert unwrapped["machineType"] == "PMSM"
    env = rebuild_viewport_payload(envelope)
    assert env["topology"] == "RF"
    assert _min_set_keys() <= set(env.keys())
    live = rebuild_live_geometry(rf)
    assert env["meshDescriptor"] == live["meshDescriptor"]
    # 包内便利：根对象仍可用
    assert unwrap_rebuild_params(rf) is rf
    bare_wrap = unwrap_rebuild_params({"params": rf})
    assert bare_wrap["topology"] == "RF"


def test_unwrap_topology_mismatch_raises():
    rf = default_radial_pmsm()
    with pytest.raises(ValueError, match="topology mismatch"):
        unwrap_rebuild_params({"topology": "AF", "params": rf})


def test_same_params_same_hash_and_descriptor():
    rf = default_radial_pmsm()
    a = rebuild_viewport_payload(rf)
    b = rebuild_viewport_payload(copy.deepcopy(rf))
    assert a["paramsHash"] == b["paramsHash"]
    assert a["meshDescriptor"] == b["meshDescriptor"]
    assert a["geometrySummary"] == b["geometrySummary"]


def test_different_params_different_hash():
    a = default_radial_pmsm()
    b = copy.deepcopy(a)
    b["stator"]["slotCount"] = int(a["stator"]["slotCount"]) + 6
    ha = rebuild_viewport_payload(a)["paramsHash"]
    hb = rebuild_viewport_payload(b)["paramsHash"]
    assert ha != hb


def test_meta_excluded_from_hash():
    a = creator_radial_pmsm_4p6s()
    b = copy.deepcopy(a)
    b["meta"] = {"source": "noise-only-change", "extra": 1}
    # meta 不进 hash；几何字段相同 → hash 相同
    assert params_hash(a) == params_hash(b)


def test_no_cache_sequential_param_changes():
    p = default_radial_pmsm()
    e1 = rebuild_viewport_payload(p)
    p2 = copy.deepcopy(p)
    # 保持气隙配合：SID ≈ ROD + 2*airgap
    p2["airgap"] = float(p["airgap"]) + 0.3
    p2["stator"]["innerDiameter"] = float(p2["rotor"]["outerDiameter"]) + 2.0 * float(p2["airgap"])
    e2 = rebuild_viewport_payload(p2)
    p3 = copy.deepcopy(p2)
    p3["stator"]["slotCount"] = int(p2["stator"]["slotCount"]) + 6
    e3 = rebuild_viewport_payload(p3)
    assert e1["paramsHash"] != e2["paramsHash"] != e3["paramsHash"]
    assert e1["meshDescriptor"] != e2["meshDescriptor"]
    assert e2["meshDescriptor"] != e3["meshDescriptor"]
    assert e1["meshDescriptor"]["meta"]["airgap"] != e2["meshDescriptor"]["meta"]["airgap"]


# ---------------------------------------------------------------------------
# RF matrix：slot / pole / dims / magnetThickness
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("factory", [default_radial_pmsm, creator_radial_pmsm_4p6s])
def test_rf_slot_count_changes_primitive_count(factory):
    base = factory()
    m0 = rebuild_viewport_payload(base)["meshDescriptor"]
    teeth0 = _tooth_sectors(m0)
    mutated = copy.deepcopy(base)
    mutated["stator"]["slotCount"] = int(base["stator"]["slotCount"]) + 6
    m1 = rebuild_viewport_payload(mutated)["meshDescriptor"]
    teeth1 = _tooth_sectors(m1)
    assert len(teeth1) == len(teeth0) + 6
    assert m1["meta"]["slotCount"] == mutated["stator"]["slotCount"]
    assert m0 != m1


@pytest.mark.parametrize("factory", [default_radial_pmsm, creator_radial_pmsm_4p6s])
def test_rf_pole_count_changes_magnet_count(factory):
    base = factory()
    m0 = rebuild_viewport_payload(base)["meshDescriptor"]
    mags0 = _magnet_sectors(m0)
    mutated = copy.deepcopy(base)
    # poleCount 须为正偶数
    mutated["rotor"]["poleCount"] = int(base["rotor"]["poleCount"]) + 2
    m1 = rebuild_viewport_payload(mutated)["meshDescriptor"]
    mags1 = _magnet_sectors(m1)
    assert len(mags1) == len(mags0) + 2
    assert m1["meta"]["poleCount"] == mutated["rotor"]["poleCount"]


@pytest.mark.parametrize("factory", [default_radial_pmsm, creator_radial_pmsm_4p6s])
def test_rf_airgap_tooth_od_change_dims(factory):
    base = factory()
    m0 = rebuild_viewport_payload(base)["meshDescriptor"]
    mutated = copy.deepcopy(base)
    mutated["airgap"] = float(base["airgap"]) + 0.25
    mutated["stator"]["toothWidth"] = float(base["stator"]["toothWidth"]) + 1.5
    # 配合：SID = ROD + 2*airgap；再略抬外径保持轭几何
    mutated["stator"]["innerDiameter"] = (
        float(mutated["rotor"]["outerDiameter"]) + 2.0 * float(mutated["airgap"])
    )
    mutated["stator"]["outerDiameter"] = float(mutated["stator"]["innerDiameter"]) + 30.0
    m1 = rebuild_viewport_payload(mutated)["meshDescriptor"]
    assert m1["meta"]["airgap"] == pytest.approx(mutated["airgap"])
    # 齿扇区 sweep 随 toothWidth 变
    t0 = _tooth_sectors(m0)[0]["sweepAngleDeg"]
    t1 = _tooth_sectors(m1)[0]["sweepAngleDeg"]
    assert t0 != t1
    # 定子齿内半径随 ID
    assert _tooth_sectors(m1)[0]["innerRadius"] != _tooth_sectors(m0)[0]["innerRadius"]


@pytest.mark.parametrize("factory", [default_radial_pmsm, creator_radial_pmsm_4p6s])
def test_rf_magnet_thickness_changes_mesh(factory):
    base = factory()
    # 保证有显式磁厚可改
    b = copy.deepcopy(base)
    if "magnetThickness" not in b["rotor"]:
        b["rotor"]["magnetThickness"] = 2.0
    m0 = rebuild_viewport_payload(b)["meshDescriptor"]
    assert m0["meta"]["magnetThicknessSource"].startswith("rotor.")
    mag0 = _magnet_sectors(m0)[0]
    radial0 = mag0["outerRadius"] - mag0["innerRadius"]

    mutated = copy.deepcopy(b)
    mutated["rotor"]["magnetThickness"] = float(b["rotor"]["magnetThickness"]) + 1.5
    m1 = rebuild_viewport_payload(mutated)["meshDescriptor"]
    mag1 = _magnet_sectors(m1)[0]
    radial1 = mag1["outerRadius"] - mag1["innerRadius"]
    assert radial1 != radial0
    assert m1["meta"]["magnetThickness"] == pytest.approx(mutated["rotor"]["magnetThickness"])
    assert m0 != m1
    # summary 亦变
    s0 = rebuild_viewport_payload(b)["geometrySummary"]
    s1 = rebuild_viewport_payload(mutated)["geometrySummary"]
    assert s0.get("magnet_thickness_m") != s1.get("magnet_thickness_m")


def test_rf_estimated_magnet_thickness_documented_in_meta():
    """无 magnetThickness 时估算，且 meta 可感知。"""
    p = default_radial_pmsm()
    assert "magnetThickness" not in p["rotor"]
    mesh = rebuild_viewport_payload(p)["meshDescriptor"]
    assert mesh["meta"]["magnetThicknessSource"] == "estimated_from_airgap_rotor"
    assert mesh["meta"]["magnetThickness"] > 0


# ---------------------------------------------------------------------------
# AF matrix：slot / pole / diskThickness / magnetThickness / airgap
# ---------------------------------------------------------------------------


def test_af_slot_and_pole_count_change_primitives():
    base = default_axial_af_pmsm(config="RFMR")
    m0 = rebuild_viewport_payload(base)["meshDescriptor"]
    n_slot_marks0 = len([p for p in m0["primitives"] if "slot_mark" in p["name"]])
    n_mag0 = len(_magnet_sectors(m0))

    s = copy.deepcopy(base)
    s["pmsm"]["slotCount"] = int(base["pmsm"]["slotCount"]) + 6
    m_s = rebuild_viewport_payload(s)["meshDescriptor"]
    n_slot_marks1 = len([p for p in m_s["primitives"] if "slot_mark" in p["name"]])
    assert n_slot_marks1 > n_slot_marks0
    assert m_s["meta"]["slotCount"] == s["pmsm"]["slotCount"]

    p = copy.deepcopy(base)
    p["pmsm"]["poleCount"] = int(base["pmsm"]["poleCount"]) + 2
    m_p = rebuild_viewport_payload(p)["meshDescriptor"]
    n_mag1 = len(_magnet_sectors(m_p))
    # RFMR 多转子盘：每盘极扇区随 poleCount；总数严格增加
    assert n_mag1 > n_mag0
    assert m_p["meta"]["poleCount"] == p["pmsm"]["poleCount"]


def test_af_disk_thickness_changes_mesh():
    """改盘厚 → 画面必变（ring height / magnet z）。"""
    base = default_axial_af_pmsm(config="RFMR")
    m0 = rebuild_viewport_payload(base)["meshDescriptor"]
    disks0 = [p for p in m0["primitives"] if p["type"] == "ring"]
    mutated = copy.deepcopy(base)
    mutated["pmsm"]["diskThickness"] = float(base["pmsm"]["diskThickness"]) + 3.0
    m1 = rebuild_viewport_payload(mutated)["meshDescriptor"]
    disks1 = [p for p in m1["primitives"] if p["type"] == "ring"]
    assert disks1[0]["height"] == pytest.approx(mutated["pmsm"]["diskThickness"])
    assert disks0[0]["height"] != disks1[0]["height"]
    assert m1["meta"]["diskThickness"] == pytest.approx(mutated["pmsm"]["diskThickness"])
    # summary stack_length 随盘厚
    s0 = rebuild_viewport_payload(base)["geometrySummary"]
    s1 = rebuild_viewport_payload(mutated)["geometrySummary"]
    assert s0["disk_thickness_m"] != s1["disk_thickness_m"]


def test_af_magnet_thickness_changes_mesh():
    base = default_axial_af_pmsm(config="RFMR")
    b = copy.deepcopy(base)
    b["pmsm"]["magnetThickness"] = 2.0
    m0 = rebuild_viewport_payload(b)["meshDescriptor"]
    mag0 = _magnet_sectors(m0)[0]
    mutated = copy.deepcopy(b)
    mutated["pmsm"]["magnetThickness"] = 4.5
    m1 = rebuild_viewport_payload(mutated)["meshDescriptor"]
    mag1 = _magnet_sectors(m1)[0]
    assert mag1["height"] == pytest.approx(4.5)
    assert mag0["height"] != mag1["height"]
    assert m1["meta"]["magnetThicknessSource"] == "pmsm.magnetThickness"
    assert m0 != m1


def test_af_airgap_and_od_change_dims():
    base = default_axial_af_pmsm(config="RFMR")
    m0 = rebuild_viewport_payload(base)["meshDescriptor"]
    mutated = copy.deepcopy(base)
    mutated["pmsm"]["airgap"] = float(base["pmsm"]["airgap"]) + 0.5
    mutated["pmsm"]["outerDiameter"] = float(base["pmsm"]["outerDiameter"]) + 10.0
    m1 = rebuild_viewport_payload(mutated)["meshDescriptor"]
    assert m1["meta"]["airgap"] == pytest.approx(mutated["pmsm"]["airgap"])
    rings0 = [p for p in m0["primitives"] if p["type"] == "ring"]
    rings1 = [p for p in m1["primitives"] if p["type"] == "ring"]
    assert rings1[0]["outerRadius"] > rings0[0]["outerRadius"]
    # z 堆叠间距含 airgap → 第二盘 z 变
    if len(rings0) > 1 and len(rings1) > 1:
        assert rings0[1]["z"] != rings1[1]["z"]


def test_af_same_params_stable_hash():
    af = default_axial_af_pmsm(config="RFMR")
    a = rebuild_viewport_payload(af)
    b = rebuild_viewport_payload(copy.deepcopy(af))
    assert a["paramsHash"] == b["paramsHash"]
    assert a["meshDescriptor"] == b["meshDescriptor"]
