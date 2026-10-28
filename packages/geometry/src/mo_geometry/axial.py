"""Q1-5：轴向 AF-PMSM 参数模型（RFMR/FRMF）；BLDC/ACIM 仅枚举预留。"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, TypedDict

from mo_geometry.constants import (
    GEOMETRY_SCHEMA_VERSION,
    AxialConfig,
    MachineType,
)
from mo_geometry.mesh import build_axial_mesh_descriptor as _build_mesh
from mo_geometry.units import Units, default_units, validate_units
from mo_geometry.validation import (
    require_int_positive,
    require_od_gt_id,
    require_one_of,
    require_positive,
)


class AxialPmsmFields(TypedDict):
    """AF-PMSM 完整字段树（Q1 仅为此机型展开）。"""

    innerDiameter: float
    outerDiameter: float
    diskCount: int
    airgap: float
    diskThickness: float
    magnetSectorAngle: float
    slotCount: int
    poleCount: int


class AxialParams(TypedDict, total=False):
    schemaVersion: str
    topology: str  # always "AF"
    machineType: MachineType
    config: AxialConfig
    units: Units
    # PMSM 字段；非 PMSM 时不应出现完整树
    pmsm: AxialPmsmFields


def default_axial_af_pmsm(*, config: AxialConfig = "RFMR") -> AxialParams:
    """AF-PMSM 默认盘式参数（mm / deg）。"""
    # RFMR：单定双转 → 典型 diskCount=3（定+2转）语义由 FE 解释；参数位给盘数
    disk_count = 3 if config == "RFMR" else 3  # FRMF 双定单转亦常为 3 盘
    return {
        "schemaVersion": GEOMETRY_SCHEMA_VERSION,
        "topology": "AF",
        "machineType": "PMSM",
        "config": config,
        "units": default_units(),
        "pmsm": {
            "innerDiameter": 40.0,
            "outerDiameter": 120.0,
            "diskCount": disk_count,
            "airgap": 1.0,
            "diskThickness": 8.0,
            "magnetSectorAngle": 150.0,
            "slotCount": 12,
            "poleCount": 10,
        },
    }


def validate_axial(params: Any) -> list[str]:
    """校验轴向参数。

    - machineType 可为 BLDC/PMSM/ACIM（枚举预留）
    - 仅 PMSM 允许并要求完整 `pmsm` 字段树
    - 非 PMSM：禁止完整 `pmsm` 树（仅枚举预留）
    """
    errors: list[str] = []

    if not isinstance(params, dict):
        return ["params: must be an object"]

    if params.get("schemaVersion") != GEOMETRY_SCHEMA_VERSION:
        errors.append(
            f"schemaVersion: expected {GEOMETRY_SCHEMA_VERSION!r}, "
            f"got {params.get('schemaVersion')!r}"
        )

    if params.get("topology") != "AF":
        errors.append(f"topology: must be 'AF', got {params.get('topology')!r}")

    require_one_of("machineType", params.get("machineType"), ("BLDC", "PMSM", "ACIM"), errors)
    require_one_of("config", params.get("config"), ("RFMR", "FRMF"), errors)
    validate_units(params.get("units"), errors)

    machine_type = params.get("machineType")
    pmsm = params.get("pmsm")

    if machine_type == "PMSM":
        if not isinstance(pmsm, dict):
            errors.append("pmsm: required object when machineType is 'PMSM'")
            return errors
        require_positive("pmsm.innerDiameter", pmsm.get("innerDiameter"), errors)
        require_positive("pmsm.outerDiameter", pmsm.get("outerDiameter"), errors)
        require_od_gt_id(
            "pmsm",
            pmsm.get("innerDiameter"),
            pmsm.get("outerDiameter"),
            errors,
        )
        require_int_positive("pmsm.diskCount", pmsm.get("diskCount"), errors)
        require_positive("pmsm.airgap", pmsm.get("airgap"), errors)
        require_positive("pmsm.diskThickness", pmsm.get("diskThickness"), errors)
        mag_ang = pmsm.get("magnetSectorAngle")
        if not isinstance(mag_ang, (int, float)) or isinstance(mag_ang, bool):
            errors.append("pmsm.magnetSectorAngle: must be a number")
        elif mag_ang <= 0 or mag_ang > 180:
            errors.append(
                f"pmsm.magnetSectorAngle: must be in (0, 180], got {mag_ang}"
            )
        require_int_positive("pmsm.slotCount", pmsm.get("slotCount"), errors)
        require_int_positive("pmsm.poleCount", pmsm.get("poleCount"), errors)
    else:
        # 枚举预留：不允许展开完整 PMSM 参数树
        if pmsm is not None:
            errors.append(
                f"pmsm: AF-{machine_type} is enum-reserved in Q1; "
                "do not supply full pmsm field tree (AF-PMSM only)"
            )

    return errors


def to_mems_geometry_fragment(params: AxialParams) -> dict[str, Any]:
    data = deepcopy(dict(params))
    data["schemaVersion"] = GEOMETRY_SCHEMA_VERSION
    data["topology"] = "AF"
    return data


def build_axial_mesh_descriptor(params: AxialParams) -> dict[str, Any]:
    return _build_mesh(params)
