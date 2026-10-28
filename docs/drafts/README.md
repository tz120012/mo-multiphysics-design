# docs/drafts — Gate0 / Q1 架构草案

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

其他范围笔记（几何 / 解析 / FEM / 驱动后处理等）可并存于本目录，**均不替代** 01/02。
