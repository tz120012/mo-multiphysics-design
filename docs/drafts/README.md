# docs/drafts — Gate0 / Q1 / Q2 / Q3 架构草案

本目录存放 **Mo-架构** 在不改动冻结源的前提下提交的契约与评审草稿。

## 冻结源（勿在此目录外擅自改写）

- `docs/01-任务书-v2.md` — 产品与技术栈真理源
- `docs/02-阶段任务拆解与门禁.md` — 阶段任务与门禁真理源

## 本批评审与 Q1 契约草案

| 文件 | 说明 |
| --- | --- |
| [G0-1-冻结评审.md](./G0-1-冻结评审.md) | Mo-架构对 G0-1（01/02 冻结）的评审结论 |
| [mems-schema-v1.md](./mems-schema-v1.md) | Q1 `.mems` schema **v1 草案**（`memsSchemaVersion: "1.0.0-draft"`） |
| [geometry-mems-字段对照.md](./geometry-mems-字段对照.md) | geometry ↔ `.mems` 字段对照（字段级映射权威；极数/双轨已裁决） |
| [裁决-geometry-mems-poleCount.md](./裁决-geometry-mems-poleCount.md) | Mo-架构裁决：`poleCount` + 双轨版本 KEEP |
| [openapi-v1.yaml](./openapi-v1.yaml) | Mo Platform API OpenAPI 3.1 **v1 草案**（`1.0.0-draft`） |
| [history-契约-q1-6.md](./history-契约-q1-6.md) | Q1-6 Undo/Redo **最小契约**（客户端权威线性栈 + `history/stack.json`） |
| [裁决-Q2-材料typed-curves与Motor采纳.md](./裁决-Q2-材料typed-curves与Motor采纳.md) | Motor 采纳 `3c34f1c`；typed curves 目标 + meta 过渡追认 |
| [Q2-材料与解析边界.md](./Q2-材料与解析边界.md) | **Q2 锁定**：Materials API CRUD + Wasm/analytic 双轨部署边界 |
| [Q3-轴向与FEM边界.md](./Q3-轴向与FEM边界.md) | **Q3 锁定**：轴向解析 + `solver-fem` 授权 + Jobs fem + 结果精简 |
| [Q3-F1-结果精简.md](./Q3-F1-结果精简.md) | **F1 书面**：thinning 职责、resultRef、/field 三件套、heat-proxy 口径（不宣称 ≤3%） |
| [Q4-7-热闭环-FEM损耗输入.md](./Q4-7-热闭环-FEM损耗输入.md) | **Q4-7**：FEM 损耗输入契约 + 热闭环迭代记录形状（LPTN 主责解析；`pending_calibration`） |
| [Q4-8-轴向磁拉力.md](./Q4-8-轴向磁拉力.md) | **Q4-8**：AF 轴向磁拉力/变形/轴承载荷专项报告草案（占位标量；磁静力学后置） |
| [Q4plus-5-磁静力学与轴向真值.md](./Q4plus-5-磁静力学与轴向真值.md) | **Q4+-5**：dry-run / heat-proxy / magnetostatic 分界 + 轴向真值路径壳（禁 ≤3%） |
| [Q4-10-压测与私有化.md](./Q4-10-压测与私有化.md) | **Q4-10**：压测与私有化开闸备案（运维） |
| [Q4+-1-G3校准计划.md](./Q4+-1-G3校准计划.md) | **Q4+-1**：指针 → 正式稿 [G3-校准计划](../qa/G3-校准计划.md)（tip 31c6597 + 解析确认 5df616d） |
| [Q4+-4-AF-Wasm.md](./Q4+-4-AF-Wasm.md) | **Q4+-4**：Wasm AF+PMSM 可演示最小路径（路径 A；不对标 ≤5%；金标仍 Python） |

其他范围笔记（几何 / 解析 / FEM / 驱动后处理等）可并存于本目录，**均不替代** 01/02。
Q2 解析开放项（Rust 偏好）已在 [解析范围.md](./解析范围.md) §6 勾选关闭，细节以 Q2 边界草案为准。
Q3 FEM / 轴向细节以 [Q3-轴向与FEM边界.md](./Q3-轴向与FEM边界.md) 为准；[FEM范围.md](./FEM范围.md) 为有限元侧笔记并已指针升级。

| [Maxwell-first统一工程模型与实时视口.md](./Maxwell-first统一工程模型与实时视口.md) | **架构建议稿**：UEM + 参数驱动 Three 视口；Maxwell-first / 教学后置；Motor 已拍 A1+B1+C2+D1 |
| [Q6-FEM-改参再触发.md](./Q6-FEM-改参再触发.md) | **Q6**：改参→显式再 submit FEM；组装在 FE/API；heat-proxy≠MS；不扩 F2 |
