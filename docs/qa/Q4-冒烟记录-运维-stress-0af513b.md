# Q4-10 冒烟记录 — 运维 tip `0af513b`（Q4-P10 压测与私有化）

| 字段 | 内容 |
| --- | --- |
| 日期 | 2026-10-28 14:31 Asia/Shanghai |
| 指派 tip | **`0af513b`**（`docs(ops): Q4-10 Jobs analytic/fem dry-run 入队扩展`） |
| tip 全 SHA | `0af513be5357ae81386408c8e5647ff0300d036b` |
| 报告族 | **`2a404ac`** / **`ba0cb36`**（压测跑数 + 演练；tip-backfill） |
| 祖先确认 | `git merge-base --is-ancestor 0af513b HEAD` → **0**（是祖先） |
| 仓库 HEAD（实测时） | `ed831fd`（`ed831fdf266699025abb57a213e31940cc16df22`；含 tip） |
| 执行 | Mo-测试；仅 `docs/qa/`；**未**改业务代码 / 脚本 |
| 性质 | Motor/运维交测 Q4-10：health 压测 + Jobs analytic/fem **dry-run** 入队；手册抽读 |

## 环境

| 证据 | 结果 |
| --- | --- |
| 祖先 | `git merge-base --is-ancestor 0af513b HEAD` → exit **0** |
| API health | `GET http://127.0.0.1:8000/health` → `status=ok`，`db.ok=true`，`redis.ok=true` |
| compose 栈 | `mo-postgres` / `mo-redis` / `mo-api` / `mo-web` / `mo-worker` / `mo-fem` / `mo-worker-fem` Up（box overlay；Web 映射 **:5174**） |
| `MO_FEM_DRY_RUN` | `docker exec mo-worker-fem printenv MO_FEM_DRY_RUN` → **`1`** |
| `make` | **不可用**（`make: command not found`，exit **127**）；Makefile 目标 `stress` / `stress-jobs` 存在，等价跑脚本 |
| 隔离 | 仅 `/workspace/mo-platform`；本轮**未**改 `scripts/` / 业务包；**未**动并行驱动文档 |

## 必跑命令与 exit（照实）

### 1) health 压测

```bash
cd /workspace/mo-platform
make stress                 # EXIT=127（PATH 无 make）
bash scripts/stress-smoke.sh
# EXIT=0
```

| 项 | 值 |
| --- | --- |
| 入口 | `bash scripts/stress-smoke.sh`（`make stress` 因无 make 未跑通） |
| exit | **0** |
| RESULT | **PASS** |
| concurrency / requests | 8 / 40（脚本默认） |
| ok / fail / failure_rate | **40** / **0** / **0.00%** |
| 阈值 | failure_rate > 10% 或初始 health 失败 → FAIL |

stdout 摘要：

```text
=== mo-platform stress-smoke (Q4-10 skeleton) ===
BASE_URL=http://127.0.0.1:8000  CONCURRENCY=8  REQUESTS=40
initial health: ok
ok: 40
fail: 0
total: 40
failure_rate: 0.00%
RESULT: PASS
```

### 2) Jobs analytic / fem dry-run

```bash
cd /workspace/mo-platform
make stress-jobs            # EXIT=127（PATH 无 make）
JOBS_N=8 bash scripts/stress-jobs.sh
# EXIT=0
```

| 项 | 值 |
| --- | --- |
| 入口 | `JOBS_N=8 bash scripts/stress-jobs.sh` |
| exit | **0** |
| RESULT | **PASS** |
| JOBS_N | 8（每类） |
| analytic | **ok=8 / fail=0** |
| fem | **ok=8 / fail=0** |
| wall_sec | **2** |
| projectId | `47990392-2099-4bad-b69e-9839f7fb090e` |
| fem_manifest_sample（脚本） | **`dryRun=true`** |

stdout 摘要：

```text
=== mo-platform stress-jobs (Q4-10 Jobs extension) ===
JOBS_N=8  POLL_SEC=60
MO_FEM_DRY_RUN must stay 1 (this script never flips it)
initial health: ok
login: ok (demo)
--- enqueue (8 analytic + 8 fem) ---
... 均 HTTP 202 ...
--- poll (timeout 60s) ---
... 16 jobs -> succeeded ...
analytic_ok: 8
analytic_fail: 0
fem_ok: 8
fem_fail: 0
wall_sec: 2
fem_manifest_sample: dryRun=true
RESULT: PASS
```

## dryRun 证据（强制口径）

| 检查 | 实测 |
| --- | --- |
| 容器 env | `mo-worker-fem`：`MO_FEM_DRY_RUN=1` |
| 脚本声明 | stress-jobs：**不翻** dry-run；要求保持 1 |
| 脚本摘要 | `fem_manifest_sample: dryRun=true` |
| 抽检 fem job | `605c6f94-f19f-475f-b6cc-0437401632d2` → `status=succeeded`；`payload.manifest.scalars.dryRun=true`；`pending_calibration=true`；`resultRef=solver/fem/jobs/.../manifest.json` |

> **未**开真 Elmer；**未**宣称 FEM ≤3% / 解析 ≤5%；**未**宣称 MVP。

## 手册抽读（`docs/deploy-private.md`）

| 抽读点 | 结论 |
| --- | --- |
| 可读性 | **可读**（草稿；目的 / 端口 / 步骤 / Profiles / FEM / 遗留齐全） |
| 压测入口 | 写明 `make stress` ↔ `scripts/stress-smoke.sh`；`make stress-jobs` ↔ `scripts/stress-jobs.sh` |
| `MO_FEM_DRY_RUN` | **默认 1（stub）**；勿随意翻 0；勿宣称 ≤3%/≤5% |
| 端口表 | Web 示例 **5173**；注明部分环境遗留 **5174** |
| Q4-C2 `:5174` | 文档规避：不以 `:5174/api` 作硬口径；优先 vite `:5173`；**不否决**本轮 |
| 本环境观测 | compose Web 实际映射 **:5174**（遗留）；API `:8000/health` 作硬口径 → **不否决** |

演练报告骨架：[Q4-10-压测与私有化演练](Q4-10-压测与私有化演练.md)（运维已写 health+清洁演练+Jobs §7；本记录补 Mo-测试复测）。

## 判定

| # | 检查 | 实测 | 判定 |
| --- | --- | --- | --- |
| 1 | tip `0af513b` 为 HEAD 祖先 | merge-base exit 0 | **PASS** |
| 2 | `stress-smoke.sh` exit 0 | ok=40 fail=0 | **PASS** |
| 3 | `stress-jobs.sh` JOBS_N=8 exit 0 | analytic 8/8；fem 8/8 | **PASS（dry-run）** |
| 4 | fem dryRun=true / env=1 | 见上 | **PASS** |
| 5 | 私有化手册可读 + `:5174` 不否决 | 抽读 OK | **PASS（草稿可读）** |

> **口径**：本轮为 **stress dry-run** 可运行性证据（health 压测 + Jobs analytic/fem dry-run 入队轮询 + 手册可读）。  
> **禁止宣称**：相对标杆 **≤5%** / **≤3%** 达标、真 Elmer 数值验收、MVP——一律**不宣称**。

## 未做

- 未在本轮重跑运维清洁 down/up 演练（已有报告族 `2a404ac`/`ba0cb36`；本员复测脚本）。
- 未修 `:5174` 反代；未改 compose / 业务代码。
- 未勾 Q4-G1/G2；未宣称 MVP；未动 P11。
- 未改并行驱动 tip `ab4bfda` 相关 docs。

## 跟踪动作

- [Q4-验收跟踪](Q4-验收跟踪.md)：Q4-P10 → **通过（stress dry-run）**；备注 dryRun；**勿冲** P01–P05/P08 进行中或待测、已通过的 P06/P07/P09、**P11 未开始**。
- [Q4-冒烟清单](Q4-冒烟清单.md)：Q4-F1/F2 记 PASS（报告+手册草稿；stress dry-run）。
- [Q4-10-压测与私有化演练](Q4-10-压测与私有化演练.md)：追加 Mo-测试复测段。
