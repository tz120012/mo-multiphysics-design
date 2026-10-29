"""Q7-4：mesh role / hudDims / modelingComplete=false 体感超集（不 bump HTTP 最小集）。"""

from __future__ import annotations

import copy

import pytest

from mo_geometry import (
    creator_radial_pmsm_4p6s,
    default_axial_af_pmsm,
    default_radial_acim,
    default_radial_bldc,
    default_radial_pmsm,
    rebuild_live_geometry,
    rebuild_viewport_payload,
)

_MIN_SET = {"params", "meshDescriptor", "geometrySummary"}

_RADIAL_ROLES = {
    "stator_yoke",
    "stator_tooth",
    "stator_slot",
    "rotor_core",
    "airgap_band",
    "magnet",
}
_AXIAL_ROLES = {
    "stator_disk",
    "rotor_disk",
    "stator_slot_mark",
    "magnet_sector",
}
_HUD_RF = {"slotCount", "poleCount", "airgapMm", "magnetThicknessMm"}
_HUD_AF = _HUD_RF | {"diskThicknessMm"}


def _assert_never_modeling_complete(obj: object) -> None:
    """递归：任何 modelingComplete 键必须为 False。"""
    if isinstance(obj, dict):
        if "modelingComplete" in obj:
            assert obj["modelingComplete"] is False
        for v in obj.values():
            _assert_never_modeling_complete(v)
    elif isinstance(obj, list):
        for item in obj:
            _assert_never_modeling_complete(item)


@pytest.mark.parametrize(
    "factory",
    [default_radial_bldc, default_radial_pmsm, default_radial_acim, creator_radial_pmsm_4p6s],
)
def test_live_min_set_and_q7_mesh_meta_rf(factory):
    p = factory()
    live = rebuild_live_geometry(p)
    assert set(live.keys()) == _MIN_SET or set(live.keys()) == _MIN_SET | {"pipelineEntry"}
    assert _MIN_SET <= set(live.keys())
    # 仅依赖最小集键即可消费
    mesh = live["meshDescriptor"]
    meta = mesh["meta"]
    assert meta["source"] == "parametric-rebuild"
    assert meta["modelingComplete"] is False
    assert meta["fidelity"] == "constructive-descriptor"
    assert _HUD_RF <= set(meta["hudDims"].keys())
    assert "diskThicknessMm" not in meta["hudDims"]
    # 禁止非约定 hudDims 键名
    for bad in ("airgap", "magnetThickness", "axialActiveLength", "statorOuterDiameter"):
        assert bad not in meta["hudDims"]
    roles = {prim.get("role") for prim in mesh["primitives"] if "role" in prim}
    assert _RADIAL_ROLES <= roles
    if p.get("machineType") == "ACIM":
        assert "acim_bar" in roles
    # 每个图元有 role
    for prim in mesh["primitives"]:
        assert "role" in prim
        assert isinstance(prim["role"], str)
    _assert_never_modeling_complete(live)


def test_live_min_set_and_q7_mesh_meta_af():
    af = default_axial_af_pmsm(config="RFMR")
    live = rebuild_live_geometry(af)
    assert _MIN_SET <= set(live.keys())
    assert "pipelineEntry" in live
    mesh = live["meshDescriptor"]
    meta = mesh["meta"]
    assert meta["source"] == "parametric-rebuild"
    assert meta["modelingComplete"] is False
    assert meta["fidelity"] == "constructive-descriptor"
    assert set(meta["hudDims"].keys()) == _HUD_AF
    roles = {prim["role"] for prim in mesh["primitives"]}
    assert _AXIAL_ROLES <= roles
    _assert_never_modeling_complete(live)


def test_radial_slot_cavity_and_airgap_band_param_driven():
    base = default_radial_pmsm()
    mesh = rebuild_live_geometry(base)["meshDescriptor"]
    slots = [p for p in mesh["primitives"] if p.get("role") == "stator_slot"]
    teeth = [p for p in mesh["primitives"] if p.get("role") == "stator_tooth"]
    assert len(slots) == int(base["stator"]["slotCount"])
    assert len(teeth) == int(base["stator"]["slotCount"])
    bands = [p for p in mesh["primitives"] if p.get("role") == "airgap_band"]
    assert len(bands) == 1
    band = bands[0]
    r_or = float(base["rotor"]["outerDiameter"]) / 2.0
    s_ir = float(base["stator"]["innerDiameter"]) / 2.0
    assert band["innerRadius"] == pytest.approx(min(r_or, s_ir))
    assert band["outerRadius"] == pytest.approx(max(r_or, s_ir))
    assert band["height"] == pytest.approx(float(base["axialActiveLength"]))


def test_param_change_updates_huddims_and_primitives_rf():
    base = default_radial_pmsm()
    m0 = rebuild_live_geometry(base)["meshDescriptor"]
    mutated = copy.deepcopy(base)
    mutated["stator"]["slotCount"] = int(base["stator"]["slotCount"]) + 6
    mutated["rotor"]["poleCount"] = int(base["rotor"]["poleCount"]) + 2
    mutated["rotor"]["magnetThickness"] = float(base["rotor"].get("magnetThickness", 2.0)) + 1.5
    m1 = rebuild_live_geometry(mutated)["meshDescriptor"]
    assert m1["meta"]["hudDims"]["slotCount"] == mutated["stator"]["slotCount"]
    assert m1["meta"]["hudDims"]["poleCount"] == mutated["rotor"]["poleCount"]
    assert m1["meta"]["hudDims"]["magnetThicknessMm"] == pytest.approx(
        mutated["rotor"]["magnetThickness"]
    )
    assert m0["meta"]["hudDims"] != m1["meta"]["hudDims"]
    assert len([p for p in m1["primitives"] if p.get("role") == "stator_tooth"]) == mutated[
        "stator"
    ]["slotCount"]
    assert len([p for p in m1["primitives"] if p.get("role") == "magnet"]) == mutated["rotor"][
        "poleCount"
    ]


def test_param_change_updates_huddims_af():
    base = default_axial_af_pmsm(config="RFMR")
    m0 = rebuild_live_geometry(base)["meshDescriptor"]
    mutated = copy.deepcopy(base)
    mutated["pmsm"]["diskThickness"] = float(base["pmsm"]["diskThickness"]) + 2.0
    mutated["pmsm"]["slotCount"] = int(base["pmsm"]["slotCount"]) + 6
    mutated["pmsm"]["magnetThickness"] = 3.5
    m1 = rebuild_live_geometry(mutated)["meshDescriptor"]
    assert m1["meta"]["hudDims"]["diskThicknessMm"] == pytest.approx(
        mutated["pmsm"]["diskThickness"]
    )
    assert m1["meta"]["hudDims"]["slotCount"] == mutated["pmsm"]["slotCount"]
    assert m1["meta"]["hudDims"]["magnetThicknessMm"] == pytest.approx(3.5)
    assert m0["meta"]["hudDims"] != m1["meta"]["hudDims"]
    assert m0 != m1


def test_viewport_superset_q7_meta_keeps_min_set():
    for factory in (default_radial_pmsm, default_axial_af_pmsm):
        p = factory() if factory is default_radial_pmsm else factory(config="RFMR")
        env = rebuild_viewport_payload(p)
        assert _MIN_SET <= set(env.keys())
        assert env["meta"]["modelingComplete"] is False
        assert env["meta"]["source"] == "parametric-rebuild"
        assert env["meta"]["q7Feel"] == "descriptor-superset"
        assert env["meta"]["rebuildPolicy"] == "full"
        _assert_never_modeling_complete(env)


def test_modeling_complete_never_true_across_factories():
    factories = [
        default_radial_bldc,
        default_radial_pmsm,
        default_radial_acim,
        creator_radial_pmsm_4p6s,
        lambda: default_axial_af_pmsm(config="RFMR"),
        lambda: default_axial_af_pmsm(config="FRMF"),
    ]
    for factory in factories:
        p = factory()
        live = rebuild_live_geometry(p)
        vp = rebuild_viewport_payload(p)
        _assert_never_modeling_complete(live)
        _assert_never_modeling_complete(vp)
        assert live["meshDescriptor"]["meta"]["modelingComplete"] is False
        assert vp["meta"]["modelingComplete"] is False
