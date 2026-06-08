/**
 * 模块必填字段（来源：后端模块 schema），用于配置面板的必填校验提示。
 * 全局缓存一次，避免重复请求。
 */
import { useEffect, useState } from 'react'
import { apiRequest } from '@/services/api'

let cache: Record<string, string[]> | null = null
let inflight: Promise<Record<string, string[]>> | null = null

async function fetchRequiredFields(): Promise<Record<string, string[]>> {
  if (cache) return cache
  if (inflight) return inflight
  inflight = (async () => {
    try {
      const res = await apiRequest<{ requiredFields?: Record<string, string[]> }>('/system/module-required-fields')
      cache = (res as any)?.data?.requiredFields || (res as any)?.requiredFields || {}
    } catch {
      cache = {}
    }
    inflight = null
    return cache!
  })()
  return inflight
}

/** React hook：返回必填字段映射（首次自动拉取并缓存） */
export function useRequiredFields(): Record<string, string[]> {
  const [map, setMap] = useState<Record<string, string[]>>(cache || {})
  useEffect(() => {
    if (cache) { setMap(cache); return }
    let alive = true
    fetchRequiredFields().then((m) => { if (alive) setMap(m) })
    return () => { alive = false }
  }, [])
  return map
}

/** 计算某模块当前缺失的必填字段 */
export function getMissingRequired(
  moduleType: string,
  data: Record<string, unknown>,
  reqMap: Record<string, string[]>,
): string[] {
  const req = reqMap[moduleType]
  if (!req || req.length === 0) return []
  return req.filter((f) => {
    const v = data[f]
    if (v === undefined || v === null) return true
    if (typeof v === 'string') return v.trim() === ''
    if (Array.isArray(v)) return v.length === 0
    return false
  })
}
