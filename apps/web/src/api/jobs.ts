/**
 * Jobs API — POST /jobs · GET /jobs/{id} · GET /jobs/{id}/artifacts
 * Q3 FEM 主路径：createJob(jobType=fem) → pollJob 至终态。
 * L4 / F1：listJobArtifacts + getJobArtifact（精简件，非全场 VTU）。
 */
import { apiClient } from './client'
import {
  isJobTerminal,
  type FemJobPayload,
  type Job,
  type JobCreate,
  type JobStatus,
} from './types'

export type { Job, JobCreate, FemJobPayload, JobStatus }

/** POST /jobs → 202 Job */
export async function createJob(body: JobCreate, signal?: AbortSignal): Promise<Job> {
  const { data } = await apiClient.post<Job>('/jobs', body, { signal })
  return data
}

/** GET /jobs/{jobId} */
export async function getJob(jobId: string, signal?: AbortSignal): Promise<Job> {
  const { data } = await apiClient.get<Job>(`/jobs/${jobId}`, { signal })
  return data
}

export type PollJobOptions = {
  intervalMs?: number
  timeoutMs?: number
  signal?: AbortSignal
  onUpdate?: (job: Job) => void
}

export class JobPollTimeoutError extends Error {
  readonly job: Job | null
  constructor(message: string, job: Job | null = null) {
    super(message)
    this.name = 'JobPollTimeoutError'
    this.job = job
  }
}

export class JobPollAbortedError extends Error {
  constructor(message = 'Job poll aborted') {
    super(message)
    this.name = 'JobPollAbortedError'
  }
}

function sleep(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) {
      reject(new JobPollAbortedError())
      return
    }
    const t = setTimeout(() => {
      signal?.removeEventListener('abort', onAbort)
      resolve()
    }, ms)
    const onAbort = () => {
      clearTimeout(t)
      reject(new JobPollAbortedError())
    }
    signal?.addEventListener('abort', onAbort, { once: true })
  })
}

/**
 * 轮询 GET /jobs/{id} 直至终态（succeeded|failed|cancelled）。
 * 超时抛 JobPollTimeoutError；signal abort 抛 JobPollAbortedError。
 */
export async function pollJob(jobId: string, opts: PollJobOptions = {}): Promise<Job> {
  const intervalMs = opts.intervalMs ?? 1500
  const timeoutMs = opts.timeoutMs ?? 120_000
  const signal = opts.signal
  const started = Date.now()
  let last: Job | null = null

  while (true) {
    if (signal?.aborted) throw new JobPollAbortedError()
    last = await getJob(jobId, signal)
    opts.onUpdate?.(last)
    if (isJobTerminal(last.status)) return last
    if (Date.now() - started >= timeoutMs) {
      throw new JobPollTimeoutError(
        `Job ${jobId} poll timed out after ${timeoutMs}ms (last status=${last.status})`,
        last,
      )
    }
    await sleep(intervalMs, signal)
  }
}

/** GET /jobs/{jobId}/artifacts — F1 manifest 索引 */
export interface JobArtifactFile {
  path: string
  role: string
  format: string
  bytes?: number
}

export interface JobArtifactsList {
  jobId: string
  resultRef?: string | null
  artifacts: JobArtifactFile[]
}

/**
 * 按路径段 encodeURIComponent，保留 `/`。
 * FastAPI `{artifact_path:path}` 需要真实斜杠；整段 encode 会把 `/` 收成一个 segment。
 */
export function encodeJobArtifactPath(artifactPath: string): string {
  const normalized = artifactPath.trim().replace(/\\/g, '/').replace(/^\/+/, '')
  if (!normalized) throw new Error('产物路径为空')
  const segments = normalized.split('/').filter((seg) => seg.length > 0)
  if (segments.length === 0 || segments.some((seg) => seg === '.' || seg === '..')) {
    throw new Error('产物路径非法')
  }
  return segments.map((seg) => encodeURIComponent(seg)).join('/')
}

/** GET /jobs/{jobId}/artifacts */
export async function listJobArtifacts(
  jobId: string,
  signal?: AbortSignal,
): Promise<JobArtifactsList> {
  const { data } = await apiClient.get<JobArtifactsList>(
    `/jobs/${encodeURIComponent(jobId)}/artifacts`,
    { signal },
  )
  return data
}

/**
 * GET /jobs/{jobId}/artifacts/{artifactPath} → bytes.
 * glTF / GLB / PNG 用 blob；调用方负责 createObjectURL 与 revoke。
 */
export async function getJobArtifactBlob(
  jobId: string,
  artifactPath: string,
  signal?: AbortSignal,
): Promise<Blob> {
  const rel = encodeJobArtifactPath(artifactPath)
  const { data } = await apiClient.get<Blob>(
    `/jobs/${encodeURIComponent(jobId)}/artifacts/${rel}`,
    {
      responseType: 'blob',
      signal,
      timeout: 60_000,
      headers: { Accept: '*/*' },
    },
  )
  return data
}

/** 同上，解析 JSON（manifest.json / scalars.json） */
export async function getJobArtifact<T = unknown>(
  jobId: string,
  artifactPath: string,
  signal?: AbortSignal,
): Promise<T> {
  const blob = await getJobArtifactBlob(jobId, artifactPath, signal)
  const text = (await blob.text()).replace(/^\uFEFF/, '').trim()
  try {
    return JSON.parse(text) as T
  } catch {
    throw new Error(`产物不是 JSON：${artifactPath}`)
  }
}
