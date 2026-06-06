/**
 * 模块条视图（影刀式线性流程搭建）
 *
 * 与流程图视图共用同一份 nodes/edges 数据，可随时双向切换。
 * - 按连线顺序把节点渲染成自上而下的「模块条」卡片
 * - 点击卡片选中并在右侧配置面板编辑（复用现有 ConfigPanel）
 * - 卡片间「+」按钮插入模块；卡片可上下拖拽重排；可删除
 * - 条件/循环等分支节点用徽标标注，复杂分支结构建议切回流程图微调
 */
import { useMemo, useState, useRef } from 'react'
import { useWorkflowStore, moduleTypeLabels, type NodeData } from '@/store/workflowStore'
import { moduleIcons, moduleCategories } from './ModuleSidebar'
import { moduleColors } from './moduleColors'
import { Plus, Search, Trash2, GripVertical, GitBranch, X } from 'lucide-react'
import type { ModuleType } from '@/types'
import type { Node } from '@xyflow/react'

const BRANCH_TYPES = new Set(['condition', 'loop', 'foreach', 'foreach_dict'])

/** 按连线顺序对节点做最佳线性排序（跟随 source->target 链，BFS 兜底） */
function orderNodes(nodes: Node<NodeData>[], edges: { source: string; target: string }[]): Node<NodeData>[] {
  const moduleNodes = nodes.filter((n) => n.type === 'moduleNode')
  if (moduleNodes.length === 0) return []
  const byId = new Map(moduleNodes.map((n) => [n.id, n]))
  const incoming = new Map<string, number>()
  const nextOf = new Map<string, string[]>()
  for (const n of moduleNodes) {
    incoming.set(n.id, 0)
    nextOf.set(n.id, [])
  }
  for (const e of edges) {
    if (byId.has(e.source) && byId.has(e.target)) {
      incoming.set(e.target, (incoming.get(e.target) || 0) + 1)
      nextOf.get(e.source)!.push(e.target)
    }
  }
  // 入口：无入边的节点（按原始 y 排序，保证稳定）
  const entries = moduleNodes
    .filter((n) => (incoming.get(n.id) || 0) === 0)
    .sort((a, b) => a.position.y - b.position.y)
  const visited = new Set<string>()
  const ordered: Node<NodeData>[] = []
  const queue = [...entries]
  while (queue.length) {
    const n = queue.shift()!
    if (visited.has(n.id)) continue
    visited.add(n.id)
    ordered.push(n)
    for (const t of nextOf.get(n.id) || []) {
      if (!visited.has(t) && byId.has(t)) queue.push(byId.get(t)!)
    }
  }
  // 兜底：未被链覆盖的节点按 y 追加
  for (const n of moduleNodes.sort((a, b) => a.position.y - b.position.y)) {
    if (!visited.has(n.id)) ordered.push(n)
  }
  return ordered
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


function getSummary(data: NodeData): string {
  const candidates = ['url', 'selector', 'text', 'value', 'filePath', 'inputPath', 'message', 'variableName', 'resultVariable']
  for (const k of candidates) {
    const v = data[k]
    if (v && typeof v === 'string' && v.trim()) {
      return v.length > 36 ? v.slice(0, 36) + '…' : v
    }
  }
  return ''
}

export function BlockFlowView() {
  const nodes = useWorkflowStore((s) => s.nodes)
  const edges = useWorkflowStore((s) => s.edges)
  const selectedNodeId = useWorkflowStore((s) => s.selectedNodeId)
  const selectNode = useWorkflowStore((s) => s.selectNode)
  const blockInsertNode = useWorkflowStore((s) => s.blockInsertNode)
  const blockDeleteNode = useWorkflowStore((s) => s.blockDeleteNode)
  const blockReorder = useWorkflowStore((s) => s.blockReorder)

  const ordered = useMemo(() => orderNodes(nodes, edges), [nodes, edges])
  const [pickerAfter, setPickerAfter] = useState<string | null | undefined>(undefined) // undefined=未开, null=开头
  const dragIndex = useRef<number | null>(null)
  const [dragOver, setDragOver] = useState<number | null>(null)

  const handlePick = (type: ModuleType) => {
    blockInsertNode(pickerAfter === undefined ? null : pickerAfter, type)
    setPickerAfter(undefined)
  }

  const handleDrop = (dropIndex: number) => {
    const from = dragIndex.current
    dragIndex.current = null
    setDragOver(null)
    if (from === null || from === dropIndex) return
    const ids = ordered.map((n) => n.id)
    const [moved] = ids.splice(from, 1)
    ids.splice(dropIndex, 0, moved)
    blockReorder(ids)
  }

  return (
    <div className="h-full w-full overflow-y-auto bg-[hsl(var(--background))] py-6 px-4">
      <div className="max-w-[640px] mx-auto">
        {/* 顶部插入 */}
        <AddDivider onClick={() => setPickerAfter(null)} active={pickerAfter === null} onClose={() => setPickerAfter(undefined)} onPick={handlePick} />

        {ordered.length === 0 && (
          <div className="text-center py-16 text-[13px] text-[hsl(var(--muted-foreground))]">
            还没有模块，点击上方「+」开始搭建流程
          </div>
        )}

        {ordered.map((node, index) => {
          const data = node.data as NodeData
          const type = data.moduleType as ModuleType
          const Icon = moduleIcons[type]
          const colorClass = moduleColors[type] || 'border-gray-400 bg-gray-50'
          const isBranch = BRANCH_TYPES.has(type)
          const summary = getSummary(data)
          const selected = node.id === selectedNodeId
          return (
            <div key={node.id}>
              <div
                draggable
                onDragStart={() => (dragIndex.current = index)}
                onDragOver={(e) => { e.preventDefault(); setDragOver(index) }}
                onDrop={() => handleDrop(index)}
                onClick={() => selectNode(node.id)}
                className={
                  'group relative flex items-center gap-3 rounded-[10px] border-l-4 bg-[hsl(var(--card))] px-3 py-2.5 cursor-pointer ' +
                  'shadow-soft transition-all duration-150 hover:shadow-pop ' +
                  colorClass + ' ' +
                  (selected ? 'ring-2 ring-[hsl(var(--brand-500))]' : '') + ' ' +
                  (dragOver === index ? 'border-t-2 border-t-[hsl(var(--brand-500))]' : '')
                }
              >
                <GripVertical className="w-4 h-4 text-[hsl(var(--slate-300))] cursor-grab flex-shrink-0" />
                <span className="flex items-center justify-center w-7 h-7 rounded-[7px] bg-white/70 flex-shrink-0">
                  {Icon && <Icon className="w-4 h-4" />}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="text-[13px] font-semibold text-[hsl(var(--slate-800))] truncate">
                      {(data.name as string) || moduleTypeLabels[type] || type}
                    </span>
                    {isBranch && (
                      <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full bg-[hsl(var(--warning-50))] text-[hsl(var(--warning-700))] text-[9.5px] font-semibold">
                        <GitBranch className="w-2.5 h-2.5" /> 分支
                      </span>
                    )}
                  </div>
                  {summary && <div className="text-[11px] text-[hsl(var(--muted-foreground))] truncate mt-0.5">{summary}</div>}
                </div>
                <span className="text-[10px] font-mono text-[hsl(var(--slate-400))] flex-shrink-0">#{index + 1}</span>
                <button
                  onClick={(e) => { e.stopPropagation(); blockDeleteNode(node.id) }}
                  className="opacity-0 group-hover:opacity-100 p-1 rounded text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--danger-600))] hover:bg-[hsl(var(--danger-50))] transition-all flex-shrink-0"
                  title="删除模块"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
              <AddDivider
                onClick={() => setPickerAfter(node.id)}
                active={pickerAfter === node.id}
                onClose={() => setPickerAfter(undefined)}
                onPick={handlePick}
              />
            </div>
          )
        })}

        {ordered.some((n) => BRANCH_TYPES.has(n.data.moduleType as string)) && (
          <div className="mt-4 text-center text-[11px] text-[hsl(var(--muted-foreground))] bg-[hsl(var(--warning-50))] rounded-lg py-2 px-3">
            该流程含分支/循环，模块条按主链顺序展示；分支的精细连线请切换到「流程图」模式调整
          </div>
        )}
      </div>
    </div>
  )
}

/** 模块条之间的「+」分隔插入按钮 */
function AddDivider({ onClick, active, onClose, onPick }: {
  onClick: () => void
  active: boolean
  onClose: () => void
  onPick: (t: ModuleType) => void
}) {
  return (
    <div className="relative flex items-center justify-center h-7 group/divider">
      <div className="absolute inset-x-0 top-1/2 h-px bg-[hsl(var(--border))] opacity-0 group-hover/divider:opacity-100 transition-opacity" />
      <button
        onClick={onClick}
        className="relative z-10 flex items-center justify-center w-5 h-5 rounded-full bg-[hsl(var(--card))] border border-[hsl(var(--border))] text-[hsl(var(--brand-600))] opacity-40 hover:opacity-100 hover:border-[hsl(var(--brand-500))] hover:scale-110 transition-all"
        title="在此处插入模块"
      >
        <Plus className="w-3 h-3" />
      </button>
      {active && <ModulePicker onPick={onPick} onClose={onClose} />}
    </div>
  )
}
