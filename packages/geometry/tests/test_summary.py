"""export_geometry_summary / export_axial_pipeline_entry / rebuild_live_geometry。"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from mo_geometry import (
    DEFAULT_N_PLANES,
    FEM_ENTRY_HINT_SCHEMA_VERSION,
    SOLVE_SCHEMA_VERSION,
    default_axial_af_pmsm,
    default_radial_acim,
    default_radial_pmsm,
    export_axial_pipeline_entry,
    export_geometry_summary,
    rebuild_live_geometry,
)
from mo_geometry.constants import GEOMETRY_SCHEMA_VERSION
from mo_geometry.units import default_units


_REQUIRED = (
    "poles",
    "slots",
    "stack_length_m",
    "airgap_m",
    "rotor_od_m",
    "stator_id_m",
)

_AF_EXTRA = (
    "outer_radius_m",
    "inner_radius_m",
    "disk_thickness_m",
    "disk_count",
    "n_planes",
)

_EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def test_rf_pmsm_summary_mapping_and_units():
    p = default_radial_pmsm()
    s = export_geometry_summary(p)
    for k in _REQUIRED:
        assert k in s
    assert s["poles"] == p["rotor"]["poleCount"] == 6
    assert s["poles"] % 2 == 0
    assert s["slots"] == p["stator"]["slotCount"] == 18
    assert s["stack_length_m"] == pytest.approx(25.0 / 1000.0)
    assert s["airgap_m"] == pytest.approx(0.5 / 1000.0)
    assert s["rotor_od_m"] == pytest.approx(50.0 / 1000.0)
    assert s["stator_id_m"] == pytest.approx(51.0 / 1000.0)
    # 无 magnetThickness 字段则不臆造
    assert "magnet_thickness_m" not in s


def test_rf_optional_magnet_thickness_when_present():
    p = default_radial_pmsm()
    p["rotor"]["magnetThickness"] = 3.0  # mm
    s = export_geometry_summary(p)
    assert s["magnet_thickness_m"] == pytest.approx(0.003)


def test_rf_acim_optional_bar_fields():
    p = default_radial_acim()
    s = export_geometry_summary(p)
    assert s["poles"] == 4
    assert s["rotor_bars"] == p["stator"]["slotCount"]
    # 4mm * 12mm → m²
    assert s["bar_area_m2"] == pytest.approx((4.0 / 1000.0) * (12.0 / 1000.0))


def test_af_pmsm_summary_pole_count_and_disk_thickness_stack():
    p = default_axial_af_pmsm(config="RFMR")
    s = export_geometry_summary(p)
    for k in _REQUIRED:
        assert k in s
    for k in _AF_EXTRA:
        assert k in s
    assert s["poles"] == p["pmsm"]["poleCount"] == 10
    assert s["poles"] % 2 == 0
    assert s["slots"] == 12
    # 钉死：stack = diskThickness/1000，不乘 diskCount；disk_thickness_m 同值
    assert s["stack_length_m"] == pytest.approx(8.0 / 1000.0)
    assert s["disk_thickness_m"] == pytest.approx(s["stack_length_m"])
    assert s["airgap_m"] == pytest.approx(1.0 / 1000.0)
    assert s["rotor_od_m"] == pytest.approx(120.0 / 1000.0)
    assert s["stator_id_m"] == pytest.approx(40.0 / 1000.0)
    assert s["outer_radius_m"] == pytest.approx(0.06)
    assert s["inner_radius_m"] == pytest.approx(0.02)
    assert s["disk_count"] == 3
    assert s["n_planes"] == DEFAULT_N_PLANES == 4
    assert s["magnet_arc_ratio"] == pytest.approx(150.0 / 180.0)
    assert "meta" not in s
    assert "polePairs" not in s


def test_af_n_planes_override_from_params():
    p = default_axial_af_pmsm()
    p["nPlanes"] = 6
    s = export_geometry_summary(p)
    assert s["n_planes"] == 6


def test_summary_rejects_invalid_and_bad_topology():
    bad = default_radial_pmsm()
    bad["rotor"]["poleCount"] = 7
    with pytest.raises(ValueError, match="poleCount|invalid"):
        export_geometry_summary(bad)

    with pytest.raises(ValueError, match="topology"):
        export_geometry_summary({"topology": "XY", "schemaVersion": GEOMETRY_SCHEMA_VERSION})

    reserved = {
        "schemaVersion": GEOMETRY_SCHEMA_VERSION,
        "topology": "AF",
        "machineType": "BLDC",
        "config": "RFMR",
        "units": default_units(),
    }
    with pytest.raises(ValueError, match="AF-PMSM|machineType"):
        export_geometry_summary(reserved)


def test_axial_pipeline_entry_keys_and_stubs():
    p = default_axial_af_pmsm(config="RFMR")
    entry = export_axial_pipeline_entry(p)
    for key in (
        "geometryParams",
        "geometrySummary",
        "meshDescriptor",
        "analyticSolveStub",
        "femEntryHint",
    ):
        assert key in entry

    assert entry["geometryParams"]["topology"] == "AF"
    assert entry["geometryParams"]["machineType"] == "PMSM"
    assert entry["geometrySummary"]["poles"] == 10
    assert entry["geometrySummary"]["outer_radius_m"] == pytest.approx(0.06)
    assert entry["geometrySummary"]["n_planes"] == 4
    assert entry["meshDescriptor"]["kind"] == "axial"

    stub = entry["analyticSolveStub"]
    assert stub["schema_version"] == SOLVE_SCHEMA_VERSION
    assert stub["topology"] == "AF"
    assert stub["machine_type"] == "PMSM"
    assert stub["geometry"] == entry["geometrySummary"]
    assert stub["geometry"]["disk_thickness_m"] == stub["geometry"]["stack_length_m"]
    assert "materials" in stub
    assert stub["operating_point"]["speed_rpm"] == 0.0

    hint = entry["femEntryHint"]
    assert hint["schemaVersion"] == FEM_ENTRY_HINT_SCHEMA_VERSION
    assert hint["topology"] == "AF"
    assert hint["machineType"] == "PMSM"
    assert hint["config"] == "RFMR"
    assert hint["units"]["length"] == "mm"
    assert hint["poleCount"] == 10
    assert hint["slotCount"] == 12
    assert hint["diskCount"] == 3
    assert hint["outerDiameter"] == 120.0
    assert hint["innerDiameter"] == 40.0
    assert hint["airgap"] == 1.0
    assert hint["diskThickness"] == 8.0


def test_axial_pipeline_rejects_non_pmsm_and_rf():
    reserved = {
        "schemaVersion": GEOMETRY_SCHEMA_VERSION,
        "topology": "AF",
        "machineType": "ACIM",
        "config": "FRMF",
        "units": default_units(),
    }
    with pytest.raises(ValueError, match="AF-PMSM|machineType"):
        export_axial_pipeline_entry(reserved)

    with pytest.raises(ValueError, match="topology"):
        export_axial_pipeline_entry(default_radial_pmsm())


def test_no_pole_pairs_dual_write_on_params():
    p = default_axial_af_pmsm()
    before = copy.deepcopy(p)
    export_geometry_summary(p)
    export_axial_pipeline_entry(p)
    rebuild_live_geometry(p)
    assert p == before
    assert "polePairs" not in p
    assert "polePairs" not in p["pmsm"]


def test_rebuild_live_geometry_rf_and_af():
    rf = default_radial_pmsm()
    live_rf = rebuild_live_geometry(rf)
    assert set(live_rf.keys()) == {"params", "meshDescriptor", "geometrySummary"}
    assert live_rf["params"]["topology"] == "RF"
    assert live_rf["meshDescriptor"]["kind"] == "radial"
    assert live_rf["geometrySummary"] == export_geometry_summary(rf)
    assert "pipelineEntry" not in live_rf

    af = default_axial_af_pmsm(config="RFMR")
    live_af = rebuild_live_geometry(af)
    assert "pipelineEntry" in live_af
    assert live_af["meshDescriptor"]["kind"] == "axial"
    assert live_af["geometrySummary"]["n_planes"] == 4
    assert live_af["pipelineEntry"]["analyticSolveStub"]["geometry"] == live_af["geometrySummary"]


def test_examples_match_export_spotcheck():
    """examples/ 与 live export 一致抽检（含新 AF summary 字段）。"""
    af = default_axial_af_pmsm(config="RFMR")
    expected = export_geometry_summary(af)
    on_disk = json.loads((_EXAMPLES / "axial_af_pmsm_rfmr_geometry_summary.json").read_text())
    assert on_disk == expected
    for k in _AF_EXTRA:
        assert k in on_disk

    entry_disk = json.loads((_EXAMPLES / "axial_af_pmsm_rfmr_pipeline_entry.json").read_text())
    entry_live = export_axial_pipeline_entry(af)
    assert entry_disk["geometrySummary"] == entry_live["geometrySummary"]
    assert entry_disk["analyticSolveStub"]["geometry"] == entry_live["geometrySummary"]

    rf = default_radial_pmsm()
    rf_disk = json.loads((_EXAMPLES / "radial_pmsm_geometry_summary.json").read_text())
    assert rf_disk == export_geometry_summary(rf)
