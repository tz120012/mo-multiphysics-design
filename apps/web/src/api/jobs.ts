/**
 * Jobs API — POST /jobs · GET /jobs/{id}
 * Q3 FEM 主路径：createJob(jobType=fem) → pollJob 至终态。
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
