# Q4-9 NSGA-II 多目标优化 — 跨服务边界架构锁定（草案）

| 项 | 值 |
| --- | --- |
| 状态 | **Q4 架构锁定草案**（等 Motor 追认；开放分叉见 §8 F3/F4） |
| 日期 | 2026-10-28（Asia/Shanghai） |
| 作者 | Mo-架构 |
| 依据 | `docs/01-任务书-v2.md` §3 热–力与优化 / §4 栈；`docs/02` Q4-9（Mo-架构 / Mo-解析；交付：任务定义 + 帕累托结果） |
| tip 基准 | Motor Q3 pass / Q4 open：`db4161b`（其后 tip 仅文档/运维叠加，不改本边界） |
| 配套 | [Q3-轴向与FEM边界.md](./Q3-轴向与FEM边界.md)、[Q3-F1-结果精简.md](./Q3-F1-结果精简.md)、[openapi-v1.yaml](./openapi-v1.yaml)、[驱动后处理.md](./驱动后处理.md)、[解析范围.md](./解析范围.md)、[mems-schema-v1.md](./mems-schema-v1.md) |
| 冻结源 | **不修改** `docs/01` / `docs/02` 正文 |
| memsSchemaVersion | 仍沿草案谱系（与 Q3 一致；本文件只扩 `solver/optimize/` 路径约定） |

> 本文件锁定：Q4-9 NSGA-II 的 **Jobs / 包 / 载荷 / resultRef / FE·BE 边界**；各角色 Does / Does not；验收条；以及须 Motor 拍板的开放分叉。**架构默认已标清，勿当作 Motor 已签字。**  
> 驱动（Q4-1…6）拥有驱动源 / Map / ripple / 退磁接口，**不**拥有 NSGA 核心。热 LPTN（Q4-7）、轴向磁拉力（Q4-8）的指标可被 NSGA **日后消费**，但 **Q4 MVP 不得阻塞在完整热–力闭环**。

---

## 1. Owner 总表（Q4-9）

| Owner | Owns（Q4-9） | Does not |
| --- | --- | --- |
| **Mo-架构** | 本边界稿；OpenAPI / Jobs `jobType=optimize` delta；`OptimizeJobPayload` / Pareto 结果契约形状；跨服务验收条 | NSGA 算法实现；目标度量公式本体；驱动模型 |
| **Mo-解析** | **`packages/solver-opt/`**（新）：NSGA-II 核心 + problem / 目标适配器 schema；种群评估编排（调用 analytic 求值）；帕累托精简写出 | Elmer/GetDP；把 NSGA 塞进 `solver-analytic` 根；驱动源实现；FE 帕累托图 |
| **Mo-驱动** | 目标适配器所需的 **效率 Map / 转矩脉动 / 损耗分离** 等度量出口（契约侧）；驱动 knobs 作为可选变量域 | NSGA 种群循环；Jobs `optimize` worker；解析内核 |
| **Mo-后端** | `POST/GET/cancel` Jobs：`jobType=optimize` 入队/轮询/取消；校验 `OptimizeJobPayload`；写 `resultRef`；artifacts list/get（对齐 FEM L4 模式） | 在 FastAPI 进程内跑 NSGA；浏览器直算帕累托 |
| **Mo-前端** | fire + poll Jobs；帕累托前沿图 + 选个体 → 回写几何/参数；非阻塞 UX（同 FEM 规则） | 浏览器-only 优化；以 sync FastAPI 长请求堵死 UI |
| **Mo-有限元** | （stretch）精英个体 **spot FEM** 评估钩子；不进 MVP 门禁 | NSGA 外层循环；默认全种群 FEM |
| **Mo-运维** | optimize Celery worker 镜像（含实现库，选型后置）；队列与资源配额 | 包内算法内容；OpenAPI 形状发明 |
| **Mo-测试** | Q4-9 冒烟：入队 → 取消/成功 → 帕累托 JSON 可读；契约 fixture | 发明 API / 目录布局 |
| **Mo-几何** | 变量域中几何 knobs 的摘要字段可被 payload 引用 | 优化循环；目标函数 |

---

## 2. 总则锁定（架构默认，等 Motor 追认）

| # | 决策 | 锁定内容 |
| --- | --- | --- |
| L1 | **jobType** | 新增语义落地名 **`optimize`**（OpenAPI / `apps/api` 枚举 **已占位** `[analytic, fem, optimize]`）。**必须**异步 Jobs only：**禁止** sync FastAPI 长跑；**禁止**浏览器-only NSGA。外层优化循环 **不得** 复用/overload `analytic` / `fem`。 |
| L2 | **包路径** | 新建 **`packages/solver-opt/`**，Owner = **Mo-解析**（NSGA-II + problem definition schemas）。Mo-架构 Owns OpenAPI/Jobs delta。**否决**把 NSGA 塞进 `packages/solver-analytic` 根（保持 analytic solve schema 干净）。备选包名见 §8 **F4**。 |
| L3 | **Q4 MVP 评估路径** | 种群个体适应度 **主路径 = analytic**（RF：Wasm 结果可被 BE/worker 复用或 BE `solve`；AF：Jobs `analytic` 或 sync）。**可选 spot FEM** 仅对精英个体 = **stretch**，非 MVP 门禁。驱动耦合目标（效率 Map / ripple 等）经 **objective adapters** 声明；若驱动模型未就绪，允许 **几何 + analytic-only** 目标做演示（见 §8 **F3**）。 |
| L4 | **热–力解耦** | Q4-7 LPTN / Q4-8 轴向力指标可进后续目标目录；**Q4 MVP 不阻塞**完整热–力闭环。 |
| L5 | **实现库** | **选型后置，不挡边界锁定**。当前 `packages/` 无 scipy/pymoo 依赖。优先纯 Python / worker 镜像内 pymoo（或等价），**避免**要求宿主机单独安装 scipy-only。 |
| L6 | **Cancel / resume** | **Cancel 为 MVP 必达**；resume / checkpoint = stretch。 |
| L7 | **精简精神** | 复用 Q3 **F1 thinning**：浏览器路径只吃帕累托 JSON（前沿 / 个体 / 变量向量 / 目标向量）；**禁止**默认回灌全场 FEM 场量。 |

---

## 3. 包与目录（`packages/solver-opt/`）

### 3.1 授权立包

| 项 | 锁定 |
| --- | --- |
| 包路径 | **`packages/solver-opt/`**（架构默认；Motor 追认前可先立骨架） |
| 内容 | NSGA-II 实现入口；`OptimizeJobPayload` / Pareto manifest / results JSON Schema；objective adapter 接口；样例 problem fixture |
| **禁止** | 托管 FEM 二进制；把 analytic `SolveRequest` 污染为优化专用超集；宿主机强制 scipy 系统包 |
| 与 analytic 关系 | 评估时 **调用** `packages/solver-analytic`（或已存在的 solve 契约），不把优化状态机搬进 analytic |

推荐目录（可演进，勿改名包根直至 F4 拍板）：

```text
packages/solver-opt/
  README.md
  api/                 # optimize-job-payload / optimize-manifest / pareto-results schema
  nsga/                # 算法核心（选型后置）
  adapters/            # analytic / drive /（stretch）fem 目标适配器
  fixtures/            # 可复现小种群样例
```

### 3.2 否决方案

| 方案 | 结论 |
| --- | --- |
| NSGA 代码进 `packages/solver-analytic/` 根 | **否决** — 污染 solve schema 与金标边界 |
| 仅 FE Wasm 内跑完整 NSGA | **否决** — 违反 L1（Jobs only） |
| 外层循环伪装成 `jobType=analytic` 批处理 | **否决** — 语义与观测/取消/配额混乱 |

---

## 4. Jobs / API（optimize **始终**异步）

### 4.1 总则

1. 交互优化 **禁止**以「同步长请求堵死 UI」为唯一路径：必须 **fire Jobs → poll/subscribe → 进度**（同 Q3 FEM）。
2. `POST /jobs` 且 `jobType=optimize` 为 Q4-9 **主入口**。
3. **禁止**在 `apps/api` 进程内跑 NSGA 种群循环（可入队；worker 执行）。
4. Job 状态枚举不变：`queued | running | succeeded | failed | cancelled`。
5. **Cancel MVP 必达**（`cancelled` 终态）；resume/checkpoint stretch。
6. Artifacts：**对齐 FEM L4** — `GET /jobs/{id}/artifacts`（及按 path get）可读 manifest / 帕累托 JSON；MVP 至少 `resultRef` + `.mems`/workdir GET。

### 4.2 与现有枚举关系（无冲突）

当前 OpenAPI / API：

```yaml
JobType:
  enum: [analytic, fem, optimize]
```

`apps/api/app/schemas/common.py` 同步：`analytic` | `fem` | `optimize`。  
`routers/jobs.py`：`optimize` 仍为 **queued 占位**（注释：until Q4）。  

→ **枚举名无需再改**；本锁定把 `optimize` 从占位升为 **真实异步路径 + payload/resultRef 合同**。

### 4.3 `OptimizeJobPayload`（必填形状 — 架构默认）

| 字段 | 类型 / 约束 | 说明 |
| --- | --- | --- |
| `projectId` | uuid | 与 Job 顶层一致；payload 内可冗余 |
| `memsRef` | string，可选 | 工程 `.mems` 根或快照句柄 |
| `variables` | array | 几何 / 材料 / **驱动 knobs**；每项含 id、类型、**bounds**（及可选 discrete set） |
| `objectives` | array（≥2 建议） | `{ id, sense: minimize\|maximize, metricId }`；metricId 映射适配器（efficiency / cost / torqueRipple / … 对齐 01） |
| `constraints` | array，可选 | 不等式/等式占位；MVP 可空 |
| `nsga` | object | `{ popSize, generations, seed }`（可复现；禁止无 seed 的隐式随机当金标） |
| `evaluatorProfile` | enum | **`analytic`** \| **`analytic+drive`** \| stretch **`analytic+fem`** |

规则：

- MVP 默认 `evaluatorProfile=analytic`；`analytic+drive` 在驱动度量就绪后启用（F3）。
- `analytic+fem`：仅精英 spot FEM，**非** MVP 门禁。
- 外层 job **只**用 `jobType=optimize`；内层评估可 **嵌套调用** analytic solve /（可选）enqueue fem，但不得把外层改成 `analytic`/`fem`。

### 4.4 `resultRef` 与精简产物

成功后推荐主指针：

```text
solver/optimize/jobs/{jobId}/manifest.json
```

精简帕累托目录：

```text
results/optimize/{jobId}/
```

| 产物 | 内容 |
| --- | --- |
| `manifest.json` | jobId、status、evaluatorProfile、nsga 回显、标量摘要（代数、前沿数）、`artifacts[]` |
| `results/optimize/{jobId}/pareto.json`（或拆分 fronts/individuals） | **fronts**、**individuals**、**variable vectors**、**objective vectors** |
| （禁止默认） | 全场 FEM VTK/VTU、完整每代全种群重场；可留 worker 盘 |

复用 F1 精神：浏览器默认路径只吃 JSON 帕累托；体积软顶可参考 FEM ~5–20 MB 量级（优化结果通常远小于此）。

### 4.5 验收条（后端 / Jobs）

| 角色 | Accept bar |
| --- | --- |
| **Mo-后端** | `optimize` 入队至 Celery optimize 队列（非 api 进程求解）；轮询；**cancel**；succeeded 持久化 `resultRef`；校验 `OptimizeJobPayload`（可渐进收紧）；artifacts list/get 对齐 L4 |
| **Mo-运维** | worker 镜像可加载 `solver-opt`；与 analytic 评估依赖共存；无宿主机强制 scipy |

---

## 5. 评估路径与目标适配器

### 5.1 MVP 主路径（analytic）

```text
UI → POST /jobs { jobType: optimize, payload: OptimizeJobPayload }
   → Celery optimize worker (solver-opt)
       → for each individual: adapter.analytic → SolveRequest/SolveResult
       → NSGA-II 更新种群
   → write manifest + results/optimize/{jobId}/
   → Job.resultRef = solver/optimize/jobs/{jobId}/manifest.json
```

- RF：优先复用既有 analytic 金标 / BE solve；Wasm 仍是 **交互单点**主路径，**不是**优化外环宿主。
- AF：评估走 sync 或 Jobs `analytic`（与 Q3 AF 部署一致）。

### 5.2 驱动耦合（adapter，非 NSGA 核心）

| metricId（示例） | 来源角色 | MVP |
| --- | --- | --- |
| `efficiency` / Map 派生 | Mo-驱动（Map）+ 解析损耗 | F3：可后置 |
| `torqueRipple` | Mo-驱动 ripple 指标 / 解析粗估 | F3 |
| `cost` | 几何+材料成本模型（解析/架构约定 stub 可） | MVP 可用 stub |
| 损耗分量、退磁裕度等 | 驱动/解析接口 | 随后 |

驱动 Owns 度量定义与 `drive/` 出口；**solver-opt** Owns 如何把度量挂进 objectives。驱动模型未就绪 → 允许 analytic-only 目标演示（F3）。

### 5.3 Stretch：spot FEM

- 仅对当前前沿/精英子集触发 `jobType=fem` 或内嵌 fem 评估钩子。
- **不**作为 Q4-9 门禁；失败/缺失不得挡 analytic Pareto 演示。

### 5.4 热–力

- Q4-7 / Q4-8 指标可登记为 **future metricId**；MVP **不**要求 LPTN/轴向力闭环已通。

---

## 6. 前端 / UX

| 项 | 锁定 |
| --- | --- |
| 提交 | fire-and-forget Jobs；展示进度（代数 / 已评估个体数，若 worker 上报） |
| 完成 | 拉 `resultRef` → 帕累托图；点选个体 → **apply** 到几何/材料/驱动参数 |
| 取消 | 用户可取消进行中作业（对接 BE cancel） |
| 禁止 | 以阻塞式长轮询为唯一 UX；浏览器内跑完整 NSGA 当正式路径 |

验收（前端）：非阻塞；帕累托可读；至少一次「选个体 → 参数回写」演示路径。

---

## 7. 各角色验收条汇总（Q4-9）

| 角色 | Accept bar（摘要） |
| --- | --- |
| **Mo-架构** | 本边界 + OpenAPI delta 文档化（§9）；枚举与路径无矛盾 |
| **Mo-解析** | `packages/solver-opt/` 可运行最小 NSGA；analytic 评估主路径；写出精简帕累托；fixture 可复现（固定 seed） |
| **Mo-后端** | optimize 入队/轮询/**cancel**/resultRef/artifacts；payload 校验；api 进程无 NSGA |
| **Mo-前端** | fire+poll；帕累托图；选个体 apply；非阻塞 |
| **Mo-驱动** | 提供（或 stub）objective adapter 所需度量出口；**不**实现 NSGA 核心 |
| **Mo-测试** | 冒烟：enqueue →（可选 cancel）→ succeeded → pareto JSON schema 通过；不宣称误差达标 |
| **Mo-有限元** | stretch spot FEM 文档钩子即可；非门禁 |
| **Mo-运维** | optimize worker 可调度；库选型进镜像而非宿主机 |

阶段对齐（02 Q4 验收相关句）：「热闭环与 NSGA-II 各有可演示样例」→ Q4-9 侧以 **analytic（± drive per F3）Pareto 可演示** 为门禁解读；完整热–力入环不挡。

---

## 8. 开放分叉（仅列真实议题 · 等 Motor）

> **勿发明 Motor 决策。** 下列为架构默认建议；Motor 追认前不升格为已拍板。

| # | 议题 | **架构默认（建议）** | 备注 |
| --- | --- | --- | --- |
| **F3** | Q4 门禁是否要求 **驱动耦合目标**，或 **analytic-only Pareto 演示** 即够 | **analytic-only 演示足够过 Q4-9 样例门禁**；`analytic+drive` 为驱动就绪后的增强，不挡「NSGA 可演示样例」 | 与 [驱动后处理.md](./驱动后处理.md) Q4-1…6 进度解耦 |
| **F4** | 包名 `packages/solver-opt` vs `packages/optimizer` | **采纳 `packages/solver-opt/`**（与 `solver-analytic` / `solver-fem` 前缀一致） | 若 Motor 选 `optimizer`，立包前改名一次，避免双包 |

已关闭、不重开：

| 项 | 状态 |
| --- | --- |
| jobType 名称 `optimize` | OpenAPI/API **已占位**；本锁定确认语义 |
| 外层必须异步 Jobs | 与 Q3 FEM 同规则；架构钉死 |
| 不 overload analytic/fem 做外环 | 架构钉死 |
| Q3 F1 thinning 精神 | 已由 Motor 拍板；优化侧复用 |

---

## 9. OpenAPI delta（建议 · 本提交可不改大文件）

> 优先在本 § 文档化；大块改 `openapi-v1.yaml` 可另 PR。枚举已含 `optimize`，**无 JobType 冲突**。

建议增量：

1. **`OptimizeJobPayload`** schema：`projectId?`、`memsRef?`、`variables[]`、`objectives[]`、`constraints[]?`、`nsga{popSize,generations,seed}`、`evaluatorProfile`。
2. **`JobCreate.payload`**：`oneOf` 增加 `OptimizeJobPayload`（与 `FemJobPayload` 并列）；description 写明 `jobType=optimize` 必须符合该形状。
3. **`Job.resultRef` description**：增补  
   `optimize → solver/optimize/jobs/{jobId}/manifest.json`（artifacts 列 `results/optimize/{jobId}/…`）。
4. **`POST /jobs` 说明**：将「optimize：Q4 占位」改为「optimize：Q4-9 NSGA-II 异步主路径；禁止 sync；见本边界稿」。
5. **`OptimizeManifest` / `ParetoResults`**（可先 draft 于 `packages/solver-opt/api/*.schema.json`，OpenAPI `$ref` 随后）。
6. **Cancel**：若尚未暴露独立 `POST /jobs/{id}/cancel`，在 Jobs 合同中明确 cancel 语义（状态→`cancelled`）；MVP 必达。
7. **Artifacts**：沿用 FEM L4 list/get；path 前缀允许 `solver/optimize/`、`results/optimize/`。

活代码已知缺口（非本文件修复范围）：

| 位置 | 现状 | Q4-9 期望 |
| --- | --- | --- |
| `apps/api/.../jobs.py` | `optimize` 保持 queued 占位 | 入队 Celery optimize worker + cancel |
| `packages/solver-opt/` | **不存在** | Mo-解析立包（F4 确认后） |
| `JobCreate` 校验 | optimize 自由 dict | 渐进强制 `OptimizeJobPayload` |
| mems-schema `solver/` 表 | 仅 analytic / fem | 增 `solver/optimize/` 行（草案谱系；不改 01/02） |

---

## 10. 跨链接速查

| 文档 | 用途 |
| --- | --- |
| [Q3-轴向与FEM边界.md](./Q3-轴向与FEM边界.md) | Jobs 异步 UX、resultRef、角色边界范本 |
| [Q3-F1-结果精简.md](./Q3-F1-结果精简.md) | thinning / 禁止全场默认回灌 |
| [openapi-v1.yaml](./openapi-v1.yaml) | `JobType`、`/jobs`、Fem* 对照；optimize delta 落点 |
| [驱动后处理.md](./驱动后处理.md) | Map / ripple / 损耗；驱动不拥 NSGA |
| [解析范围.md](./解析范围.md) | analytic 求值金标；opt 另包调用 |
| `docs/02` Q4-9 | Owner = Mo-架构 / Mo-解析；交付任务定义 + 帕累托 |

---

*草案结束。F3/F4 等 Motor 追认后方可标「已拍板」；升格或改包名/门禁解读须 Motor 确认。**勿改 docs/01、docs/02 正文。***
