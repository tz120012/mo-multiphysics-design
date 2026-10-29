# Q6 FE 冒烟清单 — C2 工作台

| 字段 | 内容 |
| --- | --- |
| 范围 | `apps/web` 工作台壳。不改几何包、求解核心、`docs/01`、`docs/02` |
| 架构 | A1+B1+C2+D1（`be6ed88`）。契约 `docs/drafts/Q6-UEM与几何rebuild契约.md`（`55b1255`） |
| 解析闭环 | `docs/drafts/Q6-解析-改参再求解闭环.md`（`50dacc9`）：显式求解，不走 Jobs analytic |
| 状态 | **待测**。本文件是前端自检步骤，不是放行结论 |

不把 workspace / public fixture 写成建模完成。不宣称整机误差门禁。heat-proxy 不是磁静力学。网格步不是 Maxwell 网格生成完成。

## 主路径

1. 登录后只从「工程」进入「工作台」。顶栏不再并列解析 / 场量 / 驱动。
2. `/workspace?projectId=` 打开同一会话。左侧顺序为：几何、材料、激励、网格、求解、后处理。
3. `/analytic`、`/axial`、`/field`、`/drive`、`/compare` 重定向回工作台，并保留 `projectId`。
4. 有 `projectId` 时先读 `GET .../mems/files/geometry/params.json`，失败再整包抽出该成员，再失败才是 fixture。

## 几何重建

1. 改槽数、极数、磁钢厚度或盘厚后约 200 ms，浏览器发出 `POST /api/v1/geometry/rebuild`，body 含 `topology`、`machineType`、`params`（camel，mm）。
2. HTTP 200 且返回可用 `meshDescriptor` + `geometrySummary`：`dataSource=live`，清 `geometryDirty`，视口图元变化（槽/极数量、盘厚或磁钢径向厚度）。可选 `paramsHash` 只用于比较，不要求一定存在。
3. 非 2xx，或 200 但描述符为空：视口改用 `public/mesh`，横幅为「样例/fixture · 非建模完成」。前端不用这份 JSON 假装 200。
4. `?source=fixture` 一开始就不请求 rebuild，横幅同上。
5. 网格步只读 profile / meta，并写明「非网格生成完成 / not Maxwell mesh generation complete」。

## 求解

1. 材料步只写区域 → materialId。激励步只写工况和可选驱动草稿。两步都不触发 rebuild，也不提交 Jobs。
2. 求解步按钮「求解」用当前 `geometrySummary` + 材料 + 工况，走既有 `solveRadial` / `solveAxial`（Wasm → sync → fixture）。
3. 结果进会话，面板能看到转矩和路径。fixture / mock 要标成解析降级。
4. 改几何并等 rebuild 成功后，再点一次求解，结果或状态应更新。重建进行中按钮不可用。
5. 没有 live `geometrySummary` 时不能把 fixture 网格拿去求解。

## 后处理

1. 无 jobId 时不把场图 public fixture 当作本壳结果。
2. 填入 FEM `jobId` 后，本壳嵌入既有场图页，数据仍走 Jobs artifacts。

## 构建

```bash
cd apps/web && pnpm build
```
