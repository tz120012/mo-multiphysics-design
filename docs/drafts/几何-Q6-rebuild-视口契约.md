# 几何 Q6：rebuild 视口补充契约（驱动字段 / paramsHash / 测试）

| 字段 | 内容 |
| --- | --- |
| 维护 | Mo-几何 |
| 日期 | 2026-10-29 Asia/Shanghai |
| 状态 | Q6-2 几何侧补充（对齐架构锁定稿） |
| **权威契约** | **`docs/drafts/Q6-UEM与几何rebuild契约.md`（架构 tip `55b1255`）** |
| 开闸 / 拍板 | Motor `cc3b2d1` / `be6ed88`（A1+B1+C2+D1） |
| 金标 API | **`rebuild_live_geometry`** |
| 包内超集 | `rebuild_viewport_payload`（扩展字段；不破坏 §2.3 最小集） |
| 约束 | 几何**无**自带 HTTP；不改 `apps/web`；不进求解内核；**不另立冲突请求形** |

> 本文是几何侧**补充**：驱动字段表、paramsHash、一致性测试、mesh 磁厚驱动。  
> **请求/响应权威形以架构锁定稿为准**；若本文与 `55b1255` 冲突，以架构稿为准。

---

## 0. 与架构锁定稿对齐（必读）

摘自 tip **`55b1255`** §2：

| 项 | 钉死 |
| --- | --- |
| Path | `POST /api/v1/geometry/rebuild`（后端薄封装；**非** Celery） |
| 实现 | `apps/api` → **`mo_geometry.rebuild_live_geometry`** |
| **Request** | **`{ "topology", "machineType?", "params" }`**，`params` = `geometry/params.json` |
| **Response 最小集 §2.3** | `{ params, meshDescriptor, geometrySummary[, pipelineEntry] }` |
| 禁止 | `public/mesh` fixture 冒充成功响应 |

几何包内便利：直接对 `rebuild_live_geometry(params)` / `rebuild_viewport_payload` 传入 params 根对象亦可；**HTTP 权威请求形仍是信封**。

---

## 1. 角色边界

| 角色 | 做什么 |
| --- | --- |
| **Mo-几何** | 金标 `rebuild_live_geometry`；驱动尺寸进 mesh；`rebuild_viewport_payload` 超集；pytest 矩阵；本文补充 |
| **Mo-后端** | 薄 HTTP：Request 信封 → `rebuild_live_geometry` → §2.3 响应 |
| **Mo-前端** | debounce 后 `POST /geometry/rebuild`；订阅 `meshDescriptor`；禁静态冒充建模 |

P0 机型：RF-BLDC / RF-PMSM / RF-ACIM；AF-PMSM（+`pipelineEntry`）。AF 非 PMSM → 后端 **400**（架构 §2.4）。

---

## 2. Request（权威 = 架构 §2.2）

```json
{
  "topology": "RF",
  "machineType": "PMSM",
  "params": {
    "schemaVersion": "0.1.0-q1",
    "topology": "RF",
    "machineType": "PMSM",
    "units": { "length": "mm", "angle": "deg" },
    "rotorTopology": "inner",
    "stator": { },
    "rotor": { },
    "airgap": 0.5,
    "axialActiveLength": 25.0
  }
}
```

| 字段 | 要求 |
| --- | --- |
| `topology` | 必填；与 `params.topology` 一致（`RF` \| `AF`） |
| `machineType` | 可选 |
| `params` | **必填**；mems `geometry/params.json`（camel；`schemaVersion` **`0.1.0-q1`**） |

`unwrap_rebuild_params` / 后端 normalize：信封优先；外层 topology/machineType 与内层不一致时以校验错误或信封覆盖策略为准（几何侧：topology 不一致 → `ValueError`）。

包内亦可直接传 `params` 根（无信封）给 Python API——**仅便利，非 HTTP 权威**。

---

## 3. Response

### 3.1 HTTP P0 最小集（架构 §2.3 = 金标）

```json
{
  "params": { },
  "meshDescriptor": { },
  "geometrySummary": { },
  "pipelineEntry": { }
}
```

`pipelineEntry` 仅 AF-PMSM 等既有导出时出现。

### 3.2 几何超集 `rebuild_viewport_payload`（可选）

在**保留最小集全部键**的前提下附加：

| 扩展字段 | 说明 |
| --- | --- |
| `schemaVersion` | 几何子 schema `0.1.0-q1` |
| `topology` / `machineType` | 冗余便于 FE 快捷读 |
| `paramsHash` | 规范化 params 的 sha256 hex **前 16**；排序键；排除顶层 `meta` |
| `meta.rebuildPolicy` | `"full"`（明示全量重算、无缓存） |

**后端 HTTP 主路径不必返回超集**；返回金标即可满足 P0。超集用于对拍、工具链或自愿扩展——**不得删除/改名最小集字段**。

样例：`packages/geometry/examples/*_viewport_payload.json`。  
JSON Schema（超集）：`docs/drafts/几何-Q6-rebuild-viewport.schema.json`。

---

## 4. Debounce 与禁止

| 项 | 建议 |
| --- | --- |
| Debounce | **150–300 ms** |
| 禁止 | 只改 UI/本地 params **不**调 rebuild |
| 禁止 | `public/mesh` 冒充 rebuild 成功 / 「建模完成」 |
| 禁止 | 缓存跳过全量重算（与 `meta.rebuildPolicy=full` 一致） |

改 **槽 / 极 / 磁厚 / 盘厚** → descriptor 与画面必须变（见 §6 测试）。

---

## 5. 驱动字段表（几何补充）

| 字段 | mesh 是否变 | summary 是否变 | 备注 |
| --- | --- | --- | --- |
| `stator.slotCount` / `pmsm.slotCount` | ✅ 数量 | ✅ `slots` | |
| `rotor.poleCount` / `pmsm.poleCount` | ✅ 数量 | ✅ `poles` | 正偶数 |
| `airgap` / `pmsm.airgap` | ✅ | ✅ `airgap_m` | RF 须气隙配合 |
| 内外径 / `toothWidth` / `yokeHeight` | ✅ | 部分 ✅ | toothWidth → mesh 角宽；未进 summary |
| `axialActiveLength` / stackLength | ✅ 高度 | ✅ `stack_length_m` | |
| **`rotor.magnetThickness`** | ✅ 磁钢径向厚 | ✅ `magnet_thickness_m` | 缺省估算 → `meta.magnetThicknessSource` |
| `rotor.magnetSpanDeg` | ✅ 扫掠角 | ❌ | 可选 |
| **`pmsm.diskThickness`** | ✅ 盘高 / z | ✅ `disk_thickness_m` | AF 验收必测 |
| **`pmsm.magnetThickness`** | ✅ 磁钢扇区高 | ✅ | 缺省 = 0.3×盘厚估算 |
| `pmsm.magnetSectorAngle` | ✅ | ✅ 可选 `magnet_arc_ratio` | |
| `stator.slotOpeningWidth/Height` | ❌ **未进 mesh** | ❌ | 只存 params；P0 未驱动 |
| `rotor.magnetHeight` | ❌ **未进 mesh** | ❌ | IPM 近似仍用径向磁厚 |

IPM：贴边扇区近似；**magnetThickness 变化必须可测**。

---

## 6. 一致性测试矩阵（P0）

`packages/geometry/tests/test_viewport_rebuild.py`（亦覆盖金标路径）：

| 用例 | RF | AF |
| --- | --- | --- |
| 改 `slotCount` → primitives 数量变 | ✅ | ✅ |
| 改 `poleCount` → 磁钢扇区数变 | ✅ | ✅ |
| 改内外径 / airgap / toothWidth → 尺寸变 | ✅ | ✅ airgap/OD |
| 改 **`magnetThickness`** → mesh 尺寸变 | ✅ | ✅ |
| 改 **`diskThickness`** → mesh 变 | — | ✅ |
| 同 params 两次 → 同 `paramsHash` + 同 descriptor | ✅ | ✅ |
| 不同 params → 不同 hash | ✅ | ✅ |
| 连续改参无缓存 | ✅ | ✅ |
| 架构信封 `{topology, params}` unwrap | ✅ | ✅ |

---

## 7. Python 入口

```python
from mo_geometry import (
    rebuild_live_geometry,      # 金标 = HTTP §2.3
    rebuild_viewport_payload,   # 超集（paramsHash 等）
    params_hash,
    unwrap_rebuild_params,      # 信封 → params
)

# HTTP 后端伪代码（权威）
live = rebuild_live_geometry(unwrap_rebuild_params(request_json))
# → {params, meshDescriptor, geometrySummary[, pipelineEntry]}
```

---

## 8. 消费要点（转交）

### Mo-后端

1. `POST /api/v1/geometry/rebuild`：Request = 架构信封；调用 **`rebuild_live_geometry`**；响应 §2.3。
2. 非法 / topology 不一致 / AF 非 PMSM → **400**。
3. **禁止** fixture 冒充；全量重算。

### Mo-前端

1. UEM 改参 → debounce 150–300ms → POST rebuild → 写 `meshDescriptor` / `geometrySummary`。
2. 禁静态 `public/mesh` 标「建模完成」。
3. 改槽/极/磁厚/盘厚须见视口变。

### Motor / QA

- 契约权威：`55b1255`；几何 tip 含驱动表 + 测试全绿。

---

*补充短文结束。权威锁定稿：`Q6-UEM与几何rebuild契约.md` @ tip `55b1255`。*

> **Q7-4 超集**见 [`几何-Q7-rebuild-体感超集.md`](./几何-Q7-rebuild-体感超集.md)（role / hudDims / modelingComplete=false；不 bump HTTP 最小集）。
