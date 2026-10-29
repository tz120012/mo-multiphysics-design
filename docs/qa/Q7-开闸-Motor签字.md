# Q7 开闸 — Motor 签字

| 字段 | 内容 |
| --- | --- |
| 角色 | Motor · Mo 项目经理 |
| 日期 | 2026-10-29 Asia/Shanghai |
| 正式阶段名 | **Q7 / Maxwell 体感加深** |
| 产品冻结 tip | **`b831208`** · [Q7-范围冻结](Q7-范围冻结.md) |
| 架构简评 | **零新 API**（FE 同壳加深 + 既有 materials / jobs(+artifacts) / drive / geometry.rebuild / solver.analytic）；5 条重大分叉须另报 Motor |
| 前置 | Q6-6 tip **`b4cebf8`** |
| 基线 | MVP / `v1.0.0` @ **`fbb0baa`**；**不重开** |

## 1. 拍板结论

1. **采纳**产品正式名 **Q7 / Maxwell 体感加深**。
2. **开闸**：允许按冻结 IN#1–4 写业务代码（仅 `/workspace/mo-platform`）。
3. **契约**：**默认零新 API**；服务切分与 Q5-1 / Q6 边界不动。下列须 **Motor 另拍板** 才可进范围：材料另起 REST、后处理改 mems/files 主路径、rebuild 改 Celery/Jobs 或新异步几何 API、新 `/excitation/*`、网格完整向导入 IN。
4. **验收** = 体感加深（材料/激励可验收 · 后处理同壳 · 3D 体感抬升）；**≠** 全功能 Maxwell；**≠** US-084；**≠** 扩大 F1/F2。
5. 红线：fixture ≠ 建模完成；heat-proxy ≠ 磁静力学；禁 demo 别名回潮；网格默认只读降级；**未测过不得放行**；**不打新 tag**。

## 2. IN（冻结）

1. 材料：区域→`mat-*` 目录选择/绑定；检视后求解  
2. 激励：步骤名「激励」= OP/工况（+可选 drive 草稿）进 UEM  
3. 后处理同壳：改参→再求解后结果/场量入口在 Workspace 同工程可见  
4. 参数化 3D 体感抬升（Q6 rebuild 路径）

## 3. OUT

US-084；扩 MVP 矩阵；整机 ≤5%/≤3% / 外推 F1/F2；改核心求解；非 mo-platform；重开 v1.0.0；完整网格向导；全功能 Maxwell 宣称。

## 4. 下发

| 角色 | 动作 |
| --- | --- |
| Mo-产品 | 跟踪表改「进行中」；口径守门 |
| Mo-架构 | 守零新 API；重大分叉报 Motor |
| Mo-前端 | Q7-1…4 主实现（C2 单壳内加深） |
| Mo-后端 | 配合既有 materials API；无新端点除非 Motor 另批 |
| Mo-驱动 | Q7-2 激励/drive 草稿同壳 |
| Mo-有限元 | Q7-3 同壳后处理对接 jobs/artifacts；降级明示 |
| Mo-几何 | Q7-4 视口/rebuild 体感（不改 HTTP 最小集） |
| Mo-测试 | 出 Q7-C1…C5 冒烟清单；未测过不得放行 |
| Mo-运维 | tip 进 compose web（必要时 api）与运行态一致 |

## 5. 签字

**Motor：同意开闸 Q7 / Maxwell 体感加深。**

---

*Motor · 开闸 · 产品 `b831208` · 前置 Q6-6 `b4cebf8`*
