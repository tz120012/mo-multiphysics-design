# 几何 Q7-4：rebuild 体感超集（role / hudDims / modelingComplete）

| 字段 | 内容 |
| --- | --- |
| 维护 | Mo-几何 |
| 日期 | 2026-10-29 Asia/Shanghai |
| 状态 | Q7-4 几何侧体感抬升（Motor 开闸 tip `30a37a7`） |
| 前置 | Q6 视口契约 tip `05180e2` / 架构 `55b1255` |
| 金标 API | **`rebuild_live_geometry`** = HTTP §2.3 最小集 |
| 包内超集 | `rebuild_viewport_payload` + meshDescriptor 可选字段 |
| 约束 | **不** bump HTTP 最小集字段名；**无**新 API；**禁** fixture 冒充建模完成；不改 Jobs / `apps/web` |

> 本文描述几何包**可选超集**。FE 可读可忽略；HTTP P0 仍只依赖 §2.3 最小集键。

---

## 1. 与 Q6 契约关系

| 层 | 权威 | 说明 |
| --- | --- | --- |
| HTTP §2.3 最小集 | `rebuild_live_geometry` | `params` / `meshDescriptor` / `geometrySummary` / 可选 `pipelineEntry` |
| Q6 包内超集 | `rebuild_viewport_payload` | + `paramsHash` / `schemaVersion` / `meta.rebuildPolicy` 等 |
| **Q7-4 体感超集** | 本文 | mesh 图元可选 `role`；`meshDescriptor.meta` 诚实/HUD 字段；viewport `meta` 再附 `q7Feel` 等 |

**不得删除/改名**最小集键。超集键全部可选；旧消费者不读即可。

交叉引用：[`几何-Q6-rebuild-视口契约.md`](./几何-Q6-rebuild-视口契约.md)。

---

## 2. 图元可选 `role`（向后兼容）

`_ring` / `_sector` 接受可选 `role: str | None = None`；**给了才写** `"role"` 键（不给则不写，保持旧样例兼容）。

### 径向 role 枚举

| role | 说明 |
| --- | --- |
| `stator_yoke` | 定子轭环 |
| `stator_tooth` | 定子齿扇区 |
| `stator_slot` | 齿间槽空腔扇区（Q7-4 体感；扫角 = slot_pitch − tooth_angle） |
| `rotor_core` | 转子本体环 |
| `airgap_band` | 气隙视觉环（真实气隙内外径；内转子 inner≈r_or、outer≈s_ir） |
| `magnet` | 磁钢扇区 |
| `acim_bar` | ACIM 导条占位 |

### 轴向 role 枚举

| role | 说明 |
| --- | --- |
| `stator_disk` | 定子盘 ring |
| `rotor_disk` | 转子盘 ring |
| `stator_slot_mark` | 定子槽位标记扇区 |
| `magnet_sector` | 磁钢扇区 |

仍参数驱动，**非**静态 fixture。

---

## 3. `meshDescriptor.meta` 体感/诚实字段

保留既有键（`slotCount` / `poleCount` / `airgap` / `magnetThickness` / …），追加：

| 键 | 值 | 说明 |
| --- | --- | --- |
| `source` | `"parametric-rebuild"` | 来源诚实标签 |
| `modelingComplete` | **`false`（硬钉）** | **禁止**据此勾「建模完成」；任何路径不得写 `true` |
| `fidelity` | `"constructive-descriptor"` | 建设性描述符，非 CAD/FEM 网格 |
| `hudDims` | object | FE HUD 稳定键（见下）；缺则省略该键 |

### `hudDims` 稳定键（FE 约定）

| 键 | 径向 | 轴向 | 单位 |
| --- | --- | --- | --- |
| `slotCount` | ✅ | ✅ | 无量纲 |
| `poleCount` | ✅ | ✅ | 无量纲 |
| `airgapMm` | ✅ | ✅ | mm（与 `units.length=mm` 时数值一致） |
| `magnetThicknessMm` | ✅ | ✅ | mm |
| `diskThicknessMm` | —（省略） | ✅ | mm |

**不要**用 `airgap` / `magnetThickness` / `axialActiveLength` 等非约定名作 `hudDims` 键（那些仍可在 meta 顶层保留，供既有消费者）。

---

## 4. `rebuild_viewport_payload` 超集 meta

在既有 `rebuildPolicy` / `geometryApi` / `liveApi` / `httpMinSet` 上追加：

| 键 | 值 |
| --- | --- |
| `modelingComplete` | `false` |
| `source` | `"parametric-rebuild"` |
| `q7Feel` | `"descriptor-superset"` |

最小集键仍完整保留。

---

## 5. 禁止与诚实边界

1. **禁止** `public/mesh` / examples fixture 冒充「建模完成」。
2. **`modelingComplete` 恒为 `false`**——体感抬升 ≠ 建模完成。
3. **不** bump HTTP 最小集；**无**新 REST；不改 Jobs/Celery；不改 `apps/web`。
4. FE 可忽略全部超集键；可读 `role` / `hudDims` 做材质着色与 HUD。

---

## 6. 测试

`packages/geometry/tests/test_q7_feel.py`（+ 既有 `test_viewport_rebuild.py`）：

- 金标仍含且仅依赖最小集键；mesh 含 `role` / `modelingComplete=false` / `hudDims`
- 改 slot/pole/magnet/disk 厚度 → primitives 或 hudDims 必变
- viewport 超集含 `modelingComplete=false`；最小集键仍在
- 断言无路径把 `modelingComplete` 设为 `true`

---

*Q7-4 几何体感超集短文。权威最小集仍以架构 tip `55b1255` / Q6 契约为准。*
