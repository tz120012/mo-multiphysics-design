# 裁决：Q4+-3 mems 单文件 GET 与 artifacts / FE 收口

| 字段 | 内容 |
| --- | --- |
| 维护 | Mo-架构 |
| 日期 | 2026-10-28（Asia/Shanghai） |
| 状态 | **已锁定（默认）**；F5 仅 Motor 可改 |
| 基线 tip | Motor 开闸 Q4+：`10d3ff9` |
| 任务源 | `docs/02` Q4+-3：Mo-架构 / Mo-后端 / Mo-前端 — mems 单文件 GET 与 artifacts/FE 对齐收口；交付物 API+冒烟；FE 非仅 fixture 路径说明 |
| 关联 | Q3-L4「无 mems 单文件 GET → `/field` fixture 降级」子项；F1/L4 Jobs artifacts；`docs/drafts/Q3-F1-结果精简.md` |
| 仓库 | `/workspace/mo-platform`（仅本仓库） |

> **不改** `docs/01` / `docs/02` 正文。  
> **禁勾** ≤3% / ≤5%；**不宣称** MVP 已达成。  
> 本文把 Q4+-3 收口语义钉死；开叉仅 F5（见 §7）。

---

## 0. 现状核对（写稿时锁定）

| 面 | 事实 |
| --- | --- |
| Mems 包 I/O | `GET/PUT /projects/{id}/mems`（及 import/export）= **整包 zip only**（`apps/api/app/routers/mems.py`）。**无** public `GET .../mems/files/{path}`。 |
| Jobs 精简件 | `GET /jobs/{id}/artifacts` + `GET /jobs/{id}/artifacts/{path}` 已存在（F1/L4）。 |
| 解析序 | `artifacts_resolve.resolve_artifact_bytes`：`MO_OPT_WORKDIR` / `MO_FEM_WORKDIR` 下 `mems_shadow/{rel}` → `{rel}` → payload 内嵌 manifest.json → **可选** 工程 `.mems` zip member（`read_mems_member`）。 |
| 路径布局 | `resultRef` → `solver/{fem\|optimize}/jobs/{id}/manifest.json`；精简件多在 `results/{fem\|optimize}/{id}/…`。compose 卷 + `MO_*_WORKDIR` 对齐已修（证据 tip `e9d8af6` 一类）。 |
| FE `/field` | tip `c37422e`/`f207bbb` 已能接 Jobs artifacts；冒烟仍常 **fixture 降级**（未带 `jobId` 或产物不可达）。`fieldViz.ts` / `FieldVizView.vue` 已部分区分 `job-artifacts` / `job-fixture` / `fixture`。 |
| Q3-L4 | 整行仍跟踪（live 几何 / AF Wasm / 磁静力学 + mems 单文件）；本裁决只关 **field/artifacts「无 mems 单文件 GET」子项** 的口径，不整关 Q3-L4。 |

---

## 1. L1 — 收口语义（钉死）

Q3-L4 子弹「无 mems 单文件 GET」对 **`/field`** 的含义，**以 Jobs artifacts GET 为精简 FEM/optimize 产物的权威单文件读路径**，当请求侧具备 `jobId`（及可选 `resultRef`→manifest）时成立。

| 能力 | 权威路径 | 角色 |
| --- | --- | --- |
| 精简场量 / 优化产物单文件读 | `GET /api/v1/jobs/{jobId}/artifacts` + `.../artifacts/{path}` | **Q4+-3 关门主路径**；关闭「须另开 mems member GET 才能给 `/field`」的缺口叙述 |
| 工程包整包 I/O | `GET/PUT /projects/{id}/mems` | 继续；**不**改成按成员默认下载 |

> **不**把「无 `GET /projects/.../mems/files/{path}`」继续写成 `/field` 的硬阻塞；该缺口改记为 **Q4+-3b 快跟进**（§4），除非 Motor 在 F5 改闸。

---

## 2. L2 — FE 主路径（关 Q4+-3 必达）

`/field?jobId=…` **必须**：

1. 用 Jobs artifacts **list**；再按 manifest `artifacts[].path`（或 `resultRef`→manifest 后再取 path）**get** 精简件。
2. UI **明示** `source=job-artifacts`（已有类型与页眉展示；保持可见，勿藏进 console）。
3. **仅**在下列情况允许降级 public / fixture（含既有 `job-fixture`）：
   - 无 `jobId`；或
   - artifacts list 空 **且** 关键 get 为 404 / 不可达；或
   - 显式 `?source=fixture`（强制 fixture；联调/演示用）。
4. 降级时 UI 须区分 `source=fixture` vs `source=job-fixture`（有 job 但未吃到精简件），并保留「不宣称误差达标」提示。

**关项证据口径**：冒烟须证明带真实 `jobId` 时出现 **`source=job-artifacts`**（非仅 fixture 路径说明）。fixture 保留作降级，**禁止删除**（见 §6）。

---

## 3. L3 — BE（关 Q4+-3 必达）

1. **保持** `GET /jobs/{id}/artifacts` 与 `GET /jobs/{id}/artifacts/{path}` 对 **fem + optimize**（drive 若适用则同形）稳定；勿为收口改破坏性路径。
2. **文档化解析序**（OpenAPI description / 路由 docstring 与实现对齐），建议明示：

   ```text
   MO_OPT_WORKDIR / MO_FEM_WORKDIR:
     mems_shadow/{rel} → {rel}
   → payload 内嵌 manifest.json（仅 manifest 自身）
   → 可选：job.projectId 对应已存 .mems zip 内同相对路径 member
   ```

3. compose / 环境：`MO_*_WORKDIR` + 共享卷须使 SUCCEEDED 作业的精简件 **GET≠404**（既有修复保持）。
4. OpenAPI 注记建议句：**「Jobs artifacts GET = L4 / Q4+-3 精简结果单文件读；工程包仍走整包 mems；`GET .../mems/files/{path}` 为可选快跟进，非本门硬项。」**
5. 可选改进（非硬项）：若 `resultRef` / `artifacts[].path` 仅存在于已持久化 `.mems` zip，确认 zip-member 回落路径在冒烟中可触达，并在 OpenAPI notes 写明「已实现可选 zip member」。

---

## 4. L4 — mems member GET（拆项）

| 编号 | 内容 | 是否进 Q4+-3 同闸 |
| --- | --- | --- |
| **Q4+-3（本门）** | Jobs-artifacts-only 证明 + FE `source=job-artifacts` 冒烟 | **是** |
| **Q4+-3b（快跟进）** | 新增 `GET /projects/{projectId}/mems/files/{path}`：任意 mems 相对成员（如 `geometry/params.json`、包持久化后的 `solver/*`）；用于 **job workdir 已 GC、mems 仍保留** | **默认否**；Motor F5 改闸除外 |

Q4+-3b 用途：包级任意成员读，**不是** `/field` 精简件主路径的替代叙事。未开 F5 前标 stretch。

---

## 5. L5 — 验收条

| 角色 | 条 |
| --- | --- |
| **Mo-架构** | 本锁定稿入库（本文件） |
| **Mo-后端** | fem+optimize artifacts GET 冒烟绿；OpenAPI/注释写明 Jobs artifacts = L4 精简单文件读；备注 mems/files 推迟（除非 F5） |
| **Mo-前端** | `/field` + 真实 `jobId` 展示 `source=job-artifacts`（非 fixture-only）；README 或视图注释写清降级规则（§2） |
| **Mo-测试** | 冒烟记录证明非 fixture 主路径；**可关** Q3-L4 的 **field/artifacts「无 mems 单文件 GET」子项**；**不可**整关 Q3-L4（live 几何 / AF Wasm / 磁静力学 → Q4+-4 / Q4+-5） |

---

## 6. L6 — 明确非目标

- **不**勾选解析 ≤5% / FEM ≤3%。
- **不**宣称 MVP 已达成 / 全流程数值验收完成。
- **不**删除 fixture / public 降级路径。
- **不**要求本门交付任意 mems 成员 GET（见 §4 / F5）。
- **不**把 heat-proxy / dry-run 精简件等同磁静力学真场。

---

## 7. 分叉（仅 Motor）

**F5**：Q4+-3 同闸是否必须上线 `GET /projects/{projectId}/mems/files/{path}`？

| 选项 | 含义 |
| --- | --- |
| **A（架构默认）** | Jobs-artifacts-only 即可关 Q4+-3；`mems/files` = **Q4+-3b** 快跟进 |
| B | 同闸必须同时交付 `mems/files/{path}` |

未收到 Motor 改口前按 **A** 执行。

---

## 8. 给各角色的一句话

| 角色 | 动作 |
| --- | --- |
| **Mo-后端** | 稳住 artifacts list/get + 解析序文档/OpenAPI 注记；冒烟绿；**勿**默认开工 mems/files（等 F5） |
| **Mo-前端** | `/field?jobId=` 主路径吃 job-artifacts；强制展示 source；补 `?source=fixture` 与降级规则说明 |
| **Mo-测试** | 记一条 **source=job-artifacts** 冒烟；只关 L4 field/artifacts 子项，不整关 Q3-L4 |
| **Motor** | 默认采纳 A；若要同闸 mems/files 请明示 F5→B |

---

## 9. 修订

| 日期（Asia/Shanghai） | 说明 |
| --- | --- |
| 2026-10-28 | 初稿锁定 L1–L6；F5 默认 A |
