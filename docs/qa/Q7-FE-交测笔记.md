# Q7 FE 交测笔记（C2 工作台体感）

| 字段 | 内容 |
| --- | --- |
| 范围 | 仅 `apps/web`。零新 API。不改几何 / FEM / drive 求解核心 |
| 基线 | master 已含驱动 `0a33e86`、几何 `2fb0d65`、FEM 草案 `2d6bcf2` |
| 状态 | 交测步骤，不是放行结论。未跑浏览器冒烟前不要写 PASS |

不把 fixture 写成建模完成。不宣称整机 ≤5% / ≤3%。heat-proxy 不是磁静力学。网格步仍是只读降级。

## Q7-C1 材料

1. 工作台「材料」步：钢 / 磁钢 / 绕组（ACIM 为导条、端环）是下拉，不是自由文本。
2. 选项只含种子：`mat-steel-m19`、`mat-steel-50ww470`、`mat-ndfeb-n42`、`mat-ndfeb-n35`、`mat-copper`、`mat-coil-al`、`mat-acim-bar-al`、`mat-acim-bar-cu`、`mat-acim-endring-al`。
3. 目录 `GET /materials` 可达时，标签带来目录名称；不可达时仍用种子清单。请求里不应出现 `demo-steel`、`demo-N35`、裸 `Cu`。
4. 「检视 · 再进求解」列出区域 → id。求解步能看到同一组绑定，求解不因这些 id 失败。

## Q7-C2 激励

1. 步骤名是「激励」。
2. 工况蛇形键进 UEM：`speed_rpm`、`current_a_peak`、`gamma_deg`、`voltage_v_peak`、`freq_hz`、`slip`（按机型显示），经 `commitOperatingPoint` 读写。
3. drive 草稿 / PWM /「用现有 drive Job 预览」保持驱动侧实现，不另开 `/excitation/*`。

## Q7-C3 后处理同壳

1. 后处理步显示 `lastFemJobId` 与 `resultRef`（缺省 `solver/fem/jobs/{jobId}/manifest.json`）。
2. 「在本壳查看场图」嵌入既有场图，数据仍是 `GET /jobs/{id}/artifacts` 再按 role 取 scalars / preview / slice。
3. 无 jobId：可见「未绑定 FEM job；当前为 public fixture / 演示数据。不宣称误差达标。」
4. artifacts 失败：可见「已降级 public fixture…不是该 job 精简产物。」
5. `equationMode=heat_proxy` 或缺省：可见 heat-proxy、不是磁静力学真值。
6. `equationMode=magnetostatic`：可见有限边界与 pending_calibration，不出现整机精度或磁静力学整机关闭。
7. 改几何或工况后，旧 job 不得标「结果已更新」。换成另一个 succeeded job 后才标「结果已更新（新 jobId）」。
8. 解析求解结果在后处理步单独标成「非 FEM 场」。

## Q7-C4 三维体感

1. 改槽数 / 极数 / 磁钢厚 / 盘厚后仍走约 200 ms `POST /geometry/rebuild`。
2. HUD 优先 `meta.hudDims`（槽、极、气隙 mm、磁钢 mm、盘厚 mm）并显示 `paramsHash`。有 `stator_slot` / `airgap_band` 时 HUD 计数，视口按 role 上色（槽腔、气隙环半透明）。
3. `modelingComplete=false` 或未标 true 时，横幅与 HUD 都写「非建模完成」。fixture 横幅仍是「样例/fixture · 非建模完成」。
4. 三维只跟 `meshDescriptor` 刷新。

## Q7-C5 表述

网格步仍写「非网格生成完成」。不打新 tag。不扩拓扑。不把 heat-proxy 当磁静力学。

## 构建

```bash
cd apps/web && pnpm build
```
