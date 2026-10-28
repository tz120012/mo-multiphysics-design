"""单位制约定（与 mems project.json units 对齐）。"""

from __future__ import annotations

from typing import Any, TypedDict

from mo_geometry.constants import AngleUnit, LengthUnit


class Units(TypedDict):
    length: LengthUnit
    angle: AngleUnit


def default_units() -> Units:
    return {"length": "mm", "angle": "deg"}


def validate_units(units: Any, errors: list[str], *, prefix: str = "units") -> None:
    if not isinstance(units, dict):
        errors.append(f"{prefix}: must be an object")
        return
    length = units.get("length")
    angle = units.get("angle")
    if length not in ("mm", "m"):
        errors.append(f"{prefix}.length: must be 'mm' or 'm', got {length!r}")
    if angle not in ("deg", "rad"):
        errors.append(f"{prefix}.angle: must be 'deg' or 'rad', got {angle!r}")
