"""Schema / 枚举常量（与 mems-schema-v0 对齐命名空间）。"""

from __future__ import annotations

from typing import Final, Literal

# 几何参数 JSON schema（.mems geometry/params.json 片段）
GEOMETRY_SCHEMA_VERSION: Final[str] = "0.1.0-q1"

# Three.js 协作网格描述 schema
MESH_SCHEMA_VERSION: Final[str] = "0.1.0-q1"

Topology = Literal["RF", "AF"]
MachineType = Literal["BLDC", "PMSM", "ACIM"]
RotorTopology = Literal["inner", "outer"]
SlotShape = Literal["straight", "skewed", "fan"]
MagnetTopology = Literal["SPM", "IPM"]
AxialConfig = Literal["RFMR", "FRMF"]
LengthUnit = Literal["mm", "m"]
AngleUnit = Literal["deg", "rad"]

BAR_SLOT_SHAPES: Final[tuple[str, ...]] = (
    "rectangular",
    "oval",
    "closed_slot",
    "open_slot",
)


def pole_pairs_from_pole_count(pole_count: int) -> int:
    """电气极对数（派生）。权威持久化字段仍是 poleCount；勿反向双写。"""
    if not isinstance(pole_count, int) or isinstance(pole_count, bool) or pole_count <= 0 or pole_count % 2 != 0:
        raise ValueError(f"pole_count must be a positive even int, got {pole_count!r}")
    return pole_count // 2


# 解析 SolveRequest schema_version（只读对齐；本包不实现求解）
SOLVE_SCHEMA_VERSION: Final[str] = "0.0.0-gate0"

# Q3-2 FEM 入口 hint（独立于几何参数 schema；不做网格）
FEM_ENTRY_HINT_SCHEMA_VERSION: Final[str] = "0.1.0-q3-hint"
