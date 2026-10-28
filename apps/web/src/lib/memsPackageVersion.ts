/**
 * Q5-5（架构 tip `4b553f5`，后端钉版 tip `8d9fc3b`，`docs/drafts/Q5-5-契约1.0.0钉死.md`）：
 * 读 `.mems` 时接受 `1.0.0` 与 `1.0.0-draft`；
 * 新写入把 `project.json` / `manifest.json` 的 `memsSchemaVersion` 设为 `1.0.0`。
 * 钉 `1.0.0` ≠ MVP，≠ git tag `v1.0.0`。不改 geometry 等子 schema。
 */
import {
  assertAcceptedMemsSchemaVersion,
  MEMS_SCHEMA_VERSION_WRITE,
} from '@/api/types'

const PROJECT_JSON = 'project.json'
const MANIFEST_JSON = 'manifest.json'

interface ZipEntry {
  name: string
  nameBytes: Uint8Array
  method: number
  flags: number
  time: number
  date: number
  crc: number
  compressed: Uint8Array
  uncompressedSize: number
  versionNeeded: number
}

function u16(b: Uint8Array, o: number): number {
  return b[o] | (b[o + 1] << 8)
}

function u32(b: Uint8Array, o: number): number {
  return (b[o] | (b[o + 1] << 8) | (b[o + 2] << 16) | (b[o + 3] << 24)) >>> 0
}

function concat(parts: Uint8Array[]): Uint8Array {
  const total = parts.reduce((n, p) => n + p.length, 0)
  const out = new Uint8Array(total)
  let offset = 0
  for (const part of parts) {
    out.set(part, offset)
    offset += part.length
  }
  return out
}

function crc32(data: Uint8Array): number {
  let c = ~0
  for (let i = 0; i < data.length; i++) {
    c ^= data[i]
    for (let k = 0; k < 8; k++) {
      c = (c >>> 1) ^ (0xedb88320 & -(c & 1))
    }
  }
  return ~c >>> 0
}

function normZipName(name: string): string {
  return name.replace(/\\/g, '/').replace(/^\.\//, '')
}

function findEocd(buf: Uint8Array): number {
  const min = Math.max(0, buf.length - 22 - 0xffff)
  for (let i = buf.length - 22; i >= min; i--) {
    if (u32(buf, i) !== 0x06054b50) continue
    const commentLen = u16(buf, i + 20)
    if (i + 22 + commentLen === buf.length) return i
  }
  throw new Error('mems body is not a zip archive')
}

function readZip(buf: Uint8Array): ZipEntry[] {
  const eocd = findEocd(buf)
  if (u16(buf, eocd + 4) !== 0 || u16(buf, eocd + 6) !== 0) {
    throw new Error('unsupported multi-disk mems zip')
  }
  const count = u16(buf, eocd + 10)
  const cdOffset = u32(buf, eocd + 16)
  if (cdOffset === 0xffffffff) throw new Error('unsupported zip64 mems archive')

  const entries: ZipEntry[] = []
  let cursor = cdOffset
  for (let n = 0; n < count; n++) {
    if (cursor + 46 > buf.length || u32(buf, cursor) !== 0x02014b50) {
      throw new Error('mems zip central directory is truncated')
    }
    const flags = u16(buf, cursor + 8)
    if (flags & 0x0001) throw new Error('encrypted mems zip is not supported')
    const method = u16(buf, cursor + 10)
    const crc = u32(buf, cursor + 16)
    const compressedSize = u32(buf, cursor + 20)
    const uncompressedSize = u32(buf, cursor + 24)
    if (compressedSize === 0xffffffff || uncompressedSize === 0xffffffff) {
      throw new Error('unsupported zip64 mems archive')
    }
    const nameLen = u16(buf, cursor + 28)
    const extraLen = u16(buf, cursor + 30)
    const commentLen = u16(buf, cursor + 32)
    const localOffset = u32(buf, cursor + 42)
    const nameBytes = buf.slice(cursor + 46, cursor + 46 + nameLen)
    const name = new TextDecoder('utf-8', { fatal: false }).decode(nameBytes)
    if (localOffset + 30 > buf.length || u32(buf, localOffset) !== 0x04034b50) {
      throw new Error(`mems zip local header missing for ${name}`)
    }
    const localNameLen = u16(buf, localOffset + 26)
    const localExtraLen = u16(buf, localOffset + 28)
    const dataStart = localOffset + 30 + localNameLen + localExtraLen
    const dataEnd = dataStart + compressedSize
    if (dataEnd > buf.length) throw new Error(`mems zip entry truncated: ${name}`)

    entries.push({
      name,
      nameBytes,
      method,
      flags: flags & ~0x0008,
      time: u16(buf, cursor + 12),
      date: u16(buf, cursor + 14),
      crc,
      compressed: buf.slice(dataStart, dataEnd),
      uncompressedSize,
      versionNeeded: u16(buf, cursor + 6),
    })
    cursor += 46 + nameLen + extraLen + commentLen
  }
  return entries
}

async function inflateRaw(data: Uint8Array): Promise<Uint8Array> {
  const stream = new Blob([data]).stream().pipeThrough(new DecompressionStream('deflate-raw'))
  return new Uint8Array(await new Response(stream).arrayBuffer())
}

async function uncompressed(entry: ZipEntry): Promise<Uint8Array> {
  if (entry.method === 0) return entry.compressed
  if (entry.method === 8) return inflateRaw(entry.compressed)
  throw new Error(`unsupported zip method ${entry.method} for ${entry.name}`)
}

function entryByName(entries: ZipEntry[], fileName: string): ZipEntry | undefined {
  return entries.find((entry) => normZipName(entry.name) === fileName)
}

function versionInJson(text: string): string | undefined {
  let data: unknown
  try {
    data = JSON.parse(text)
  } catch {
    return undefined
  }
  if (!data || typeof data !== 'object' || Array.isArray(data)) return undefined
  const version = (data as { memsSchemaVersion?: unknown }).memsSchemaVersion
  return typeof version === 'string' ? version : undefined
}

function setVersionText(text: string, version: string): string {
  const pattern = /("memsSchemaVersion"\s*:\s*)"(?:\\.|[^"\\])*"/g
  if (pattern.test(text)) {
    pattern.lastIndex = 0
    return text.replace(pattern, `$1${JSON.stringify(version)}`)
  }
  const data = JSON.parse(text) as Record<string, unknown>
  if (!data || typeof data !== 'object' || Array.isArray(data)) {
    throw new Error('mems JSON member is not an object')
  }
  data.memsSchemaVersion = version
  return `${JSON.stringify(data, null, 2)}\n`
}

async function sha256Hex(data: Uint8Array): Promise<string> {
  const digest = await crypto.subtle.digest('SHA-256', data)
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, '0')).join('')
}

function storedEntry(entry: ZipEntry, bytes: Uint8Array): ZipEntry {
  return {
    ...entry,
    method: 0,
    crc: crc32(bytes),
    compressed: bytes,
    uncompressedSize: bytes.length,
    versionNeeded: Math.max(entry.versionNeeded, 20),
  }
}

function writeZip(entries: ZipEntry[]): Uint8Array {
  const locals: Uint8Array[] = []
  const central: Uint8Array[] = []
  let offset = 0
  for (const entry of entries) {
    const nameLen = entry.nameBytes.length
    const local = new Uint8Array(30 + nameLen + entry.compressed.length)
    const view = new DataView(local.buffer)
    view.setUint32(0, 0x04034b50, true)
    view.setUint16(4, entry.versionNeeded, true)
    view.setUint16(6, entry.flags, true)
    view.setUint16(8, entry.method, true)
    view.setUint16(10, entry.time, true)
    view.setUint16(12, entry.date, true)
    view.setUint32(14, entry.crc, true)
    view.setUint32(18, entry.compressed.length, true)
    view.setUint32(22, entry.uncompressedSize, true)
    view.setUint16(26, nameLen, true)
    view.setUint16(28, 0, true)
    local.set(entry.nameBytes, 30)
    local.set(entry.compressed, 30 + nameLen)
    locals.push(local)

    const cd = new Uint8Array(46 + nameLen)
    const cdView = new DataView(cd.buffer)
    cdView.setUint32(0, 0x02014b50, true)
    cdView.setUint16(4, 20, true)
    cdView.setUint16(6, entry.versionNeeded, true)
    cdView.setUint16(8, entry.flags, true)
    cdView.setUint16(10, entry.method, true)
    cdView.setUint16(12, entry.time, true)
    cdView.setUint16(14, entry.date, true)
    cdView.setUint32(16, entry.crc, true)
    cdView.setUint32(20, entry.compressed.length, true)
    cdView.setUint32(24, entry.uncompressedSize, true)
    cdView.setUint16(28, nameLen, true)
    cdView.setUint16(30, 0, true)
    cdView.setUint16(32, 0, true)
    cdView.setUint16(34, 0, true)
    cdView.setUint16(36, 0, true)
    cdView.setUint32(38, 0, true)
    cdView.setUint32(42, offset, true)
    cd.set(entry.nameBytes, 46)
    central.push(cd)
    offset += local.length
  }

  const cdBytes = concat(central)
  const eocd = new Uint8Array(22)
  const eocdView = new DataView(eocd.buffer)
  eocdView.setUint32(0, 0x06054b50, true)
  eocdView.setUint16(8, entries.length, true)
  eocdView.setUint16(10, entries.length, true)
  eocdView.setUint32(12, cdBytes.length, true)
  eocdView.setUint32(16, offset, true)
  return concat([...locals, cdBytes, eocd])
}

async function jsonText(entries: ZipEntry[], fileName: string): Promise<string | undefined> {
  const entry = entryByName(entries, fileName)
  if (!entry) return undefined
  const bytes = await uncompressed(entry)
  return new TextDecoder('utf-8').decode(bytes)
}

/**
 * 下载的包：zip 时要求 project.json（以及若存在的 manifest.json）版本在双接受集合内。
 * 非 zip（例如错误响应体）原样放过，由调用方处理 HTTP 错误。
 */
export async function assertAcceptedMemsPackage(data: Uint8Array): Promise<void> {
  if (data.length < 4 || data[0] !== 0x50 || data[1] !== 0x4b) return
  const entries = readZip(data)
  const projectText = await jsonText(entries, PROJECT_JSON)
  if (projectText === undefined) throw new Error('mems zip missing required project.json')
  assertAcceptedMemsSchemaVersion(versionInJson(projectText))
  const manifestText = await jsonText(entries, MANIFEST_JSON)
  if (manifestText !== undefined) {
    const manifestVersion = versionInJson(manifestText)
    if (manifestVersion !== undefined) assertAcceptedMemsSchemaVersion(manifestVersion)
  }
}

async function rewriteManifest(text: string, projectBytes: Uint8Array): Promise<Uint8Array> {
  const versioned = setVersionText(text, MEMS_SCHEMA_VERSION_WRITE)
  const data = JSON.parse(versioned) as {
    memsSchemaVersion?: string
    files?: Array<{ path?: string; sha256?: string; size?: number }>
  }
  data.memsSchemaVersion = MEMS_SCHEMA_VERSION_WRITE
  if (Array.isArray(data.files)) {
    const digest = await sha256Hex(projectBytes)
    for (const file of data.files) {
      if (file && typeof file.path === 'string' && normZipName(file.path) === PROJECT_JSON) {
        file.sha256 = digest
        file.size = projectBytes.length
      }
    }
  }
  return new TextEncoder().encode(`${JSON.stringify(data, null, 2)}\n`)
}

/** 新写入：project.json / manifest.json 的 memsSchemaVersion 改为 `1.0.0`。 */
export async function stampMemsPackageWriteVersion(data: Uint8Array): Promise<Uint8Array> {
  const entries = readZip(data)
  const project = entryByName(entries, PROJECT_JSON)
  if (!project) throw new Error('mems zip missing required project.json')
  const projectText = new TextDecoder('utf-8').decode(await uncompressed(project))
  const manifest = entryByName(entries, MANIFEST_JSON)
  const manifestText = manifest
    ? new TextDecoder('utf-8').decode(await uncompressed(manifest))
    : undefined
  const projectVersion = versionInJson(projectText)
  const manifestVersion = manifestText ? versionInJson(manifestText) : undefined
  if (
    projectVersion === MEMS_SCHEMA_VERSION_WRITE &&
    (manifestText === undefined || manifestVersion === MEMS_SCHEMA_VERSION_WRITE)
  ) {
    return data
  }

  const nextProjectText = setVersionText(projectText, MEMS_SCHEMA_VERSION_WRITE)
  if (versionInJson(nextProjectText) !== MEMS_SCHEMA_VERSION_WRITE) {
    throw new Error('failed to set project.json memsSchemaVersion to 1.0.0')
  }
  const projectBytes = new TextEncoder().encode(nextProjectText)
  const next: ZipEntry[] = []
  for (const entry of entries) {
    const name = normZipName(entry.name)
    if (name === PROJECT_JSON) {
      next.push(storedEntry(entry, projectBytes))
    } else if (name === MANIFEST_JSON && manifestText !== undefined) {
      next.push(storedEntry(entry, await rewriteManifest(manifestText, projectBytes)))
    } else {
      next.push(entry)
    }
  }
  return writeZip(next)
}
