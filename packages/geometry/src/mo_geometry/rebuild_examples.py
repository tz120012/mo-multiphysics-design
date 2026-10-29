"""从 default_* 重写 packages/geometry/examples/ 下相关 JSON（live 可演示路径）。

用法::

    python -m mo_geometry.rebuild_examples
    # 或
    python packages/geometry/scripts/rebuild_examples.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from mo_geometry import (
    creator_radial_pmsm_4p6s,
    default_axial_af_pmsm,
    default_radial_acim,
    default_radial_pmsm,
    export_axial_pipeline_entry,
    export_geometry_summary,
    rebuild_live_geometry,
    rebuild_viewport_payload,
)
from mo_geometry.axial import build_axial_mesh_descriptor, to_mems_geometry_fragment as to_mems_axial
from mo_geometry.radial import (
    build_radial_mesh_descriptor,
    to_mems_geometry_fragment as to_mems_radial,
)


def _examples_dir() -> Path:
    # src/mo_geometry/rebuild_examples.py → packages/geometry/examples
    return Path(__file__).resolve().parents[2] / "examples"


def _dump(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {path.relative_to(path.parents[2])}")


def rebuild(examples_dir: Path | None = None) -> list[Path]:
    """重写样例 JSON；返回写入路径列表。"""
    out = examples_dir or _examples_dir()
    out.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    # --- RF PMSM ---
    rf = default_radial_pmsm()
    live_rf = rebuild_live_geometry(rf)
    paths = {
        out / "radial_pmsm_params.json": to_mems_radial(rf),
        out / "radial_pmsm_mesh.json": build_radial_mesh_descriptor(rf),
        out / "radial_pmsm_geometry_summary.json": export_geometry_summary(rf),
    }
    # sanity: live 与单独 export 一致
    assert live_rf["geometrySummary"] == paths[out / "radial_pmsm_geometry_summary.json"]
    assert live_rf["meshDescriptor"] == paths[out / "radial_pmsm_mesh.json"]
    paths[out / "radial_pmsm_viewport_payload.json"] = rebuild_viewport_payload(rf)

    # --- RF ACIM ---
    acim = default_radial_acim()
    paths[out / "radial_acim_params.json"] = to_mems_radial(acim)
    paths[out / "radial_acim_mesh.json"] = build_radial_mesh_descriptor(acim)

    # --- AF PMSM RFMR ---
    af = default_axial_af_pmsm(config="RFMR")
    live_af = rebuild_live_geometry(af)
    entry = export_axial_pipeline_entry(af)
    paths[out / "axial_af_pmsm_rfmr_params.json"] = to_mems_axial(af)
    paths[out / "axial_af_pmsm_rfmr_mesh.json"] = build_axial_mesh_descriptor(af)
    paths[out / "axial_af_pmsm_rfmr_geometry_summary.json"] = export_geometry_summary(af)
    paths[out / "axial_af_pmsm_rfmr_pipeline_entry.json"] = entry
    assert live_af["geometrySummary"] == entry["geometrySummary"]
    assert live_af["pipelineEntry"]["analyticSolveStub"]["geometry"] == entry["geometrySummary"]
    paths[out / "axial_af_pmsm_rfmr_viewport_payload.json"] = rebuild_viewport_payload(af)

    # --- RF PMSM CREATOR 4p/6s（独立样例；不覆盖 radial_pmsm_* demo）---
    creator = creator_radial_pmsm_4p6s()
    live_c = rebuild_live_geometry(creator)
    paths[out / "radial_pmsm_creator_4p6s_params.json"] = to_mems_radial(creator)
    paths[out / "radial_pmsm_creator_4p6s_mesh.json"] = build_radial_mesh_descriptor(creator)
    paths[out / "radial_pmsm_creator_4p6s_geometry_summary.json"] = export_geometry_summary(
        creator
    )
    assert live_c["geometrySummary"] == paths[out / "radial_pmsm_creator_4p6s_geometry_summary.json"]
    assert live_c["meshDescriptor"] == paths[out / "radial_pmsm_creator_4p6s_mesh.json"]

    for path, obj in paths.items():
        _dump(path, obj)
        written.append(path)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rebuild mo_geometry examples/ from defaults")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="examples directory (default: package examples/)",
    )
    args = parser.parse_args(argv)
    rebuild(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
