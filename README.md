# Mo — 电机多物理场智能设计平台

**Mo** 是面向无人机 / eVTOL / 高功率密度电机场景的**云端 Web、免安装**多物理场智能设计软件。支持径向与轴向磁通拓扑，集成秒级解析求解与云端高精度 FEM，并以无人机电调驱动对比、热–力耦合与多目标优化为特色；**ACIM（感应电机）为一等公民**，与 BLDC / PMSM 并列。

## 技术栈（锁定）

| 层 | 选型 |
| --- | --- |
| 前端 | Vue 3 + TypeScript + Element Plus + Three.js |
| 后端 | FastAPI + Celery + Redis + PostgreSQL |
| 解析 / Wasm | WebAssembly（解析 MEC / 多平面 / ACIM 等效电路） |
| FEM | Elmer / GetDP（2D / 3D，云端调度） |

## 文档

- [01-任务书-v2](docs/01-任务书-v2.md) — 背景目标、拓扑×机型矩阵、四大模块、里程碑与风险
- [02-阶段任务拆解与门禁](docs/02-阶段任务拆解与门禁.md) — Gate0 → Q1 → Q2 → Q3 → Q4 门禁与角色交付
- [03-用户故事与MVP](docs/03-用户故事与MVP.md) — 史诗、用户故事与近端优先级切片
- [04-验收标准-Gate0与Q1](docs/04-验收标准-Gate0与Q1.md) — Gate0/Q1 可勾选验收与角色确认

## 门禁原则

**未通过当前 Gate / 阶段验收，且未经 Motor 签字，不得开启下一阶段业务代码。**

## 隔离说明

本仓库（`/workspace/mo-platform`）**独立**维护。禁止改动 `low-altitude-platform` 及其他现有项目的仓库、同事工作区与流水线。
