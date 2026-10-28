"""径向 ACIM 导条参数位（Q1-7）。

附着于 radial 模型的可选 `acim` 块；machineType=acim 时必填。
笼型极对数 / 槽配合仅为校验占位（可出 warning 级信息，当前以 errors 列表返回约束提示）。
"""

from __future__ import annotations

from typing import Any, TypedDict

from mo_geometry.constants import BAR_SLOT_SHAPES
from mo_geometry.validation import (
    require_int_positive,
    require_one_of,
    require_positive,
)


class BarCrossSection(TypedDict):
    width: float
    height: float


class EndRingSection(TypedDict):
    width: float
    height: float


class AcimBlock(TypedDict):
    barSlotShape: str
    barCrossSection: BarCrossSection
    endRingSection: EndRingSection
    barMaterialId: str
    endRingMaterialId: str
    cagePolePairs: int


def default_acim_block() -> AcimBlock:
    return {
        "barSlotShape": "rectangular",
        "barCrossSection": {"width": 4.0, "height": 12.0},
        "endRingSection": {"width": 8.0, "height": 10.0},
        "barMaterialId": "mat.acim.bar.aluminum-default",
        "endRingMaterialId": "mat.acim.endring.aluminum-default",
        "cagePolePairs": 2,
    }


def validate_acim_block(
    acim: Any,
    *,
    slot_count: int | None,
    errors: list[str],
    warnings: list[str] | None = None,
) -> None:
    """校验 ACIM 导条块。warnings 可选收集槽配合占位提示。"""
    if not isinstance(acim, dict):
        errors.append("acim: must be an object when present")
        return

    require_one_of("acim.barSlotShape", acim.get("barSlotShape"), BAR_SLOT_SHAPES, errors)

    bar_cs = acim.get("barCrossSection")
    if not isinstance(bar_cs, dict):
        errors.append("acim.barCrossSection: must be an object")
    else:
        require_positive("acim.barCrossSection.width", bar_cs.get("width"), errors)
        require_positive("acim.barCrossSection.height", bar_cs.get("height"), errors)

    end_ring = acim.get("endRingSection")
    if not isinstance(end_ring, dict):
        errors.append("acim.endRingSection: must be an object")
    else:
        require_positive("acim.endRingSection.width", end_ring.get("width"), errors)
        require_positive("acim.endRingSection.height", end_ring.get("height"), errors)

    for key in ("barMaterialId", "endRingMaterialId"):
        val = acim.get(key)
        if not isinstance(val, str) or not val.strip():
            errors.append(f"acim.{key}: must be a non-empty material id string")

    require_int_positive("acim.cagePolePairs", acim.get("cagePolePairs"), errors)

    # 槽配合 / 极对数占位约束（Q1 仅提示，不阻断默认样例）
    cage_pp = acim.get("cagePolePairs")
    if (
        warnings is not None
        and isinstance(slot_count, int)
        and isinstance(cage_pp, int)
        and not isinstance(cage_pp, bool)
        and slot_count > 0
        and cage_pp > 0
    ):
        # 占位：常见经验 Ns / (2*p) 宜为整数；非硬失败
        poles = 2 * cage_pp
        if slot_count % poles != 0:
            warnings.append(
                f"acim.slotFit: slotCount ({slot_count}) is not divisible by "
                f"2*cagePolePairs ({poles}); treat as soft constraint placeholder"
            )
