"""通用校验辅助。"""

from __future__ import annotations

from typing import Any, Iterable


def require_positive(name: str, value: Any, errors: list[str]) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        errors.append(f"{name}: must be a number, got {type(value).__name__}")
        return
    if value <= 0:
        errors.append(f"{name}: must be > 0, got {value}")


def require_non_negative(name: str, value: Any, errors: list[str]) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        errors.append(f"{name}: must be a number, got {type(value).__name__}")
        return
    if value < 0:
        errors.append(f"{name}: must be >= 0, got {value}")


def require_int_positive(name: str, value: Any, errors: list[str]) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        errors.append(f"{name}: must be an int, got {type(value).__name__}")
        return
    if value <= 0:
        errors.append(f"{name}: must be > 0, got {value}")


def require_one_of(name: str, value: Any, allowed: Iterable[str], errors: list[str]) -> None:
    allowed_set = set(allowed)
    if value not in allowed_set:
        errors.append(f"{name}: must be one of {sorted(allowed_set)}, got {value!r}")


def require_od_gt_id(prefix: str, inner: Any, outer: Any, errors: list[str]) -> None:
    if isinstance(inner, (int, float)) and isinstance(outer, (int, float)):
        if not isinstance(inner, bool) and not isinstance(outer, bool):
            if outer <= inner:
                errors.append(f"{prefix}: outerDiameter must be > innerDiameter ({outer} <= {inner})")


def require_positive_even_int(name: str, value: Any, errors: list[str]) -> None:
    """正偶数（极数 poleCount 规范）。"""
    if not isinstance(value, int) or isinstance(value, bool):
        errors.append(f"{name}: must be an int, got {type(value).__name__}")
        return
    if value <= 0:
        errors.append(f"{name}: must be > 0, got {value}")
        return
    if value % 2 != 0:
        errors.append(f"{name}: must be a positive even int (pole count), got {value}")
