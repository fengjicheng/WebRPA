/**
 * 模块条视图（影刀式结构化线性流程）
 *
 * 与流程图视图共用同一份 nodes/edges 数据，可随时双向切换。
 * 核心：把图（nodes+edges）重建成「缩进嵌套」的模块条——
 *   - 条件(condition)：如果 → (缩进的"是"分支) → 否则 → (缩进的"否"分支) → 结束判断
 *   - 循环(loop/foreach)：循环 → (缩进的循环体) → 结束循环
 *   - 普通模块：顺序排列
 * 点击卡片选中并在右侧配置面板编辑；从左侧拖模块进来追加到末尾。
 */
import { useMemo, useState, useRef } from 'react'
import { useWorkflowStore, moduleTypeLabels, type NodeData } from '@/store/workflowStore'
import { moduleIcons, moduleCategories } from './ModuleSidebar'
import { moduleColors } from './moduleColors'
import { Plus, Search, Trash2, X, CornerDownRight, RefreshCw } from 'lucide-react'
import type { ModuleType } from '@/types'
import type { Node, Edge } from '@xyflow/react'

const CONDITION_TYPES = new Set(['condition'])
const LOOP_TYPES = new Set(['loop', 'foreach', 'foreach_dict'])

type RowType = 'step' | 'else' | 'endif' | 'endloop'
interface BlockRow {
  key: string
  type: RowType
  node?: Node<NodeData>
  depth: number
}

/** 取某节点指定 handle 的目标；handle 为 null 表示默认出口（无 sourceHandle 且非 error） */
function edgeTarget(edges: Edge[], source: string, handle: string | null): string | null {
  if (handle === null) {
    const e = edges.find((x) => x.source === source && (!x.sourceHandle || x.sourceHandle === '') )
    return e ? e.target : null
  }
  const e = edges.find((x) => x.source === source && x.sourceHandle === handle)
  return e ? e.target : null
}

/** 把图重建成缩进嵌套的模块条行序列 */
function buildRows(nodes: Node<NodeData>[], edges: Edge[]): BlockRow[] {
  const moduleNodes = nodes.filter((n) => n.type === 'moduleNode')
  if (moduleNodes.length === 0) return []
  const byId = new Map(moduleNodes.map((n) => [n.id, n]))

  // 计算入度，找入口（无入边者，按 y 排序取最靠上的）
  const incoming = new Map<string, number>()
  moduleNodes.forEach((n) => incoming.set(n.id, 0))
  for (const e of edges) {
    if (byId.has(e.source) && byId.has(e.target)) {
      incoming.set(e.target, (incoming.get(e.target) || 0) + 1)
    }
  }
  const entries = moduleNodes
    .filter((n) => (incoming.get(n.id) || 0) === 0)
    .sort((a, b) => a.position.y - b.position.y)

  const rows: BlockRow[] = []
  const visited = new Set<string>()

  // 从某节点出发可达的所有节点集合（用于求分支合并点）
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
  // 求条件 true/false 两分支的合并点：从 b 出发 BFS，第一个落在 a 可达集合里的节点
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

  const walk = (startId: string | null, stop: Set<string>, depth: number) => {
    let cur = startId
    while (cur && byId.has(cur) && !stop.has(cur) && !visited.has(cur)) {
      visited.add(cur)
      const node = byId.get(cur)!
      const mt = node.data.moduleType as string
      if (CONDITION_TYPES.has(mt)) {
        rows.push({ key: cur, type: 'step', node, depth })
        const t = edgeTarget(edges, cur, 'true')
        const f = edgeTarget(edges, cur, 'false')
        const merge = findMerge(t, f)
        const innerStop = new Set(stop)
        if (merge) innerStop.add(merge)
        walk(t, innerStop, depth + 1)
        rows.push({ key: cur + '::else', type: 'else', depth })
        walk(f, innerStop, depth + 1)
        rows.push({ key: cur + '::endif', type: 'endif', depth })
        cur = merge
      } else if (LOOP_TYPES.has(mt)) {
        rows.push({ key: cur, type: 'step', node, depth })
        const body = edgeTarget(edges, cur, 'loop')
        const done = edgeTarget(edges, cur, 'done')
        const innerStop = new Set(stop)
        innerStop.add(cur) // 循环体回边指回循环节点 → 在此停止
        walk(body, innerStop, depth + 1)
        rows.push({ key: cur + '::endloop', type: 'endloop', depth })
        cur = done
      } else {
        rows.push({ key: cur, type: 'step', node, depth })
        cur = edgeTarget(edges, cur, null)
      }
    }
  }

  for (const entry of entries) walk(entry.id, new Set(), 0)
  // 兜底：未被遍历到的孤立节点（无连线/环）按 y 追加到末尾
  for (const n of [...moduleNodes].sort((a, b) => a.position.y - b.position.y)) {
    if (!visited.has(n.id)) walk(n.id, new Set(), 0)
  }
  return rows
}

function getSummary(data: NodeData): string {
  const candidates = ['url', 'selector', 'text', 'value', 'filePath', 'inputPath', 'message', 'variableName', 'resultVariable', 'condition', 'count']
  for (const k of candidates) {
    const v = data[k]
    if (v && typeof v === 'string' && v.trim()) {
      return v.length > 40 ? v.slice(0, 40) + '…' : v
    }
  }
  return ''
}


/** 模块选择弹层 */
function ModulePicker({ onPick, onClose }: { onPick: (t: ModuleType) => void; onClose: () => void }) {
  const [query, setQuery] = useState('')
  const q = query.trim().toLowerCase()
  const filtered = useMemo(() => {
    return moduleCategories
      .map((cat) => ({
        ...cat,
        modules: cat.modules.filter((m) => {
          if (!q) return true
          const label = (moduleTypeLabels[m] || m).toLowerCase()
          return label.includes(q) || m.toLowerCase().includes(q)
        }),
      }))
      .filter((cat) => cat.modules.length > 0)
  }, [q])

  return (
    <div className="absolute z-50 left-1/2 -translate-x-1/2 mt-1 w-[360px] max-h-[420px] overflow-hidden flex flex-col rounded-[12px] border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-pop-2xl animate-scale-in">
      <div className="flex items-center gap-2 px-3 py-2 border-b border-[hsl(var(--border))]">
        <Search className="w-3.5 h-3.5 text-[hsl(var(--muted-foreground))]" />
        <input
          autoFocus
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="搜索模块…"
          className="flex-1 bg-transparent outline-none text-[13px]"
        />
        <button onClick={onClose} className="text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]">
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-1.5">
        {filtered.map((cat) => (
          <div key={cat.name} className="mb-1">
            <div className="px-2 py-1 text-[10.5px] font-semibold text-[hsl(var(--muted-foreground))] uppercase tracking-wider">
              {cat.name}
            </div>
            {cat.modules.map((m) => {
              const Icon = moduleIcons[m]
              return (
                <button
                  key={m}
                  onClick={() => onPick(m)}
                  className="w-full flex items-center gap-2 px-2 py-1.5 rounded-[7px] text-left hover:bg-[hsl(var(--brand-50))] transition-colors"
                >
                  {Icon && <Icon className="w-3.5 h-3.5 text-[hsl(var(--brand-600))]" />}
                  <span className="text-[12.5px] text-[hsl(var(--slate-700))]">{moduleTypeLabels[m] || m}</span>
                </button>
              )
            })}
          </div>
        ))}
        {filtered.length === 0 && (
          <div className="py-6 text-center text-[12px] text-[hsl(var(--muted-foreground))]">无匹配模块</div>
        )}
      </div>
    </div>
  )
}


export function BlockFlowView() {
  const nodes = useWorkflowStore((s) => s.nodes)
  const edges = useWorkflowStore((s) => s.edges)
  const selectedNodeId = useWorkflowStore((s) => s.selectedNodeId)
  const selectNode = useWorkflowStore((s) => s.selectNode)
  const blockInsertNode = useWorkflowStore((s) => s.blockInsertNode)
  const blockDeleteNode = useWorkflowStore((s) => s.blockDeleteNode)

  const rows = useMemo(() => buildRows(nodes, edges), [nodes, edges])
  const lastStepId = useMemo(() => {
    for (let i = rows.length - 1; i >= 0; i--) if (rows[i].type === 'step' && rows[i].node) return rows[i].node!.id
    return null
  }, [rows])

  const [pickerAfter, setPickerAfter] = useState<string | null | undefined>(undefined) // undefined=未开, null=末尾
  const [dropActive, setDropActive] = useState(false)

  const handlePick = (type: ModuleType) => {
    blockInsertNode(pickerAfter === undefined ? lastStepId : pickerAfter, type)
    setPickerAfter(undefined)
  }

  const handleCanvasDragOver = (e: React.DragEvent) => {
    if (e.dataTransfer.types.includes('application/reactflow')) {
      e.preventDefault()
      e.dataTransfer.dropEffect = 'move'
      setDropActive(true)
    }
  }
  const handleCanvasDrop = (e: React.DragEvent) => {
    const dataStr = e.dataTransfer.getData('application/reactflow')
    setDropActive(false)
    if (!dataStr) return
    e.preventDefault()
    try {
      const parsed = JSON.parse(dataStr)
      if (parsed && parsed.type === 'custom_module' && parsed.moduleId) {
        blockInsertNode(lastStepId, 'custom_module' as ModuleType, { customModuleId: parsed.moduleId } as Partial<NodeData>)
        return
      }
    } catch {
      // 普通模块类型字符串
    }
    blockInsertNode(lastStepId, dataStr as ModuleType)
  }

  const INDENT = 26

  return (
    <div
      className={
        'h-full w-full overflow-y-auto bg-[hsl(var(--background))] py-6 px-4 ' +
        (dropActive ? 'ring-2 ring-inset ring-[hsl(var(--brand-500))] bg-[hsl(var(--brand-50))]' : '')
      }
      onDragOver={handleCanvasDragOver}
      onDragLeave={() => setDropActive(false)}
      onDrop={handleCanvasDrop}
    >
      <div className="max-w-[680px] mx-auto">
        {rows.length === 0 && (
          <div className="text-center py-16 text-[13px] text-[hsl(var(--muted-foreground))]">
            从左侧拖拽模块到这里，或点击下方「添加模块」开始搭建流程
          </div>
        )}

        {rows.map((row) => {
          const pad = row.depth * INDENT
          // 结构标记行：否则 / 结束判断 / 结束循环
          if (row.type !== 'step') {
            const labelMap: Record<string, string> = { else: '否则', endif: '结束判断', endloop: '结束循环' }
            return (
              <div key={row.key} style={{ paddingLeft: pad }} className="py-0.5">
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-[8px] bg-[hsl(var(--slate-100))] border border-dashed border-[hsl(var(--slate-300))]">
                  <span className="text-[11.5px] font-semibold text-[hsl(var(--slate-500))]">{labelMap[row.type]}</span>
                </div>
              </div>
            )
          }
          const node = row.node!
          const data = node.data as NodeData
          const type = data.moduleType as ModuleType
          const Icon = moduleIcons[type]
          const borderClass = (moduleColors[type] || '').split(' ').find((c) => c.startsWith('border-')) || 'border-slate-400'
          const isCond = CONDITION_TYPES.has(type)
          const isLoop = LOOP_TYPES.has(type)
          const summary = getSummary(data)
          const selected = node.id === selectedNodeId
          const prefix = isCond ? '如果　' : isLoop ? '循环　' : ''
          return (
            <div key={row.key} style={{ paddingLeft: pad }} className="py-0.5">
              <div
                onClick={() => selectNode(node.id)}
                className={
                  'group relative flex items-center gap-3 rounded-[10px] border-l-4 bg-[hsl(var(--card))] px-3 py-2.5 cursor-pointer ' +
                  'shadow-soft transition-all duration-150 hover:shadow-pop ' +
                  borderClass + ' ' +
                  (selected ? 'ring-2 ring-[hsl(var(--brand-500))]' : '')
                }
              >
                {row.depth > 0 && <CornerDownRight className="w-3.5 h-3.5 text-[hsl(var(--slate-300))] flex-shrink-0" />}
                <span className="flex items-center justify-center w-7 h-7 rounded-[7px] bg-[hsl(var(--slate-50))] flex-shrink-0">
                  {Icon && <Icon className="w-4 h-4" />}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="text-[13px] font-semibold text-[hsl(var(--slate-800))] truncate">
                    {prefix}{(data.name as string) || moduleTypeLabels[type] || type}
                  </div>
                  {summary && <div className="text-[11px] text-[hsl(var(--muted-foreground))] truncate mt-0.5">{summary}</div>}
                </div>
                {(isCond || isLoop) && (
                  <span className="text-[9.5px] font-semibold px-1.5 py-0.5 rounded-full bg-[hsl(var(--warning-50))] text-[hsl(var(--warning-700))] flex-shrink-0">
                    {isCond ? '条件' : '循环'}
                  </span>
                )}
                <button
                  onClick={(e) => { e.stopPropagation(); blockDeleteNode(node.id) }}
                  className="opacity-0 group-hover:opacity-100 p-1 rounded text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--danger-600))] hover:bg-[hsl(var(--danger-50))] transition-all flex-shrink-0"
                  title="删除模块"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          )
        })}

        {/* 末尾添加模块 */}
        <div className="relative flex justify-center mt-3">
          <button
            onClick={() => setPickerAfter(null)}
            className="flex items-center gap-1.5 px-4 py-2 rounded-[9px] border border-dashed border-[hsl(var(--brand-500)/0.4)] text-[hsl(var(--brand-600))] text-[12.5px] font-medium hover:bg-[hsl(var(--brand-50))] hover:border-[hsl(var(--brand-500))] transition-all"
          >
            <Plus className="w-4 h-4" /> 添加模块
          </button>
          {pickerAfter !== undefined && <ModulePicker onPick={handlePick} onClose={() => setPickerAfter(undefined)} />}
        </div>

        {/* 含分支时的提示 */}
        {rows.some((r) => r.type === 'endif' || r.type === 'endloop') && (
          <div className="mt-4 flex items-start gap-1.5 text-[11px] text-[hsl(var(--slate-600))] bg-[hsl(var(--brand-50))] rounded-lg py-2 px-3">
            <RefreshCw className="w-3 h-3 mt-0.5 flex-shrink-0" />
            <span>条件/循环已按结构缩进展示。分支内部的连线调整、分支增删等精细操作建议切换到「流程图」模式完成。</span>
          </div>
        )}
      </div>
    </div>
  )
}
