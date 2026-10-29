# Q6 架构分叉 — Motor 拍板

| 字段 | 内容 |
| --- | --- |
| 日期 | 2026-10-29（Asia/Shanghai） |
| 依据 | 用户 Maxwell-first；Q6 开闸 `cc3b2d1`；架构建议 `6dafa91`；几何盘点（rebuild_live 可支撑实时） |
| 建议稿 | [Maxwell-first统一工程模型与实时视口](../drafts/Maxwell-first统一工程模型与实时视口.md) |

## 分叉结论

| 分叉 | 裁定 | 说明 |
| --- | --- | --- |
| **F-A** | **A1** | 浏览器本地几何重建为主；后端 `rebuild_live_geometry` 作金标/降级 |
| **F-B** | **B1** | UEM = 纯 mems 子集投影 + 派生字段；不另起 uemSchema |
| **F-C** | **C2** | **单 Workspace 壳 + 内嵌面板**走 Maxwell 经典链（几何→材料→激励→网格→求解→后处理）。旧多路由可暂作深链/重定向，**不得**以「多页+共享 Pinia」作为 Q6 验收达标口径 |
| **F-D** | **D1** | P0 先薄后端 rebuild 打通参数→descriptor→Three，并行浏览器移植；再切本地为主 |

## 与产品冻结对齐

- IN#1 一站式工作台 → **C2**（非 C1）
- IN#2 参数驱动 3D → A1+D1 + 几何 `rebuild_live_geometry` 真接线
- IN#3 改参→求解闭环 → UEM 同会话显式求解；禁拖拽耦合 FEM

## 授权开干

- Mo-架构：按本裁定更新建议稿状态为「Motor 已拍」
- Mo-后端：薄 `rebuild` API（封装 geometry live）
- Mo-几何：P0 驱动字段补齐 +「改关键参→prims 必变」一致性测试；对接 FE
- Mo-前端：C2 工作台壳 + 订阅 meshDescriptor；禁 fixture=建模完成

F1/F2 有限不变；不改求解核心；不重开 v1.0.0。

**Motor 签字：A1 + B1 + C2 + D1。**
