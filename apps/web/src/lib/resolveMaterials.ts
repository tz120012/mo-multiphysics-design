/**
 * 材料 resolve 预留（Q2）。
 *
 * 策略（docs/drafts/Q2-材料与解析边界.md §2.4）：
 * - materialId → GET /materials/{id}
 * - 失败则回退到 SolveRequest.materials 内联字段（br_t / sigma_* 等）
 * - `.mems materials/` **只写 refs + overrides**；完整库在 API DB，勿把整库塞进包。
 */
import { getMaterial } from '@/api/materials'
import { catalogMaterialId } from '@/lib/geometryDefaults'
import type { Material } from '@/types/materials'
import type { Materials as SolveMaterials } from '@/types/solver'

export interface ResolvedMaterials {
  /** id → Material（成功 GET 的） */
  byId: Record<string, Material>
  /** 未能 GET 的 id */
  missing: string[]
  /** 合并后的求解材料字段（内联 override 优先保留） */
  inline: SolveMaterials
}

/**
 * 给定 SolveRequest.materials，尝试按 id 拉取曲线；失败保留内联字段。
 */
function withCatalogIds(materials: SolveMaterials): SolveMaterials {
  return {
    ...materials,
    steel_id: catalogMaterialId(materials.steel_id),
    magnet_id: catalogMaterialId(materials.magnet_id),
    conductor_id: catalogMaterialId(materials.conductor_id),
    bar_id: catalogMaterialId(materials.bar_id),
  }
}

export async function resolveMaterials(materials: SolveMaterials): Promise<ResolvedMaterials> {
  const requested = withCatalogIds(materials)
  const ids = [
    requested.steel_id,
    requested.magnet_id,
    requested.conductor_id,
    requested.bar_id,
  ].filter((x): x is string => !!x && x.length > 0)

  const byId: Record<string, Material> = {}
  const missing: string[] = []

  await Promise.all(
    ids.map(async (id) => {
      try {
        byId[id] = await getMaterial(id)
      } catch {
        missing.push(id)
      }
    }),
  )

  // 内联字段始终保留；曲线消费留给真核 / sync（此处不改写已有 br_t 等）
  const inline: SolveMaterials = { ...requested }

  // 若 magnet GET 成功且内联无 br_t，可从 curves.magnet.br_t 填入
  const mid = requested.magnet_id
  if (mid && byId[mid] && inline.br_t == null) {
    const br = byId[mid].curves?.magnet?.br_t
    if (typeof br === 'number') inline.br_t = br
  }
  const cid = requested.conductor_id
  if (cid && byId[cid] && inline.sigma_copper == null) {
    const rho = byId[cid].curves?.coil?.resistivity_ohm_m
    if (typeof rho === 'number' && rho > 0) inline.sigma_copper = 1 / rho
  }
  const bid = requested.bar_id
  if (bid && byId[bid] && inline.sigma_bar == null) {
    const sigma = byId[bid].curves?.acim_bar?.conductivity_s_per_m
    if (typeof sigma === 'number') inline.sigma_bar = sigma
  }

  return { byId, missing, inline }
}
