# Q4-7 热闭环 — FEM 电磁损耗输入（Mo-有限元）

| 项 | 值 |
| --- | --- |
| 状态 | **书面契约草案 + 最小样例**（US-070；迭代收敛记录形状） |
| 日期 | 2026-10-28（Asia/Shanghai） |
| Owner | Mo-有限元（损耗输入 / 可选场侧校核）；**LPTN 主责 Mo-解析**；工况分损耗 **Mo-驱动** |
| 边界源 | [02-阶段任务拆解与门禁](../02-阶段任务拆解与门禁.md) Q4-7；[FEM范围.md](./FEM范围.md) §4；[驱动后处理.md](./驱动后处理.md) §3/§5；[Q3-F1-结果精简.md](./Q3-F1-结果精简.md) |
| 误差口径 | **`pending_calibration`**；**禁止宣称 FEM ≤3%**；heat-proxy ≠ LPTN、≠ 磁静力学电机解 |

> 闭环：电磁损耗 → LPTN → 温度 → 反馈 Br / 电阻温漂。本文只锁定 **FEM 侧损耗输入契约** 与演示用迭代记录形状；不抢 LPTN 实现。

---

## 1. 角色分工

| 角色 | 提供 | 不负责 |
| --- | --- | --- |
| **Mo-有限元** | 电磁损耗输入（`lossesW` / `lossBreakdown`）；可选场侧校核损耗；`resultRef` / `jobId` 指针 | LPTN 网络求解、温漂材料更新主循环 |
| **Mo-解析** | LPTN 热网、温漂反馈、迭代收敛主责 | Elmer 作业调度 |
| **Mo-驱动** | 工况分损耗功率（铁/铜/PM 涡流/导条/端环等时间平均或工况点） | FEM 网格与求解 |

当前 Elmer 路径仍是 **heat-proxy**（Q3 E2E）。**不得**把 heat-proxy 温度场当作 LPTN 结果。本契约可先接 **解析 / 驱动** 损耗；**FEM 真电磁损耗待磁静力学后置**。

---

## 2. 最小契约（JSON）

建议落在 `results/fem/{jobId}/scalars.json` 扩展字段，或并列小文件由 manifest `artifacts[]` 索引；**不强制新 API**（L4 artifacts 已由后端落地）。

```json
{
  "schemaVersion": "fem-scalars-v0",
  "pending_calibration": true,
  "lossesW": {
    "total": null,
    "iron": null,
    "copper": null,
    "pmEddy": null,
    "rotorBar": null,
    "endRing": null
  },
  "lossBreakdown": {
    "source": "analytic",
    "unit": "W",
    "notes": "placeholder; FEM EM losses pending magnetostatics"
  },
  "operatingPoint": {
    "rpm": 3000,
    "torqueNm": null,
    "T_ambientC": 25
  },
  "source": "analytic",
  "jobId": "00000000-0000-4000-8000-000000000001",
  "resultRef": "solver/fem/jobs/00000000-0000-4000-8000-000000000001/manifest.json"
}
```

| 字段 | 说明 |
| --- | --- |
| `lossesW` | 分项功率（W）；缺项可省略或 `null`；空对象 `{}` 表示尚未填充 |
| `lossBreakdown` | 可选元数据（单位、备注、分量定义） |
| `operatingPoint` | `rpm` / `torqueNm` / `T_ambientC` 等工况 |
| `source` | `fem` \| `analytic` \| `drive` — 标明损耗来源 |
| `jobId` / `resultRef` | 与 F1 manifest 对齐的指针 |
| `pending_calibration` | 恒为真，直至正式校准流程关闭 |

可选键名别名：`iron`≈铁损、`copper`≈铜损、`pmEddy`≈永磁涡流、`rotorBar`/`endRing`≈ACIM 导条/端环。驱动侧分损耗见 [驱动后处理.md](./驱动后处理.md)。

---

## 3. 与 F1 scalars / manifest 的衔接

1. **扩展** `results/fem/{jobId}/scalars.json`：在现有 `torqueNm` / `dryRun` / `pending_calibration` / `inputEcho` 旁增加 `lossesW`（及可选 `operatingPoint`、`source`）。  
2. **manifest.scalars** 可摘要 `lossesW.total`（若有）；完整分项仍以 `scalars.json` 为准。  
3. 不强制新 Job API；解析/驱动读 `resultRef` → `artifacts` → `scalars.json`。  
4. `thinning.py` dry-run / heat-proxy 默写 `lossesW: {}` 占位，**不**伪造电磁损耗数值。

样例（可选）：`packages/solver-fem/fixtures/q4_thermal_loss_contract.json`。

---

## 4. 闭环迭代记录（演示最小形状）

供 US-070「迭代收敛记录」演示；主责写入方可在解析侧 `.mems` 或协作目录落盘。每轮一条：

```json
{
  "schemaVersion": "thermal-loop-iter-v0",
  "pending_calibration": true,
  "iters": [
    {
      "iter": 0,
      "lossesIn": { "source": "drive", "lossesW": { "iron": null, "copper": null } },
      "tempsOut": { "windingC": null, "magnetC": null, "ambientC": 25 },
      "materialUpdate": { "BrFactor": 1.0, "resistivityFactor": 1.0 },
      "residual": null
    }
  ]
}
```

| 键 | 含义 |
| --- | --- |
| `lossesIn` | 本轮注入损耗（可带 `source`） |
| `tempsOut` | LPTN 输出温度（节点名由解析定义） |
| `materialUpdate` | Br / 电阻率等相对因子（解析主责） |
| `residual` | 收敛判据标量；未算则为 `null` |

**明确**：FEM heat-proxy 温度 **不是** `tempsOut`；`tempsOut` 只来自 LPTN（或解析占位）。

---

## 5. 现状与后置

| 项 | 现状 |
| --- | --- |
| Elmer | heat-proxy E2E；非磁静力学电机解 |
| FEM `lossesW` | 占位空对象 / null；`source` 可先为 `analytic`/`drive` |
| LPTN | Mo-解析主责；本文不实现 |
| 磁静力学后 | FEM 可填 `source: "fem"` 与场侧校核损耗 |

---

## 6. tip / 指针

| 文档 | 关系 |
| --- | --- |
| [FEM范围.md](./FEM范围.md) §4 Q4-7 | 范围表 |
| [Q3-F1-结果精简.md](./Q3-F1-结果精简.md) | scalars / resultRef |
| [驱动后处理.md](./驱动后处理.md) | 分损耗功率接口 |
| [Q4-8-轴向磁拉力.md](./Q4-8-轴向磁拉力.md) | 同季专项（力/变形，非热） |
