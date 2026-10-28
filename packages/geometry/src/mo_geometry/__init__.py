"""Mo-几何：参数化电机几何 + Three.js 协作网格描述 + Q3 解析/FEM 入口导出。

不含 STEP/DXF（Q2）、不含 Wasm / 解析求解 / FEM 求解。参数以 JSON 供 FE/BE/.mems 消费。
"""

from __future__ import annotations

from mo_geometry.axial import (
    AxialParams,
    build_axial_mesh_descriptor,
    default_axial_af_pmsm,
    to_mems_geometry_fragment as to_mems_axial_fragment,
    validate_axial,
)
from mo_geometry.constants import (
    FEM_ENTRY_HINT_SCHEMA_VERSION,
    GEOMETRY_SCHEMA_VERSION,
    MESH_SCHEMA_VERSION,
    SOLVE_SCHEMA_VERSION,
    pole_pairs_from_pole_count,
)
from mo_geometry.radial import (
    RadialParams,
    build_radial_mesh_descriptor,
    default_radial_acim,
    default_radial_bldc,
    default_radial_pmsm,
    to_mems_geometry_fragment as to_mems_radial_fragment,
    validate_radial,
)
from mo_geometry.summary import export_axial_pipeline_entry, export_geometry_summary

__all__ = [
    "GEOMETRY_SCHEMA_VERSION",
    "MESH_SCHEMA_VERSION",
    "SOLVE_SCHEMA_VERSION",
    "FEM_ENTRY_HINT_SCHEMA_VERSION",
    "pole_pairs_from_pole_count",
    "AxialParams",
    "RadialParams",
    "build_axial_mesh_descriptor",
    "build_radial_mesh_descriptor",
    "default_axial_af_pmsm",
    "default_radial_acim",
    "default_radial_bldc",
    "default_radial_pmsm",
    "to_mems_axial_fragment",
    "to_mems_radial_fragment",
    "validate_axial",
    "validate_radial",
    "export_geometry_summary",
    "export_axial_pipeline_entry",
]

__version__ = "0.1.0"
