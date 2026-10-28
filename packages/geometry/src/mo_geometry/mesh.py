"""Three.js 协作层：网格描述 JSON（无 Three / 无 Wasm）。

前端将 primitives 转为 BufferGeometry；本包只输出维度驱动的描述符。
"""

from __future__ import annotations

import math
from typing import Any

from mo_geometry.constants import MESH_SCHEMA_VERSION


def _ring(
    *,
    name: str,
    inner_radius: float,
    outer_radius: float,
    height: float,
    z: float = 0.0,
    radial_segments: int = 64,
    theta_segments: int | None = None,
) -> dict[str, Any]:
    return {
        "type": "ring",
        "name": name,
        "innerRadius": inner_radius,
        "outerRadius": outer_radius,
        "height": height,
        "z": z,
        "radialSegments": radial_segments,
        "thetaSegments": theta_segments or max(16, radial_segments),
    }


def _sector(
    *,
    name: str,
    inner_radius: float,
    outer_radius: float,
    height: float,
    start_angle_deg: float,
    sweep_angle_deg: float,
    z: float = 0.0,
    segments: int = 16,
) -> dict[str, Any]:
    return {
        "type": "sector",
        "name": name,
        "innerRadius": inner_radius,
        "outerRadius": outer_radius,
        "height": height,
        "startAngleDeg": start_angle_deg,
        "sweepAngleDeg": sweep_angle_deg,
        "z": z,
        "segments": segments,
    }


def build_radial_mesh_descriptor(params: dict[str, Any]) -> dict[str, Any]:
    """由径向参数生成建设性图元描述；槽数/内外径变化会改变图元。"""
    units = params.get("units") or {"length": "mm", "angle": "deg"}
    stator = params["stator"]
    rotor = params["rotor"]
    airgap = float(params["airgap"])
    length = float(params["axialActiveLength"])
    slot_count = int(stator["slotCount"])
    pole_count = int(rotor["poleCount"])
    rotor_topo = params.get("rotorTopology", "inner")

    s_ir = float(stator["innerDiameter"]) / 2.0
    s_or = float(stator["outerDiameter"]) / 2.0
    r_ir = float(rotor["innerDiameter"]) / 2.0
    r_or = float(rotor["outerDiameter"]) / 2.0
    tooth_w = float(stator["toothWidth"])
    yoke_h = float(stator["yokeHeight"])

    primitives: list[dict[str, Any]] = []

    # 定子轭环（外圈）
    yoke_inner = max(s_or - yoke_h, s_ir)
    primitives.append(
        _ring(
            name="stator_yoke",
            inner_radius=yoke_inner,
            outer_radius=s_or,
            height=length,
            radial_segments=max(48, slot_count * 4),
        )
    )

    # 定子齿扇区（数量 = slotCount）
    slot_pitch = 360.0 / slot_count
    # 齿宽角近似：arc ≈ toothWidth / mean radius
    mean_r = (s_ir + yoke_inner) / 2.0
    tooth_angle = min(slot_pitch * 0.6, math.degrees(tooth_w / max(mean_r, 1e-6)))
    for i in range(slot_count):
        start = i * slot_pitch + (slot_pitch - tooth_angle) / 2.0
        primitives.append(
            _sector(
                name=f"stator_tooth_{i}",
                inner_radius=s_ir,
                outer_radius=yoke_inner,
                height=length,
                start_angle_deg=start,
                sweep_angle_deg=tooth_angle,
                segments=8,
            )
        )

    # 转子本体
    primitives.append(
        _ring(
            name="rotor_core",
            inner_radius=r_ir,
            outer_radius=r_or,
            height=length,
            radial_segments=max(48, pole_count * 4),
        )
    )

    # 磁钢扇区占位（极数驱动）；内转子贴外径、外转子贴内径
    pole_pitch = 360.0 / pole_count
    mag_sweep = pole_pitch * 0.7
    mag_thickness = max(airgap * 2.0, (r_or - r_ir) * 0.15)
    if rotor_topo == "inner":
        mag_or = r_or
        mag_ir = max(r_ir, r_or - mag_thickness)
    else:
        mag_ir = r_ir
        mag_or = min(r_or, r_ir + mag_thickness)
    for i in range(pole_count):
        start = i * pole_pitch + (pole_pitch - mag_sweep) / 2.0
        primitives.append(
            _sector(
                name=f"magnet_{i}",
                inner_radius=mag_ir,
                outer_radius=mag_or,
                height=length * 0.95,
                start_angle_deg=start,
                sweep_angle_deg=mag_sweep,
                segments=6,
            )
        )

    # ACIM 导条占位：按槽位在转子外缘放细扇区
    acim = params.get("acim")
    if isinstance(acim, dict) and params.get("machineType") == "ACIM":
        bar_cs = acim.get("barCrossSection") or {}
        bar_w = float(bar_cs.get("width", 4.0))
        bar_h = float(bar_cs.get("height", 12.0))
        bar_angle = min(slot_pitch * 0.4, math.degrees(bar_w / max(r_or, 1e-6)))
        for i in range(slot_count):
            start = i * slot_pitch
            primitives.append(
                _sector(
                    name=f"acim_bar_{i}",
                    inner_radius=max(r_ir, r_or - bar_h),
                    outer_radius=r_or,
                    height=length,
                    start_angle_deg=start,
                    sweep_angle_deg=bar_angle,
                    segments=4,
                )
            )

    return {
        "schemaVersion": MESH_SCHEMA_VERSION,
        "kind": "radial",
        "units": dict(units),
        "meta": {
            "rotorTopology": rotor_topo,
            "machineType": params.get("machineType"),
            "slotCount": slot_count,
            "poleCount": pole_count,
            "airgap": airgap,
        },
        "primitives": primitives,
    }


def build_axial_mesh_descriptor(params: dict[str, Any]) -> dict[str, Any]:
    """轴向盘式：按 diskCount 堆叠 ring；槽/极扇区随参数变化。"""
    units = params.get("units") or {"length": "mm", "angle": "deg"}
    config = params.get("config", "RFMR")
    machine_type = params.get("machineType")

    if machine_type != "PMSM" or not isinstance(params.get("pmsm"), dict):
        return {
            "schemaVersion": MESH_SCHEMA_VERSION,
            "kind": "axial",
            "units": dict(units),
            "meta": {
                "config": config,
                "machineType": machine_type,
                "note": "Q1 mesh only for AF-PMSM; enum-reserved types return empty primitives",
            },
            "primitives": [],
        }

    pmsm = params["pmsm"]
    ir = float(pmsm["innerDiameter"]) / 2.0
    or_ = float(pmsm["outerDiameter"]) / 2.0
    disk_count = int(pmsm["diskCount"])
    airgap = float(pmsm["airgap"])
    thickness = float(pmsm["diskThickness"])
    mag_sector = float(pmsm["magnetSectorAngle"])
    slot_count = int(pmsm["slotCount"])
    pole_count = int(pmsm["poleCount"])

    primitives: list[dict[str, Any]] = []
    # 沿 z 堆叠：disk + airgap 交替
    z = 0.0
    for d in range(disk_count):
        role = "disk"
        if config == "RFMR":
            # 单定双转：中间定子，两侧转子（简化）
            mid = disk_count // 2
            role = "stator_disk" if d == mid else "rotor_disk"
        else:
            # FRMF 双定单转：中间转子
            mid = disk_count // 2
            role = "rotor_disk" if d == mid else "stator_disk"

        primitives.append(
            _ring(
                name=f"{role}_{d}",
                inner_radius=ir,
                outer_radius=or_,
                height=thickness,
                z=z,
                radial_segments=max(48, slot_count * 4),
            )
        )

        if role.startswith("stator"):
            slot_pitch = 360.0 / slot_count
            tooth_sweep = slot_pitch * 0.45
            for i in range(slot_count):
                start = i * slot_pitch
                primitives.append(
                    _sector(
                        name=f"stator_slot_mark_{d}_{i}",
                        inner_radius=ir,
                        outer_radius=or_,
                        height=thickness * 0.2,
                        start_angle_deg=start,
                        sweep_angle_deg=tooth_sweep,
                        z=z + thickness * 0.4,
                        segments=6,
                    )
                )
        else:
            pole_pitch = 360.0 / pole_count
            sweep = min(mag_sector, pole_pitch * 0.9)
            for i in range(pole_count):
                start = i * pole_pitch + (pole_pitch - sweep) / 2.0
                primitives.append(
                    _sector(
                        name=f"magnet_sector_{d}_{i}",
                        inner_radius=ir,
                        outer_radius=or_,
                        height=thickness * 0.3,
                        start_angle_deg=start,
                        sweep_angle_deg=sweep,
                        z=z + thickness * 0.35,
                        segments=8,
                    )
                )

        z += thickness + airgap

    return {
        "schemaVersion": MESH_SCHEMA_VERSION,
        "kind": "axial",
        "units": dict(units),
        "meta": {
            "config": config,
            "machineType": machine_type,
            "diskCount": disk_count,
            "slotCount": slot_count,
            "poleCount": pole_count,
            "airgap": airgap,
        },
        "primitives": primitives,
    }
