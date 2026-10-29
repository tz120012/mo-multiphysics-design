# Mo Web（`apps/web`）

Vue 3 + TypeScript + Vite + Element Plus + Vue Router + Pinia 工程壳（Q1-3）。

深色工程软件风：石墨黑底、细分割线、青绿 / 琥珀点缀。Q6 主路径是单一 `/workspace` 工作台（几何→材料→激励→网格→求解→后处理），Three.js 视口订阅会话里的 meshDescriptor。

## 架构契约

| 文档 | 路径 |
| --- | --- |
| OpenAPI | `docs/drafts/openapi-v1.yaml`（`servers.url`: `/api/v1`） |
| MEMS 包边界 | `docs/drafts/mems-schema-v1.md` |

前端对齐要点：

- `MEMS_SCHEMA_VERSION` = **`1.0.0`**（工程列表展示同一常量）。后端 tip `8d9fc3b` 已钉契约；架构 tip `4b553f5`，`docs/drafts/Q5-5-契约1.0.0钉死.md`。读取仍接受 `1.0.0` 与 `1.0.0-draft`；新建与 mems 写入发出 `1.0.0`。钉 `1.0.0` ≠ MVP，≠ git tag `v1.0.0`。
- `topology`: `RF` \| `AF`；`machineType`: `BLDC` \| `PMSM` \| `ACIM`
- `VITE_API_BASE` 默认 `http://localhost:8000/api/v1`；业务调用用 `/auth/login`、`/projects` 等相对路径，**不要**再叠一层 `/api/v1`
- API 占位：`src/api/auth.ts`、`src/api/projects.ts`（当前 `Promise.reject('not wired')`）；工程列表仍用本地假数据

## 环境

- Node.js ≥ 20
- 包管理：优先 **pnpm**

## 安装

```bash
cd apps/web
pnpm install
cp .env.example .env   # VITE_API_BASE=http://localhost:8000/api/v1
```

## 开发

```bash
pnpm dev
```

默认 http://localhost:5173 。

### 冒烟步骤

1. 打开开发地址 → 未登录跳转 `/login`
2. 任意账号 / 密码登录（假登录，token → `localStorage`）
3. 进入 `/projects`（3 条假数据；拓扑显示中文 label，值为 `RF`/`AF`）
4. 「新建工程」对话框占位（本地 store，不调 API）
5. 「打开」或顶栏「工作台」→ `/workspace`：在同一壳内走经典链。几何改参会请求 `POST /geometry/rebuild`；失败或 `?source=fixture` 时视口标「样例/fixture · 非建模完成」
6. 退出或清 `mo_token` 后访问 `/projects` → 回 `/login`

## 构建

```bash
pnpm build
pnpm preview
```

## 目录要点

| 路径 | 说明 |
| --- | --- |
| `src/styles/tokens.css` | 色板 / 字体设计令牌 |
| `src/router/index.ts` | 路由 + 鉴权守卫 |
| `src/stores/auth.ts` | 假登录 / token |
| `src/stores/projects.ts` | 工程列表假数据（枚举对齐契约） |
| `src/api/client.ts` | axios，`baseURL` ← `VITE_API_BASE` |
| `src/api/types.ts` | Login*/Project*/MemsMeta 等最小类型 |
| `src/api/auth.ts` | `/auth/*` 占位 |
| `src/api/projects.ts` | `/projects/*`、mems、history 占位 |
| `src/layouts/AppLayout.vue` | 顶栏（含工作区入口） |
| `src/views/WorkspaceView.vue` | C2 工作台壳：步骤树 + Viewport3D + 属性 |
| `src/stores/projectSession.ts` | UEM 会话（几何 / 材料 / 激励 / 派生描述符） |
| `src/components/Viewport3D.vue` | Three.js 视口（OrbitControls / AxesHelper） |
| `src/lib/meshToThree.ts` | ring/sector → Mesh（mm→场景） |
| `src/types/mesh.ts` | mesh descriptor 类型（0.1.0-q1） |
| `public/mesh/` | 自 `packages/geometry/examples` 复制的权威 fixture |

## `/field` 数据源（Q4+-3）

页眉可见 `source=`。规则在 `src/views/FieldVizView.vue` 注释，对齐 `docs/drafts/Q4+-3-mems单文件与artifacts收口.md` §2。说明见 `docs/qa/Q4plus-FE-field-source.md`。

| 条件 | UI source | 数据 |
| --- | --- | --- |
| 无 `jobId` | `fixture` | public `/fem/rf_pmsm_2d_dryrun` |
| `?source=fixture` 且无 `jobId` | `fixture` | 同上，不请求 artifacts |
| `?jobId=` 且 `?source=fixture` | `job-fixture` | 同上（强制 fixture） |
| `?jobId=` 且 artifacts 列表非空，或 manifest/scalars/slice/preview GET 成功 | `job-artifacts` | `GET /api/v1/jobs/{id}/artifacts` 与 `.../artifacts/{path}` |
| `?jobId=` 且列表空或失败，同时关键 GET 404/不可达 | `job-fixture` | 降级 public fixture |

不使用 mems 整包或 `mems/files`。状态注记只写「不宣称误差达标」，不宣称 MVP。

磁静力学后处理（Q5-2，FEM tip `797ce67`）仍走上面的 artifacts / fixture 规则。`equationMode=magnetostatic` 或 `magnetostaticPathReady=true` 时侧栏为「磁静力学后处理」（含 `postprocess`、`axialForceN`、`magneticEnergyJ` 等）；`heat_proxy` 或旧 fixture 缺省标为 heat-proxy / 非磁静力学真值。`pending_calibration` 缺省视为未校准。说明见 `docs/qa/Q5-2-FE-field-magnetostatic.md`。

## 已知限制

- 鉴权接真 API（`POST /auth/login`）；token 存 `accessToken`
- 工程列表/新建接真 API；MEMS / history 仍可能未完全可用
- 开发态 `VITE_API_BASE=/api/v1` + vite proxy → `127.0.0.1:8000`
- 列表 `uiStatus` 为前端本地装饰，契约 `Project` 无此字段
- 工作台几何主路径是 `POST /geometry/rebuild`。public/mesh 只在失败或 `?source=fixture` 时出现，并标明非建模完成
- `/analytic` `/field` `/drive` `/axial` `/compare` 重定向进工作台步骤，不作为并列主路径
- mesh 为 ring/sector 挤出近似，非 Maxwell 网格生成完成
