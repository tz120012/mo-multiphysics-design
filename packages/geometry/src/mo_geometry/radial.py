"""Q1-4 / Q1-7：径向 RF 参数模型、校验、.mems 片段、网格描述入口。"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, TypedDict

from mo_geometry.acim import AcimBlock, default_acim_block, validate_acim_block
from mo_geometry.constants import (
    GEOMETRY_SCHEMA_VERSION,
    MachineType,
    MagnetTopology,
    RotorTopology,
    SlotShape,
)
from mo_geometry.mesh import build_radial_mesh_descriptor as _build_mesh
from mo_geometry.units import Units, default_units, validate_units
from mo_geometry.validation import (
    require_int_positive,
    require_od_gt_id,
    require_one_of,
    require_positive,
)


class StatorParams(TypedDict):
    innerDiameter: float
    outerDiameter: float
    stackLength: float
    slotCount: int
    slotShape: SlotShape
    toothWidth: float
    yokeHeight: float
    skewAngle: float | None


class RotorParams(TypedDict):
    innerDiameter: float
    outerDiameter: float
    magnetTopology: MagnetTopology
    poleCount: int


class RadialParams(TypedDict, total=False):
    schemaVersion: str
    topology: str  # always "RF"
    machineType: MachineType
    units: Units
    rotorTopology: RotorTopology
    stator: StatorParams
    rotor: RotorParams
    airgap: float
    axialActiveLength: float
    acim: AcimBlock


def _base_radial(*, machine_type: MachineType) -> RadialParams:
    """典型小型无人机径向电机量级默认值（mm）。"""
    return {
        "schemaVersion": GEOMETRY_SCHEMA_VERSION,
        "topology": "RF",
        "machineType": machine_type,
        "units": default_units(),
        "rotorTopology": "inner",
        "stator": {
            "innerDiameter": 51.0,
            "outerDiameter": 80.0,
            "stackLength": 25.0,
            "slotCount": 12,
            "slotShape": "straight",
            "toothWidth": 4.5,
            "yokeHeight": 5.0,
            "skewAngle": None,
        },
        "rotor": {
            "innerDiameter": 15.0,
            "outerDiameter": 50.0,
            "magnetTopology": "SPM",
            "poleCount": 10,
        },
        "airgap": 0.5,
        "axialActiveLength": 25.0,
    }


def default_radial_bldc() -> RadialParams:
    return _base_radial(machine_type="BLDC")


def default_radial_pmsm() -> RadialParams:
    p = _base_radial(machine_type="PMSM")
    # 略偏正弦机：更多槽
    p["stator"]["slotCount"] = 18
    p["rotor"]["poleCount"] = 6
    return p


def default_radial_acim() -> RadialParams:
    p = _base_radial(machine_type="ACIM")
    p["stator"]["slotCount"] = 36
    p["rotor"]["magnetTopology"] = "SPM"  # 占位；ACIM 无磁钢，字段保留兼容
    p["rotor"]["poleCount"] = 4
    p["acim"] = default_acim_block()
    return p


def validate_radial(params: Any) -> list[str]:
    """返回错误列表；空列表表示通过。含 ACIM soft 槽配合提示（前缀 warning:）。"""
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(params, dict):
        return ["params: must be an object"]

    if params.get("schemaVersion") != GEOMETRY_SCHEMA_VERSION:
        errors.append(
            f"schemaVersion: expected {GEOMETRY_SCHEMA_VERSION!r}, "
            f"got {params.get('schemaVersion')!r}"
        )

    if params.get("topology") != "RF":
        errors.append(f"topology: must be 'RF', got {params.get('topology')!r}")

    require_one_of("machineType", params.get("machineType"), ("BLDC", "PMSM", "ACIM"), errors)
    validate_units(params.get("units"), errors)
    require_one_of("rotorTopology", params.get("rotorTopology"), ("inner", "outer"), errors)

    stator = params.get("stator")
    slot_count: int | None = None
    if not isinstance(stator, dict):
        errors.append("stator: must be an object")
    else:
        require_positive("stator.innerDiameter", stator.get("innerDiameter"), errors)
        require_positive("stator.outerDiameter", stator.get("outerDiameter"), errors)
        require_od_gt_id(
            "stator",
            stator.get("innerDiameter"),
            stator.get("outerDiameter"),
            errors,
        )
        require_positive("stator.stackLength", stator.get("stackLength"), errors)
        require_int_positive("stator.slotCount", stator.get("slotCount"), errors)
        if isinstance(stator.get("slotCount"), int) and not isinstance(stator.get("slotCount"), bool):
            slot_count = stator["slotCount"]
        require_one_of(
            "stator.slotShape",
            stator.get("slotShape"),
            ("straight", "skewed", "fan"),
            errors,
        )
        require_positive("stator.toothWidth", stator.get("toothWidth"), errors)
        require_positive("stator.yokeHeight", stator.get("yokeHeight"), errors)
        skew = stator.get("skewAngle", None)
        if skew is not None:
            if not isinstance(skew, (int, float)) or isinstance(skew, bool):
                errors.append("stator.skewAngle: must be a number or null")
            elif skew < 0:
                errors.append(f"stator.skewAngle: must be >= 0, got {skew}")
        if stator.get("slotShape") == "skewed" and (skew is None or skew == 0):
            errors.append("stator.skewAngle: required and > 0 when slotShape is 'skewed'")

    rotor = params.get("rotor")
    if not isinstance(rotor, dict):
        errors.append("rotor: must be an object")
    else:
        require_positive("rotor.innerDiameter", rotor.get("innerDiameter"), errors)
        require_positive("rotor.outerDiameter", rotor.get("outerDiameter"), errors)
        require_od_gt_id(
            "rotor",
            rotor.get("innerDiameter"),
            rotor.get("outerDiameter"),
            errors,
        )
        require_one_of(
            "rotor.magnetTopology",
            rotor.get("magnetTopology"),
            ("SPM", "IPM"),
            errors,
        )
        require_int_positive("rotor.poleCount", rotor.get("poleCount"), errors)

    require_positive("airgap", params.get("airgap"), errors)
    require_positive("axialActiveLength", params.get("axialActiveLength"), errors)

    # 气隙与内外径一致性粗检（内转子：定子 ID ≈ 转子 OD + 2*airgap）
    if (
        isinstance(stator, dict)
        and isinstance(rotor, dict)
        and params.get("rotorTopology") == "inner"
        and isinstance(params.get("airgap"), (int, float))
        and not isinstance(params.get("airgap"), bool)
    ):
        s_id = stator.get("innerDiameter")
        r_od = rotor.get("outerDiameter")
        ag = params["airgap"]
        if isinstance(s_id, (int, float)) and isinstance(r_od, (int, float)):
            expected = r_od + 2 * ag
            # 允许 0.1 mm 公差（默认单位 mm）
            if abs(s_id - expected) > max(0.1, 0.05 * ag):
                errors.append(
                    f"airgap/fit: for inner rotor, stator.innerDiameter ({s_id}) "
                    f"should ≈ rotor.outerDiameter + 2*airgap ({expected})"
                )

    machine_type = params.get("machineType")
    acim = params.get("acim")
    if machine_type == "ACIM":
        if acim is None:
            errors.append("acim: required when machineType is 'ACIM'")
        else:
            validate_acim_block(acim, slot_count=slot_count, errors=errors, warnings=warnings)
    elif acim is not None:
        # 非 ACIM 允许省略；若提供则仍校验形状
        validate_acim_block(acim, slot_count=slot_count, errors=errors, warnings=warnings)

    # soft warnings 以 warning: 前缀并入返回，便于调用方过滤
    return errors + [f"warning: {w}" for w in warnings]


def to_mems_geometry_fragment(params: RadialParams) -> dict[str, Any]:
    """稳定 JSON：可写入 geometry/params.json 的径向片段。"""
    data = deepcopy(dict(params))
    data["schemaVersion"] = GEOMETRY_SCHEMA_VERSION
    data["topology"] = "RF"
    # 去掉 None 的 skewAngle 仍保留键以稳定 shape
    stator = data.get("stator")
    if isinstance(stator, dict) and "skewAngle" not in stator:
        stator["skewAngle"] = None
    return data


def build_radial_mesh_descriptor(params: RadialParams) -> dict[str, Any]:
    """委托 mesh 模块；保持 public API 在 radial 侧可发现。"""
    return _build_mesh(params)
