"""Q6 视口 rebuild 超集：在金标 rebuild_live_geometry 之上附加对接字段。

权威 HTTP 契约见 ``docs/drafts/Q6-UEM与几何rebuild契约.md``（架构 tip ``55b1255``）：

- Request（后端封装形）：``{ "topology", "machineType?", "params" }``
  其中 ``params`` = ``geometry/params.json``
- Response 最小集（§2.3）= ``rebuild_live_geometry`` 形：
  ``params`` + ``meshDescriptor`` + ``geometrySummary`` + 可选 ``pipelineEntry``

本模块的 ``rebuild_viewport_payload`` 是**包内超集**（另附 ``paramsHash`` /
``schemaVersion`` / ``meta.rebuildPolicy`` 等），**不破坏**最小集字段。
HTTP P0 后端应调用 ``rebuild_live_geometry``（或返回至少含最小集的超集）。
几何包**不**自带 HTTP。
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any

from mo_geometry.constants import GEOMETRY_SCHEMA_VERSION
from mo_geometry.summary import rebuild_live_geometry

# 不参与 paramsHash 的顶层键（噪声 / 非几何权威）
_HASH_EXCLUDE_TOP: frozenset[str] = frozenset(
    {
        "meta",  # 文档/溯源旁注，不驱动 mesh
    }
)


def unwrap_rebuild_params(body: dict[str, Any]) -> dict[str, Any]:
    """解析调用入参为几何 ``geometry/params.json`` 对象。

    **权威（架构 tip ``55b1255`` §2.2）：**

    ```json
    { "topology": "RF", "machineType": "PMSM", "params": { /* geometry/params.json */ } }
    ```

    - 外层 ``topology`` 必填语义由 HTTP 保证；与 ``params.topology`` 不一致 → ``ValueError``
    - 外层 ``machineType`` 若给，写入/覆盖进返回的 params 拷贝

    **包内便利（非 HTTP 权威）：** 直接传 ``geometry/params.json`` 根对象
    （含 ``topology`` ∈ {RF,AF}，且**无**嵌套几何 ``params`` 信封）。
    """
    if not isinstance(body, dict):
        raise ValueError("rebuild params: body must be a dict")

    nested = body.get("params")
    has_nested = isinstance(nested, dict)
    root_topo = body.get("topology")
    root_mt = body.get("machineType")

    # --- 权威信封：{ topology, machineType?, params } ---
    if has_nested and (
        root_topo is not None
        or root_mt is not None
        or "topology" not in nested
    ):
        params = deepcopy(nested)
        if root_topo is not None:
            inner_topo = params.get("topology")
            if inner_topo is not None and inner_topo != root_topo:
                raise ValueError(
                    f"rebuild params: topology mismatch "
                    f"(envelope={root_topo!r}, params={inner_topo!r})"
                )
            params["topology"] = root_topo
        if root_mt is not None:
            params["machineType"] = root_mt
        if params.get("topology") not in ("RF", "AF"):
            raise ValueError(
                "rebuild params: topology must be 'RF' or 'AF' "
                f"(got {params.get('topology')!r})"
            )
        return params

    # 仅 { params: <geometry/params.json> }（无外层 topology）
    if has_nested and root_topo is None:
        params = deepcopy(nested)
        if params.get("topology") not in ("RF", "AF"):
            raise ValueError(
                "rebuild params: params.topology must be 'RF' or 'AF' "
                f"(got {params.get('topology')!r})"
            )
        return params

    # --- 包内便利：geometry/params.json 根 ---
    if root_topo in ("RF", "AF") or "stator" in body or "pmsm" in body or "rotor" in body:
        return body

    raise ValueError(
        "rebuild params: expected arch envelope "
        '{ "topology", "machineType?", "params" } '
        "(params = geometry/params.json; tip 55b1255 §2.2) "
        "or a bare geometry/params.json object"
    )


def canonicalize_params_for_hash(params: dict[str, Any]) -> Any:
    """规范化 params 供稳定 hash：深拷贝、去掉噪声键、排序键由 json 完成。"""
    if not isinstance(params, dict):
        raise ValueError("canonicalize_params_for_hash: params must be a dict")
    data = deepcopy(params)
    for k in _HASH_EXCLUDE_TOP:
        data.pop(k, None)
    return data


def params_hash(params: dict[str, Any]) -> str:
    """对规范化 params JSON 做 sha256，返回 hex 前 16 字符。

    - ``json.dumps(..., sort_keys=True, separators=(',', ':'), ensure_ascii=False)``
    - 排除顶层 ``meta`` 等噪声（见 ``_HASH_EXCLUDE_TOP``）
    """
    canon = canonicalize_params_for_hash(params)
    payload = json.dumps(canon, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return digest[:16]


def rebuild_viewport_payload(body: dict[str, Any]) -> dict[str, Any]:
    """视口 rebuild **超集**（Q6）：全量重算，无缓存。

    入参优先架构信封 ``{topology, machineType?, params}``（见 ``unwrap_rebuild_params``）。
    内部调用金标 ``rebuild_live_geometry``，响应**包含** §2.3 最小集，并扩展：

    **HTTP P0 最小集（架构 §2.3 / 金标）：**
    ``params`` / ``meshDescriptor`` / ``geometrySummary`` / 可选 ``pipelineEntry``

    **几何侧扩展（不破坏最小集）：**
    ``schemaVersion`` / ``topology`` / ``machineType`` / ``paramsHash`` /
    ``meta.rebuildPolicy="full"``

    后端 HTTP 主路径应返回至少最小集（直接 ``rebuild_live_geometry`` 即可）；
    本函数供对拍、本地工具或自愿返回超集时使用。
    """
    inner = unwrap_rebuild_params(body)
    live = rebuild_live_geometry(inner)
    mems_params = live["params"]
    # 最小集字段在前，扩展随后——消费者可只读 §2.3 键
    out: dict[str, Any] = {
        "params": mems_params,
        "meshDescriptor": live["meshDescriptor"],
        "geometrySummary": live["geometrySummary"],
    }
    if "pipelineEntry" in live:
        out["pipelineEntry"] = live["pipelineEntry"]
    # 扩展字段
    out["schemaVersion"] = GEOMETRY_SCHEMA_VERSION
    out["topology"] = mems_params.get("topology")
    out["machineType"] = mems_params.get("machineType")
    out["paramsHash"] = params_hash(mems_params)
    out["meta"] = {
        "rebuildPolicy": "full",
        "geometryApi": "rebuild_viewport_payload",
        "liveApi": "rebuild_live_geometry",
        "httpMinSet": "rebuild_live_geometry",  # 架构 §2.3
    }
    return out


__all__ = [
    "unwrap_rebuild_params",
    "canonicalize_params_for_hash",
    "params_hash",
    "rebuild_viewport_payload",
]
