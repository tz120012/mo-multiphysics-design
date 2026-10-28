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
