"""Q3-2：GeometrySummary 导出 + 轴向 AF 全流程入口（几何侧）。

将本包 camelCase（默认 mm）参数映射为解析契约
``packages/solver-analytic/api/solve.schema.json`` ``$defs.GeometrySummary``
（snake_case + SI 米）。

**AF stack_length_m 约定（钉死、可测）：**
盘式无径向「叠长」时，用单有效盘厚作为有效磁路轴向长度：

    stack_length_m = pmsm.diskThickness / 1000   # length unit = mm

若 ``units.length == "m"``，则不做 /1000。不按 diskCount 累乘，避免多气隙构型歧义。
AF 特有盘数/构型等放在 ``export_axial_pipeline_entry`` 的 ``femEntryHint``，
**不**写入 GeometrySummary（schema 无 meta）。
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from mo_geometry.axial import (
    build_axial_mesh_descriptor,
    to_mems_geometry_fragment as to_mems_axial_fragment,
    validate_axial,
)
from mo_geometry.constants import FEM_ENTRY_HINT_SCHEMA_VERSION, SOLVE_SCHEMA_VERSION
from mo_geometry.radial import validate_radial

_GEOMETRY_SUMMARY_REQUIRED = (
    "poles",
    "slots",
    "stack_length_m",
    "airgap_m",
    "rotor_od_m",
    "stator_id_m",
)


def _hard_errors(msgs: list[str]) -> list[str]:
    return [m for m in msgs if not m.startswith("warning:")]


def _raise_if_invalid(label: str, msgs: list[str]) -> None:
    hard = _hard_errors(msgs)
    if hard:
        joined = "; ".join(hard)
        raise ValueError(f"{label}: invalid params — {joined}")


def _length_to_m(value: Any, *, length_unit: str, field: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{field}: must be a number, got {type(value).__name__}")
    v = float(value)
    if length_unit == "m":
        return v
    if length_unit == "mm":
        return v / 1000.0
    raise ValueError(f"units.length: unsupported {length_unit!r} (expected 'mm' or 'm')")


def _area_to_m2(width: Any, height: Any, *, length_unit: str, field: str) -> float:
    w = _length_to_m(width, length_unit=length_unit, field=f"{field}.width")
    h = _length_to_m(height, length_unit=length_unit, field=f"{field}.height")
    return w * h


def _length_unit_of(params: dict[str, Any]) -> str:
    units = params.get("units") or {}
    if isinstance(units, dict):
        return str(units.get("length") or "mm")
    return "mm"


def _to_mm(value: float, *, length_unit: str) -> float:
    if length_unit == "mm":
        return float(value)
    if length_unit == "m":
        return float(value) * 1000.0
    raise ValueError(f"units.length: unsupported {length_unit!r}")


def _export_rf_summary(params: dict[str, Any]) -> dict[str, Any]:
    _raise_if_invalid("export_geometry_summary(RF)", validate_radial(params))
    lu = _length_unit_of(params)
    stator = params["stator"]
    rotor = params["rotor"]

    stack_src = stator.get("stackLength")
    if stack_src is None:
        stack_src = params.get("axialActiveLength")
    if stack_src is None:
        raise ValueError(
            "export_geometry_summary(RF): need stator.stackLength or axialActiveLength"
        )

    summary: dict[str, Any] = {
        "poles": int(rotor["poleCount"]),
        "slots": int(stator["slotCount"]),
        "stack_length_m": _length_to_m(stack_src, length_unit=lu, field="stack_length"),
        "airgap_m": _length_to_m(params["airgap"], length_unit=lu, field="airgap"),
        "rotor_od_m": _length_to_m(
            rotor["outerDiameter"], length_unit=lu, field="rotor.outerDiameter"
        ),
        "stator_id_m": _length_to_m(
            stator["innerDiameter"], length_unit=lu, field="stator.innerDiameter"
        ),
    }

    # 可选：仅当 params 已有字段时映射（禁止估算污染契约）
    mag_th = rotor.get("magnetThickness")
    if mag_th is None:
        mag_th = params.get("magnetThickness")
    if mag_th is not None:
        summary["magnet_thickness_m"] = _length_to_m(
            mag_th, length_unit=lu, field="magnetThickness"
        )

    acim = params.get("acim")
    if isinstance(acim, dict):
        bar_cs = acim.get("barCrossSection")
        if isinstance(bar_cs, dict) and "width" in bar_cs and "height" in bar_cs:
            summary["bar_area_m2"] = _area_to_m2(
                bar_cs["width"],
                bar_cs["height"],
                length_unit=lu,
                field="acim.barCrossSection",
            )
        if "rotorBars" in acim:
            summary["rotor_bars"] = int(acim["rotorBars"])
        elif params.get("machineType") == "ACIM":
            summary["rotor_bars"] = int(stator["slotCount"])

    return summary


def _export_af_summary(params: dict[str, Any]) -> dict[str, Any]:
    _raise_if_invalid("export_geometry_summary(AF)", validate_axial(params))
    if params.get("machineType") != "PMSM":
        raise ValueError(
            "export_geometry_summary(AF): only AF-PMSM has a full field tree; "
            f"got machineType={params.get('machineType')!r}"
        )
    pmsm = params.get("pmsm")
    if not isinstance(pmsm, dict):
        raise ValueError("export_geometry_summary(AF): pmsm object required")

    lu = _length_unit_of(params)
    # 钉死：有效磁路轴向长度 = 单盘厚（不乘 diskCount）
    summary: dict[str, Any] = {
        "poles": int(pmsm["poleCount"]),
        "slots": int(pmsm["slotCount"]),
        "stack_length_m": _length_to_m(
            pmsm["diskThickness"], length_unit=lu, field="pmsm.diskThickness"
        ),
        "airgap_m": _length_to_m(pmsm["airgap"], length_unit=lu, field="pmsm.airgap"),
        "rotor_od_m": _length_to_m(
            pmsm["outerDiameter"], length_unit=lu, field="pmsm.outerDiameter"
        ),
        "stator_id_m": _length_to_m(
            pmsm["innerDiameter"], length_unit=lu, field="pmsm.innerDiameter"
        ),
    }

    mag_th = pmsm.get("magnetThickness")
    if mag_th is not None:
        summary["magnet_thickness_m"] = _length_to_m(
            mag_th, length_unit=lu, field="pmsm.magnetThickness"
        )

    return summary


def export_geometry_summary(params: dict[str, Any]) -> dict[str, Any]:
    """导出解析用 GeometrySummary（snake_case + SI 米）。

    输入为本包径向 RF 或轴向 AF params（camelCase；默认 length=mm）。
    非法 topology / 校验失败 → ``ValueError``（先跑 ``validate_*``，忽略 ``warning:``）。

    映射要点：
    - RF: ``poles←rotor.poleCount``，``slots←stator.slotCount``，
      ``stack_length_m←(stator.stackLength|axialActiveLength)``，
      ``airgap_m←airgap``，``rotor_od_m←rotor.outerDiameter``，
      ``stator_id_m←stator.innerDiameter``。
    - AF-PMSM: ``poles←pmsm.poleCount``，``slots←pmsm.slotCount``，
      ``airgap_m←pmsm.airgap``，``rotor_od_m←pmsm.outerDiameter``，
      ``stator_id_m←pmsm.innerDiameter``，
      ``stack_length_m←pmsm.diskThickness``（单有效盘厚；见模块 docstring）。

    **禁止**往 params/mems 双写 polePairs；``poles`` 即为极数（=poleCount）。
    """
    if not isinstance(params, dict):
        raise ValueError("export_geometry_summary: params must be a dict")

    topology = params.get("topology")
    if topology == "RF":
        return _export_rf_summary(params)
    if topology == "AF":
        return _export_af_summary(params)
    raise ValueError(
        f"export_geometry_summary: unsupported topology {topology!r} (expected 'RF' or 'AF')"
    )


def export_axial_pipeline_entry(params: dict[str, Any]) -> dict[str, Any]:
    """AF-PMSM 全流程入口：几何 → 解析 stub → FEM hint（几何侧，无求解 / 无网格生成）。

    返回稳定 JSON，供 Mo-前端 / 后端串联：

    - ``geometryParams``：mems 几何片段
    - ``geometrySummary``：``export_geometry_summary`` 结果
    - ``meshDescriptor``：``build_axial_mesh_descriptor``（Three.js 协作）
    - ``analyticSolveStub``：可直接 POST 的 SolveRequest 骨架（材料/工况占位）
    - ``femEntryHint``：给 Mo-有限元的最小几何 hint（不做 FEM 网格；
      ``schemaVersion`` = ``0.1.0-q3-hint``）

    仅 AF-PMSM；其它机型 / 拓扑 → ``ValueError``。
    """
    if not isinstance(params, dict):
        raise ValueError("export_axial_pipeline_entry: params must be a dict")
    if params.get("topology") != "AF":
        raise ValueError(
            f"export_axial_pipeline_entry: topology must be 'AF', got {params.get('topology')!r}"
        )
    if params.get("machineType") != "PMSM":
        raise ValueError(
            "export_axial_pipeline_entry: only AF-PMSM supported; "
            f"got machineType={params.get('machineType')!r}"
        )

    _raise_if_invalid("export_axial_pipeline_entry", validate_axial(params))

    pmsm = params["pmsm"]
    geometry_params = to_mems_axial_fragment(params)  # type: ignore[arg-type]
    geometry_summary = export_geometry_summary(params)
    mesh_descriptor = build_axial_mesh_descriptor(params)  # type: ignore[arg-type]

    analytic_stub: dict[str, Any] = {
        "schema_version": SOLVE_SCHEMA_VERSION,
        "topology": "AF",
        "machine_type": "PMSM",
        "geometry": deepcopy(geometry_summary),
        # 材料 / 工况占位：由 Mo-前端或材料服务填实后再 POST
        "materials": {},
        "operating_point": {"speed_rpm": 0.0},
    }

    lu = _length_unit_of(params)
    angle_unit = "deg"
    units = params.get("units")
    if isinstance(units, dict) and units.get("angle") in ("deg", "rad"):
        angle_unit = str(units["angle"])

    fem_hint: dict[str, Any] = {
        "schemaVersion": FEM_ENTRY_HINT_SCHEMA_VERSION,
        "topology": "AF",
        "machineType": "PMSM",
        "config": params.get("config"),
        "units": {"length": "mm", "angle": angle_unit},
        "innerDiameter": _to_mm(float(pmsm["innerDiameter"]), length_unit=lu),
        "outerDiameter": _to_mm(float(pmsm["outerDiameter"]), length_unit=lu),
        "diskCount": int(pmsm["diskCount"]),
        "airgap": _to_mm(float(pmsm["airgap"]), length_unit=lu),
        "diskThickness": _to_mm(float(pmsm["diskThickness"]), length_unit=lu),
        "slotCount": int(pmsm["slotCount"]),
        "poleCount": int(pmsm["poleCount"]),
        "note": "Q3 geometry hint for Mo-FEM; no mesh generation in mo_geometry",
    }

    return {
        "geometryParams": geometry_params,
        "geometrySummary": geometry_summary,
        "meshDescriptor": mesh_descriptor,
        "analyticSolveStub": analytic_stub,
        "femEntryHint": fem_hint,
    }


__all__ = [
    "export_geometry_summary",
    "export_axial_pipeline_entry",
]
