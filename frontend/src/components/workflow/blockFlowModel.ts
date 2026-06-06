/**
 * 模块条结构化模型：图(nodes+edges) ↔ 结构树(Block[]) 双向转换
 *
 * 思路（对标影刀）：模块条编辑时以「结构树」为操作对象，每次编辑后
 * 由树**完整重新生成图**（自动连好 true/false/loop/done/回边/合并点），
 * 从而保证纯模块条模式也能搭出任意含条件/循环/嵌套的完整工作流。
 */
import { nanoid } from 'nanoid'
import type { Node, Edge } from '@xyflow/react'
import type { NodeData } from '@/store/workflowStore'
import { moduleTypeLabels } from '@/store/workflowStore'
import type { ModuleType } from '@/types'

export type Block =
  | { kind: 'step'; id: string; node: Node<NodeData> }
  | { kind: 'if'; id: string; node: Node<NodeData>; then: Block[]; els: Block[] }
  | { kind: 'loop'; id: string; node: Node<NodeData>; body: Block[] }

export const CONDITION_TYPES = new Set(['condition'])
export const LOOP_TYPES = new Set(['loop', 'foreach', 'foreach_dict'])

function edgeTarget(edges: Edge[], source: string, handle: string | null): string | null {
  if (handle === null) {
    const e = edges.find((x) => x.source === source && (!x.sourceHandle || x.sourceHandle === ''))
    return e ? e.target : null
  }
  const e = edges.find((x) => x.source === source && x.sourceHandle === handle)
  return e ? e.target : null
}

/** 图 → 结构树 */
export function parseGraphToBlocks(nodes: Node<NodeData>[], edges: Edge[]): Block[] {
  const moduleNodes = nodes.filter((n) => n.type === 'moduleNode')
  if (moduleNodes.length === 0) return []
  const byId = new Map(moduleNodes.map((n) => [n.id, n]))

  const incoming = new Map<string, number>()
  moduleNodes.forEach((n) => incoming.set(n.id, 0))
  for (const e of edges) {
    if (byId.has(e.source) && byId.has(e.target)) incoming.set(e.target, (incoming.get(e.target) || 0) + 1)
  }
  const entries = moduleNodes
    .filter((n) => (incoming.get(n.id) || 0) === 0)
    .sort((a, b) => a.position.y - b.position.y)

  const visited = new Set<string>()

  const reachable = (start: string | null): Set<string> => {
    const s = new Set<string>()
    if (!start) return s
    const q = [start]
    while (q.length) {
      const c = q.shift()!
      if (s.has(c) || !byId.has(c)) continue
      s.add(c)
      for (const e of edges) if (e.source === c) q.push(e.target)
    }
    return s
  }
  const findMerge = (a: string | null, b: string | null): string | null => {
    if (!a || !b) return a || b || null
    const ra = reachable(a)
    const seen = new Set<string>()
    const q = [b]
    while (q.length) {
      const c = q.shift()!
      if (seen.has(c)) continue
      seen.add(c)
      if (ra.has(c)) return c
      for (const e of edges) if (e.source === c) q.push(e.target)
    }
    return null
  }

  const parseSeq = (startId: string | null, stop: Set<string>): Block[] => {
    const seq: Block[] = []
    let cur = startId
    while (cur && byId.has(cur) && !stop.has(cur) && !visited.has(cur)) {
      visited.add(cur)
      const node = byId.get(cur)!
      const mt = node.data.moduleType as string
      if (CONDITION_TYPES.has(mt)) {
        const t = edgeTarget(edges, cur, 'true')
        const f = edgeTarget(edges, cur, 'false')
        const merge = findMerge(t, f)
        const innerStop = new Set(stop)
        if (merge) innerStop.add(merge)
        const thenSeq = parseSeq(t, innerStop)
        const els = parseSeq(f, innerStop)
        seq.push({ kind: 'if', id: cur, node, then: thenSeq, els })
        cur = merge
      } else if (LOOP_TYPES.has(mt)) {
        const body = edgeTarget(edges, cur, 'loop')
        const done = edgeTarget(edges, cur, 'done')
        const innerStop = new Set(stop)
        innerStop.add(cur)
        const bodySeq = parseSeq(body, innerStop)
        seq.push({ kind: 'loop', id: cur, node, body: bodySeq })
        cur = done
      } else {
        seq.push({ kind: 'step', id: cur, node })
        cur = edgeTarget(edges, cur, null)
      }
    }
    return seq
  }

  const result: Block[] = []
  for (const entry of entries) result.push(...parseSeq(entry.id, new Set()))
  for (const n of [...moduleNodes].sort((a, b) => a.position.y - b.position.y)) {
    if (!visited.has(n.id)) result.push(...parseSeq(n.id, new Set()))
  }
  return result
}


/** 结构树 → 图（重新生成 nodes+edges，自动连好所有分支/循环/合并边） */
export function generateGraphFromBlocks(blocks: Block[]): { nodes: Node<NodeData>[]; edges: Edge[] } {
  const outNodes: Node<NodeData>[] = []
  const outEdges: Edge[] = []
  const X0 = 220, XSTEP = 64, Y0 = 80, YSTEP = 110
  let yi = 0

  // 布局：前序遍历分配位置（阅读顺序自上而下、按层缩进）
  const place = (seq: Block[], depth: number) => {
    for (const b of seq) {
      outNodes.push({ ...b.node, position: { x: X0 + depth * XSTEP, y: Y0 + yi * YSTEP }, selected: false } as Node<NodeData>)
      yi++
      if (b.kind === 'if') { place(b.then, depth + 1); place(b.els, depth + 1) }
      else if (b.kind === 'loop') { place(b.body, depth + 1) }
    }
  }
  place(blocks, 0)

  const addEdge = (source: string, target: string | null, handle: string | null) => {
    if (!target) return
    const e: Edge = { id: `e-${source}-${handle || 'd'}-${target}`, source, target }
    if (handle) (e as Edge & { sourceHandle?: string }).sourceHandle = handle
    outEdges.push(e)
  }

  // 接线：返回序列入口节点 id（空序列返回 afterId）
  const wireSeq = (seq: Block[], afterId: string | null): string | null => {
    let entry = afterId
    for (let i = seq.length - 1; i >= 0; i--) entry = wireBlock(seq[i], entry)
    return entry
  }
  const wireBlock = (b: Block, followId: string | null): string => {
    if (b.kind === 'step') {
      addEdge(b.id, followId, null)
      return b.id
    }
    if (b.kind === 'if') {
      const thenEntry = wireSeq(b.then, followId)
      const elseEntry = wireSeq(b.els, followId)
      addEdge(b.id, thenEntry ?? followId, 'true')
      addEdge(b.id, elseEntry ?? followId, 'false')
      return b.id
    }
    // loop
    if (b.body.length > 0) {
      const bodyEntry = wireSeq(b.body, b.id) // 循环体最后回到循环节点
      addEdge(b.id, bodyEntry, 'loop')
    }
    addEdge(b.id, followId, 'done')
    return b.id
  }
  wireSeq(blocks, null)

  return { nodes: outNodes, edges: outEdges }
}

/** 新建一个 Block（条件/循环带空分支） */
export function createBlock(type: ModuleType, extraData?: Partial<NodeData>): Block {
  const id = nanoid()
  const node: Node<NodeData> = {
    id,
    type: 'moduleNode',
    position: { x: 0, y: 0 },
    data: { label: moduleTypeLabels[type] || type, moduleType: type, ...(extraData || {}) } as NodeData,
  }
  if (CONDITION_TYPES.has(type)) return { kind: 'if', id, node, then: [], els: [] }
  if (LOOP_TYPES.has(type)) return { kind: 'loop', id, node, body: [] }
  return { kind: 'step', id, node }
}

// ---------- 结构树编辑（纯函数，返回新树） ----------

type Found = { list: Block[]; index: number } | null

function locate(blocks: Block[], id: string): Found {
  for (let i = 0; i < blocks.length; i++) {
    const b = blocks[i]
    if (b.id === id) return { list: blocks, index: i }
    if (b.kind === 'if') {
      const inThen = locate(b.then, id)
      if (inThen) return inThen
      const inEls = locate(b.els, id)
      if (inEls) return inEls
    } else if (b.kind === 'loop') {
      const inBody = locate(b.body, id)
      if (inBody) return inBody
    }
  }
  return null
}

function findBlock(blocks: Block[], id: string): Block | null {
  for (const b of blocks) {
    if (b.id === id) return b
    if (b.kind === 'if') {
      const r = findBlock(b.then, id) || findBlock(b.els, id)
      if (r) return r
    } else if (b.kind === 'loop') {
      const r = findBlock(b.body, id)
      if (r) return r
    }
  }
  return null
}

/** 在某 block 之后插入（同一容器列表内）；afterId 为 null 则插到顶层末尾 */
export function insertAfter(blocks: Block[], afterId: string | null, neu: Block): Block[] {
  if (afterId === null) return [...blocks, neu]
  const loc = locate(blocks, afterId)
  if (!loc) return [...blocks, neu]
  loc.list.splice(loc.index + 1, 0, neu)
  return [...blocks]
}

/** 插入到 if 分支(then/els) 或 loop 体的开头 */
export function insertIntoContainer(blocks: Block[], containerId: string, slot: 'then' | 'els' | 'body', neu: Block): Block[] {
  const c = findBlock(blocks, containerId)
  if (!c) return blocks
  if (c.kind === 'if' && (slot === 'then' || slot === 'els')) {
    c[slot] = [...c[slot], neu]
  } else if (c.kind === 'loop' && slot === 'body') {
    c.body = [...c.body, neu]
  }
  return [...blocks]
}

export function removeBlock(blocks: Block[], id: string): Block[] {
  const loc = locate(blocks, id)
  if (!loc) return blocks
  loc.list.splice(loc.index, 1)
  return [...blocks]
}

export function moveBlock(blocks: Block[], id: string, dir: -1 | 1): Block[] {
  const loc = locate(blocks, id)
  if (!loc) return blocks
  const j = loc.index + dir
  if (j < 0 || j >= loc.list.length) return blocks
  const tmp = loc.list[loc.index]
  loc.list[loc.index] = loc.list[j]
  loc.list[j] = tmp
  return [...blocks]
}

/** 收集一个块（含其分支/循环体）内的所有 block id */
function subtreeIds(b: Block, acc: Set<string>) {
  acc.add(b.id)
  if (b.kind === 'if') { b.then.forEach((x) => subtreeIds(x, acc)); b.els.forEach((x) => subtreeIds(x, acc)) }
  else if (b.kind === 'loop') { b.body.forEach((x) => subtreeIds(x, acc)) }
}

/**
 * 把已存在的块（含子结构）移动到目标位置。
 * target: { mode:'after', id } 移到某块之后（id 为 null 移到顶层末尾）；
 *         { mode:'into', id, slot } 移入某容器分支/循环体末尾。
 * 防护：不允许移入自身子树（否则会丢失结构）。
 */
export function moveBlockTo(
  blocks: Block[],
  id: string,
  target: { mode: 'after'; id: string | null } | { mode: 'into'; id: string; slot: 'then' | 'els' | 'body' },
): Block[] {
  const moving = findBlock(blocks, id)
  if (!moving) return blocks
  // 目标不能是被移动块本身或其子孙
  const ids = new Set<string>()
  subtreeIds(moving, ids)
  const targetId = target.mode === 'after' ? target.id : target.id
  if (targetId && ids.has(targetId)) return blocks
  // 先摘除
  const removed = removeBlock(blocks, id)
  // 再插入到目标
  if (target.mode === 'after') return insertAfter(removed, target.id, moving)
  return insertIntoContainer(removed, target.id, target.slot, moving)
}
