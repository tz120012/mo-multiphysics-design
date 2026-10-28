# 裁决：Q5-1 mems/files 独立路径边界（原 Q4+-3b）

| 字段 | 内容 |
| --- | --- |
| 维护 | Mo-架构 |
| 日期 | 2026-10-28（Asia/Shanghai） |
| 状态 | **已锁定**（架构边界；实现由 Mo-后端跟进；跟踪表由产品改进行中） |
| 基线 tip | Motor 开闸 Q5：`8079c11`；Q4+-3 F5=A 裁决：`bf0c1d5` / `83d2e6e`；后端 artifacts：`6144f91`；前端 `/field`：`4794565` |
| 任务源 | `docs/02` §Q5-1；`docs/qa/Q5-验收跟踪.md` Q5-1 |
| 关联 | Q4+-3 Jobs-artifacts-only 已关；本项补齐工程包任意成员只读 GET |
| 仓库 | `/workspace/mo-platform`（仅本仓库） |

> **不改** `docs/01` / `docs/02` 正文。  
> **禁勾** ≤5% / ≤3%；**不宣称** MVP 已达成。  
> 本文钉死 mems/files vs Jobs artifacts 边界与 OpenAPI 级契约；**不**写业务大改代码。

---

## 0. 现状核对（写稿时锁定）

| 面 | 事实 |
| --- | --- |
| Jobs 精简件 | `GET /jobs/{id}/artifacts` (+ `/{path}`) = L4/Q4+-3 **canonical**；解析序含可选 `.mems` zip-member 回落（tip `6144f91` PASS）。 |
| 整包 I/O | `GET/PUT /projects/{id}/mems` (+ import/export) = zip only；**无** public mems/files 路由。 |
| FE `/field` | tip `4794565` 主路径 job-artifacts；fixture 降级保留。 |
| Q4+-3 | 产品/Motor 已整关；mems/files 后置到 **Q5-1**（原 Q4+-3b）。 |

---

## 1. L1 — 边界对比（书面清晰）

| 能力 | 权威路径 | 用途 |
| --- | --- | --- |
| Jobs 精简场量/优化产物 | `GET /api/v1/jobs/{jobId}/artifacts` (+ `/{path}`) | `/field`、FEM/optimize 精简件；**Q4+-3 已关** |
| 工程包任意成员读 | `GET /api/v1/projects/{projectId}/mems/files/{path}` | job workdir GC 后仍可读；`geometry/params`、持久化 `solver/*`、history 等包内相对路径 |
| 整包 I/O | `GET/PUT /projects/{id}/mems` (+ import/export) | **不变** |

> **不要**把 mems/files 叙述成 `/field` 替代。公开消费几何/工程文件应走 mems/files；`/field` 精简件仍优先 job-artifacts。artifacts 仍可选用 `job.projectId` 的 mems member 作解析**回落**（内部实现），与公开展示路径分离。

---

## 2. L2 — API 契约（OpenAPI 级）

| 项 | 钉死 |
| --- | --- |
| Method/path | `GET /projects/{projectId}/mems/files/{path}`（`path` = zip 内相对路径，支持多段） |
| path 规则 | 禁止 `..`、空段、绝对路径（leading `/`）；规范化同 `artifacts_resolve.normalize_rel_path` 同严 |
| Auth | 与现有 mems GET 同（Bearer） |
| 200 | raw bytes + 合适 `Content-Type`（按扩展名；未知则 `application/octet-stream`）；可选 `Content-Disposition` |
| 404 | 项目无包 / 成员不存在 |
| 400 | 非法 path（含 `..`、空、绝对） |
| 本阶段范围 | **默认只读 GET**；**非目标**：member 级 PUT/DELETE |

OpenAPI：须新增完整 path 项；原「mems/files 推迟 / Q4+-3b」注记改为 **「Q5-1 提供」**（实现未齐时可标 `x-status: planned-q5-1` 或文内「Q5-1 实现中」）。

---

## 3. L3 — 实现要点（给 Mo-后端）

1. 复用现有 zip 读（如 `read_mems_member` / mems_store）；**勿**另造宽松路径解析。
2. 路径规范化与 artifacts **同严**（拒 `..` / 绝对 / 空）。
3. OpenAPI 新增 path；更新整包 mems 与 Jobs artifacts description 中的推迟措辞 → 指向 Q5-1。
4. **本架构 tip 不改** `apps/api` 业务代码；实现另 tip。
5. 冒烟：至少一条 GET 真实成员 **200**（如样例包 `geometry/params.json`）。

---

## 4. L4 — 前端

| 场景 | 优先路径 |
| --- | --- |
| `/field` 精简 FEM/optimize 件 | **仍优先** job-artifacts（Q4+-3） |
| 包内 geometry/params、非 job 精简件、workdir 已 GC 后的持久成员 | **优先** mems/files |
| 整包下载/替换 | 继续整包 mems |

冒烟：若 FE 本门消费 mems/files，至少一条真实成员 GET 200；否则可仅文档/类型预留，由测试记 BE 冒烟即可。

---

## 5. L5 — 验收

| 角色 | 条 |
| --- | --- |
| **Mo-架构** | 本锁定稿入库；OpenAPI 含 mems/files 路径骨架；与 artifacts 边界表清晰 |
| **Mo-后端** | 实现 GET + 路径安全 + OpenAPI 与实现对齐；冒烟 GET 真实成员 200 |
| **Mo-前端** | 非 job 精简件优先 mems/files；`/field` 不改叙事 |
| **Mo-测试** | 记 mems/files 可测；**不**整关 Q3-L4；跟踪表由产品改「进行中/通过」 |

---

## 6. L6 — 明确非目标

- **不**勾选解析 ≤5% / FEM ≤3%。
- **不**宣称 MVP 已达成。
- **不**整关 Q3-L4。
- **不**删 fixture / 不改整包默认语义。
- **不**要求本阶段 member PUT/DELETE（若要写另开项）。
- **不**把 mems/files 写成 `/field` 主路径替代。
- **不**改 `docs/qa/Q5-验收跟踪.md` 状态列（产品/测试维护）。

---

## 7. Motor 拍板项

| 项 | 内容 |
| --- | --- |
| 本门分叉 | **无新分叉默认** |
| member PUT/DELETE | 若要做 → **另开项**；不进本门 |
| F* | **无需 F* 除非改口**（例如要求同闸写成员、或改边界表权威路径） |

---

## 8. 给各角色的一句话

| 角色 | 动作 |
| --- | --- |
| **Mo-后端** | 实现只读 `GET .../mems/files/{path}`；复用 zip 读 + 同严 path；OpenAPI 去「推迟」；冒烟 200 |
| **Mo-前端** | 几何/工程文件走 mems/files；`/field` 仍 job-artifacts |
| **Mo-测试** | 记 mems/files 可测；禁勾误差；不整关 Q3-L4 |
| **Motor** | 无新 F*；改口（写成员 / 改权威路径）再拍 |

---

## 9. 修订

| 日期（Asia/Shanghai） | 说明 |
| --- | --- |
| 2026-10-28 | 初稿锁定 L1–L6；边界 vs artifacts；只读 GET；无需 F* 除非改口 |
