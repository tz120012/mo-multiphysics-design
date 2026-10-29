"""Mo-几何：参数化电机几何 + Three.js 协作网格描述 + 解析/FEM 入口导出 + live 重建 + Q6 视口 envelope。

不含 STEP/DXF（本阶段降级，见 docs/drafts/几何-Q4plus-live与降级.md）、
不含 Wasm / 解析求解 / FEM 求解。参数以 JSON 供 FE/BE/.mems 消费。
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
    DEFAULT_N_PLANES,
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
    creator_radial_pmsm_4p6s,
    default_radial_pmsm,
    to_mems_geometry_fragment as to_mems_radial_fragment,
    validate_radial,
)
from mo_geometry.summary import (
    export_axial_pipeline_entry,
    export_geometry_summary,
    rebuild_live_geometry,
)
from mo_geometry.viewport import (
    params_hash,
    rebuild_viewport_payload,
    unwrap_rebuild_params,
)

__all__ = [
    "GEOMETRY_SCHEMA_VERSION",
    "MESH_SCHEMA_VERSION",
    "SOLVE_SCHEMA_VERSION",
    "FEM_ENTRY_HINT_SCHEMA_VERSION",
    "DEFAULT_N_PLANES",
    "pole_pairs_from_pole_count",
    "AxialParams",
    "RadialParams",
    "build_axial_mesh_descriptor",
    "build_radial_mesh_descriptor",
    "default_axial_af_pmsm",
    "default_radial_acim",
    "default_radial_bldc",
    "creator_radial_pmsm_4p6s",
    "default_radial_pmsm",
    "to_mems_axial_fragment",
    "to_mems_radial_fragment",
    "validate_axial",
    "validate_radial",
    "export_geometry_summary",
    "export_axial_pipeline_entry",
    "rebuild_live_geometry",
    "rebuild_viewport_payload",
    "params_hash",
    "unwrap_rebuild_params",
]

__version__ = "0.1.0"
