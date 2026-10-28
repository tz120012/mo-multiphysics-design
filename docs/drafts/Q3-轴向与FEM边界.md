# Q3 轴向解析 + FEM 调度 + 结果精简 — 架构锁定

| 项 | 值 |
| --- | --- |
| 状态 | **Q3 架构锁定草案**（Mo-架构裁决；勿擅自重开除非与 01/02 矛盾） |
| 日期 | 2026-10-28（Asia/Shanghai） |
| 作者 | Mo-架构（Mo-架构 worker） |
| 依据 | `docs/01-任务书-v2.md` §2 / §3 模块二·三 / §6；`docs/02` Q3-1…Q3-7 |
| tip 基准 | Motor 签 Q2 通过并开 Q3：`5059b51`；本锁定相对其后 tip 提交 |
| 配套 | [openapi-v1.yaml](./openapi-v1.yaml)、[mems-schema-v1.md](./mems-schema-v1.md)、[解析范围.md](./解析范围.md)、[FEM范围.md](./FEM范围.md)、`packages/solver-analytic/api/solve.schema.json`、`packages/solver-fem/` |
| 冻结源 | **不修改** `docs/01` / `docs/02` 正文 |

> 本文件锁定：轴向多平面解析契约与部署路径；`packages/solver-fem` 授权与所有权；Jobs `jobType=fem` 必选异步形态；结果精简回传路径与格式；各角色 Q3 验收条。开放分叉见 §8（升级 Motor，不由架构擅自拍板）。

---

## 1. Owner 总表

| Owner | Owns（Q3） | Does not |
| --- | --- | --- |
| **Mo-解析** | 轴向多平面 Python 金标（`packages/solver-analytic/axial_planes/`）；同契约 `SolveRequest`/`SolveResult`（`topology: AF`，机型 MVP=**PMSM**）；解析↔FEM 对照字段 | Elmer/GetDP 内核；容器；FE 云图 |
| **Mo-有限元** | `packages/solver-fem/`：前处理 / 网格描述 / 求解模板、job payload & result index schema、**结果精简（thinning）** 逻辑与样例 | 宿主机安装 Elmer/GetDP/Gmsh；`apps/api` 进程内跑求解 |
| **Mo-运维** | Elmer / GetDP / Gmsh **容器镜像** + Celery FEM worker 镜像；compose/CI 拉起工人 | 模板数学内容；Jobs API 形状发明 |
| **Mo-后端** | `POST/GET /jobs`：`jobType=fem` 入队/轮询；`resultRef` 持久化；`.mems` PUT/GET 写入路径协调 | 将 Elmer 嵌进 FastAPI 进程；浏览器直吐全场 |
| **Mo-前端** | 触发 FEM Jobs（fire + poll/subscribe + 进度）；消费 **精简产物** 可视化（Q3-6）；AF 全流程 UI（几何→解析→FEM 入口）；RF 交互解析仍以径向 Wasm 为主 | 长轮询阻塞唯一 UX；下载全网格当默认 |
| **Mo-几何** | 网格输入描述符 / CAD 导出挂钩（供 FEM 前处理） | 求解内核；精简策略本体 |
| **Mo-测试** | Q3-7 FEM Benchmark / 冒烟；解析对照 | 发明 API / 目录布局 |
| **Mo-架构** | 本草案 + OpenAPI / mems Q3 delta | 大块业务算法 |

---

## 2. 轴向解析（Q3-1 / Q3-2）

### 2.1 契约

| 项 | 锁定 |
| --- | --- |
| JSON 契约 | **同一** `packages/solver-analytic/api/solve.schema.json`（`SolveRequest` / `SolveResult`） |
| `topology` | `AF`（与 `RF` 并列；不得另起 AF-only schema） |
| 机型 MVP | **PMSM** 先行；AF BLDC / AF ACIM 按任务书「随后」，不进 Q3 MVP 硬门禁 |
| 算法落点 | Python 金标优先：`packages/solver-analytic/axial_planes/`（或等价子包）；`meta.solver` 已含 `axial_planes` |
| `.mems` 快照 | 仍写入 **`solver/analytic/`**（与径向一致；不新建 `solver/axial/`） |

### 2.2 部署路径（AF vs RF）

| 拓扑 | 交互主路径（Q3 MVP） | 备选 | Wasm |
| --- | --- | --- | --- |
| **RF** | 客户端 **Wasm**（Q2 已 PASS） | sync `POST /solver/analytic/solve`；Jobs `analytic` | **硬门禁已满足** |
| **AF** | **Jobs `analytic` 或 sync** `/solver/analytic/solve`（BE 接真内核或本地 Python）均可 | — | **不要求** Q3 MVP 硬门禁；**推荐** Wasm AF 为 stretch / fast-follow |

规则：

1. 交互 FE **不得**以「阻塞式长轮询 Jobs」作为唯一 UX（AF 解析亦同：可展示进度，但须可取消/可离开页）。
2. 径向 Wasm 保持 FE 主路径；AF UI 在 Wasm AF 落地前走 sync / Jobs。
3. Python `solver-analytic` 始终为金标 / CI / Benchmark 对照源。

### 2.3 验收条（解析 / 前端 / 几何）

| 角色 | Accept bar |
| --- | --- |
| **Mo-解析** | AF+PMSM 多平面可运行；同 schema 进出；fixture 可复现；快照可写入 `solver/analytic/` |
| **Mo-前端（Q3-2）** | 轴向 PMSM：几何→解析→FEM 入口串联；解析调用 sync 或 Jobs；不阻塞整页 |
| **Mo-几何** | AF 几何摘要可供 `SolveRequest.geometry` / FEM mesh 描述符消费 |

---

## 3. FEM 包授权与内核（Q3-3…Q3-5）

### 3.1 `packages/solver-fem/` — Gate0 推迟已解除

| 项 | 锁定 |
| --- | --- |
| 包路径 | **`packages/solver-fem/`**（现已授权立包） |
| 内容 | 前处理/网格/求解 **模板**；job payload schema；result index / manifest schema；thinning 辅助；样例工程描述 |
| **禁止** | 托管 Elmer/GetDP/Gmsh **二进制**；要求 box **宿主机/系统级**安装 |
| Gmsh | **仅容器内**；与 Motor Gate0 批注一致 |
| 内核 | **Elmer / GetDP**（任务书锁定）；变更须评审 |

推荐目录（可演进，勿改名包根）：

```
packages/solver-fem/
  README.md
  api/                 # JSON Schema：FemJobPayload、manifest、result index
  templates/           # Elmer/GetDP 输入模板（按机型×维度）
  schemas/             # 可选：mesh descriptor、compare 字段
```

### 3.2 机型 × 维度顺序（Motor 已批注，不重开）

| 线 | 顺序 / 最小路径 |
| --- | --- |
| 径向 2D | **PMSM → ACIM → BLDC** |
| 轴向 3D | **AF PMSM** 最小可重复作业（Q3-5） |

### 3.3 内核落地建议（分叉见 §8）

| 内核 | Q3 MVP 建议 |
| --- | --- |
| **Elmer** | **优先**：Q3-4 / Q3-5 跑通路径 |
| **GetDP** | 模板 / payload 枚举保留；**stub 可接受**，不作为 Q3-4/5 硬阻塞（升级 Motor 若要求双核同验） |

### 3.4 验收条（有限元 / 运维）

| 角色 | Accept bar |
| --- | --- |
| **Mo-有限元** | `solver-fem` 含径向 2D PMSM 模板 + 轴向 3D AF-PMSM 最小路径；thinning 写出 §5 路径；无宿主机装内核 |
| **Mo-运维** | Elmer（+Gmsh）容器可被 Celery worker 调用；GetDP 镜像可后置或 stub；compose 可提交作业并取回 |
| **Mo-几何** | 提供 mesh 输入描述符 / CAD 挂钩文档或样例 |

---

## 4. Jobs / API（FEM **始终**异步）

### 4.1 总则

1. **交互 FEM 禁止**以「同步长请求堵死 UI」为唯一路径：必须 **fire Jobs → poll/subscribe → 进度**。
2. `POST /jobs` 且 `jobType=fem` 为 Q3 FEM **主入口**（不像 analytic 在 Q2 可选）。
3. **禁止**在 `apps/api` 进程内嵌入 Elmer/GetDP。
4. Job 状态枚举不变：`queued | running | succeeded | failed | cancelled`。
5. 可选 `GET /jobs/{id}/artifacts`：**Q3 MVP 可不实现**；MVP = `resultRef` + `.mems` GET 即可。

### 4.2 `jobType=fem` payload（必填形状）

| 字段 | 类型 / 枚举 | 说明 |
| --- | --- | --- |
| `projectId` | uuid | 与 Job 顶层一致；payload 内可冗余校验 |
| `topology` | `RF` \| `AF` | |
| `machineType` | `BLDC` \| `PMSM` \| `ACIM` | Q3 径向优先 PMSM；轴向 PMSM |
| `dim` | `2d` \| `3d` | 径向主 2d；轴向主 3d |
| `solverKernel` | `elmer` \| `getdp` | 见 §3.3 / §8 |
| `meshProfile` | string | 模板/剖面 id（如 `rf_pmsm_2d_default`） |
| `operatingPoint` | object **或** ref | 工况内联或指向 `.mems` / 工程字段 |
| `materials` | refs 数组/对象 | 材料引用（与 Q2 materials 对齐） |
| `templateId` | string，可选 | `packages/solver-fem/templates` 内 id |

OpenAPI：`FemJobPayload`；顶层 `JobCreate` 在 `jobType=fem` 时 `payload` 应符合该 schema（实现侧校验可分阶段收紧）。

### 4.3 `resultRef` 约定

成功后 `resultRef` 指向 `.mems` 内相对路径（或随后对象存储 URI，见 §8），推荐主指针：

```text
solver/fem/jobs/{jobId}/manifest.json
```

manifest 内 `artifacts[]` 再列出 `results/fem/{jobId}/...` 相对路径。允许 `resultRef` 直接指向 `results/fem/{jobId}/` 目录（实现二选一须在 worker 与 BE 间一致；**默认推荐 manifest 指针**）。

### 4.4 验收条（后端 / 前端）

| 角色 | Accept bar |
| --- | --- |
| **Mo-后端** | `jobType=fem` 入队至 Celery FEM 队列（非 api 进程求解）；轮询状态；succeeded 时持久化 `resultRef`；校验必填 payload 字段（可渐进） |
| **Mo-前端** | 触发 fem job；进度 UI；成功后按 manifest 拉精简产物；**不以**全场网格为默认下载 |

---

## 5. 结果精简（mandatory）

### 5.1 原则

1. **默认禁止**将全网格 / 全场体积数据灌进浏览器。
2. Worker（Mo-有限元逻辑 + Mo-运维容器）写出索引 + 精简产物；FE（Q3-6）**只消费**精简产物。
3. 全场 / 重网格留在 worker 侧或对象存储；Q3 若极小可暂存 mems zip（见 §8）。

### 5.2 路径布局

```text
solver/fem/jobs/{jobId}/manifest.json   # 状态、内核、维度、标量摘要、产物清单
results/fem/{jobId}/                    # 切片 / 等值面网格 / 预览图 / 关键标量
```

可选并存（工况定义，非浏览器大数据）：

```text
solver/fem/cases/{caseId}.json          # 网格句柄、BC、模板引用等
solver/fem/index.json                   # 工程级作业索引（可选）
```

### 5.3 `manifest.json` 最小字段

| 字段 | 说明 |
| --- | --- |
| `jobId` | uuid |
| `status` | 与 Job 对齐 |
| `solverKernel` | `elmer` \| `getdp` |
| `topology` / `machineType` / `dim` | 回显 |
| `scalars` | 关键标量摘要（转矩、损耗等，便于列表 UI） |
| `artifacts` | `{ path, role, format, bytes? }[]`，`path` 相对 `.mems` 根 |
| `createdAt` / `updatedAt` | ISO-8601 |

### 5.4 Q3 允许的浏览器侧格式（钉死一套）

| role | 格式 | 说明 |
| --- | --- | --- |
| `scalars` | **JSON** | 关键标量 / 曲线抽样 |
| `surface` / `slice` | **glTF / GLB** | 等值面或切片表面；对齐 Three.js |
| `preview` | **PNG**（可选 WebP） | 预览图 |
| （禁止默认） | 全场 VTK/vtu 直灌浏览器 | 可留 worker；若提供须显式「高级下载」且非 Q3-6 默认路径 |

> 不采用「VTK.js 碎片 + glTF 双轨并行」作为 Q3 MVP，以免 FE 分叉；若 Motor 后续要求 VTK.js，走变更评审。

### 5.5 体积预算

| 项 | 指导 |
| --- | --- |
| 单作业浏览器路径合计 | **软顶 ~5–20 MB**（manifest 所列 preview 类产物） |
| 超预算 | thinning 降采样 / 少切片；全场勿进默认 mems 浏览器路径 |
| 校验 | Q3-6 / Q3-7 冒烟检查「默认加载路径无全场」 |

### 5.6 验收条（精简）

| 角色 | Accept bar |
| --- | --- |
| **Mo-有限元** | worker 写出 manifest + `results/fem/{jobId}/`；默认无全场 |
| **Mo-前端** | 仅渲染 scalars + glTF/PNG；文档化加载顺序 |
| **Mo-测试** | Benchmark 报告含精简策略雏形与体积抽查 |

---

## 6. 与解析对照（Q3-7 协作）

| 项 | 锁定 |
| --- | --- |
| 对照字段 Owner | **Mo-解析** 定义「解析侧导出」；**Mo-有限元** 在 manifest.`scalars` / compare 块对齐同名物理量 |
| 误差宣称 | 任务书 FEM ≤3% **待校准**；未完成标杆前不得宣称达标 |
| 包 | 对照逻辑不进 `apps/api` 内核 |

---

## 7. 各角色验收条汇总（门禁对齐）

| 02 任务 | 角色 | 本锁定 Accept bar（摘要） |
| --- | --- | --- |
| Q3-1 | Mo-解析 | AF 多平面 Python 金标 + 同 schema |
| Q3-2 | Mo-几何 / Mo-前端 | AF PMSM 全流程；解析 sync/Jobs；FEM 入口 |
| Q3-3 | Mo-有限元 / Mo-运维 | 容器 + Celery 工人；可提交并取回 |
| Q3-4 | Mo-有限元 | 径向 2D 模板（PMSM 首） |
| Q3-5 | Mo-有限元 | 轴向 3D AF-PMSM 最小路径 |
| Q3-6 | Mo-前端 | 仅精简产物可视化 |
| Q3-7 | Mo-测试 | Benchmark + 与解析对照报告 |

阶段验收（02）：轴向 PMSM 解析 + 至少一次成功 FEM；径向至少一种机型 2D FEM 样例；大数据回传策略有文档与实现雏形；Motor 签字开 Q4。

---

## 8. 开放分叉（升级 Motor，架构不擅自发明答案）

| # | 分叉 | 架构建议（非最终拍板） |
| --- | --- | --- |
| F1 | **大 FEM blob**：Q3 MVP 对象存储 vs **仅 mems-zip** | **建议** Q3 MVP：精简产物进 mems + `resultRef`；超软顶的全场留 worker 磁盘；对象存储 + 签名 URL 作 fast-follow |
| F2 | **GetDP** 是否 Q3 MVP 必验 | **建议** Elmer-first 跑通 Q3-4/5；GetDP 保留枚举与模板 stub，双核同验不阻塞 Q3 签字 |

---

## 9. 对活代码的已知缺口（非本提交修复范围）

| 位置 | 现状 | Q3 期望 |
| --- | --- | --- |
| `apps/api/app/routers/jobs.py` | `fem` / `optimize` 仅 `queued` 占位 | fem 入队真实 Celery FEM worker |
| `JobCreate.payload` | 自由 `dict` | fem 时按 `FemJobPayload` 校验（可渐进） |
| `packages/solver-analytic/axial_planes/` | README 仍写 Gate0 空目录 | Q3-1 由 Mo-解析填算法（本锁定已授权开工） |
| `packages/solver-fem/` | Gate0 曾禁止立包 | **已授权**；本提交立包骨架 |

---

*草案结束。升格或改内核/格式钉选须 Motor 确认；01/02 正文勿改。*
