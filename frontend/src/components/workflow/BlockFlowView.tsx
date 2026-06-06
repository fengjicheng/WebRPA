/**
 * 模块条视图（影刀式结构化编辑）
 *
 * 纯模块条模式即可搭建任意工作流（含条件/循环/嵌套），无需切回流程图。
 * 以「结构树」为操作对象，每次编辑后由树重新生成完整的图（自动连线）。
 */
import { useMemo, useState } from 'react'
import type React from 'react'
import { useWorkflowStore, moduleTypeLabels, type NodeData } from '@/store/workflowStore'
import { moduleIcons, moduleCategories } from './ModuleSidebar'
import { moduleColors } from './moduleColors'
import { Plus, Search, Trash2, X, ChevronUp, ChevronDown, CornerDownRight } from 'lucide-react'
import type { ModuleType } from '@/types'
import {
  parseGraphToBlocks, generateGraphFromBlocks, createBlock,
  insertAfter, insertIntoContainer, removeBlock, moveBlock, moveBlockTo,
  CONDITION_TYPES, LOOP_TYPES, type Block,
} from './blockFlowModel'

// 插入目标：在某 block 之后，或插入某容器的分支/循环体
type PickerTarget =
  | { mode: 'after'; id: string | null }
  | { mode: 'into'; id: string; slot: 'then' | 'els' | 'body' }

function getSummary(data: NodeData): string {
  const candidates = ['url', 'selector', 'text', 'value', 'filePath', 'inputPath', 'message', 'variableName', 'resultVariable', 'condition', 'count', 'listVariable']
  for (const k of candidates) {
    const v = data[k]
    if (v && typeof v === 'string' && v.trim()) return v.length > 40 ? v.slice(0, 40) + '…' : v
  }
  return ''
}

/** 模块选择弹层 */
function ModulePicker({ onPick, onClose }: { onPick: (t: ModuleType) => void; onClose: () => void }) {
  const [query, setQuery] = useState('')
  const q = query.trim().toLowerCase()
  const filtered = useMemo(() => moduleCategories
    .map((cat) => ({ ...cat, modules: cat.modules.filter((m) => !q || (moduleTypeLabels[m] || m).toLowerCase().includes(q) || m.toLowerCase().includes(q)) }))
    .filter((cat) => cat.modules.length > 0), [q])
  return (
    <div className="absolute z-50 left-0 mt-1 w-[340px] max-h-[400px] overflow-hidden flex flex-col rounded-[12px] border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-pop-2xl animate-scale-in">
      <div className="flex items-center gap-2 px-3 py-2 border-b border-[hsl(var(--border))]">
        <Search className="w-3.5 h-3.5 text-[hsl(var(--muted-foreground))]" />
        <input autoFocus value={query} onChange={(e) => setQuery(e.target.value)} placeholder="搜索模块…" className="flex-1 bg-transparent outline-none text-[13px]" />
        <button onClick={onClose} className="text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]"><X className="w-3.5 h-3.5" /></button>
      </div>
      <div className="flex-1 overflow-y-auto p-1.5" onWheel={(e) => e.stopPropagation()}>
        {filtered.map((cat) => (
          <div key={cat.name} className="mb-1">
            <div className="px-2 py-1 text-[10.5px] font-semibold text-[hsl(var(--muted-foreground))] uppercase tracking-wider">{cat.name}</div>
            {cat.modules.map((m) => {
              const Icon = moduleIcons[m]
              return (
                <button key={m} onClick={() => onPick(m)} className="w-full flex items-center gap-2 px-2 py-1.5 rounded-[7px] text-left hover:bg-[hsl(var(--brand-50))] transition-colors">
                  {Icon && <Icon className="w-3.5 h-3.5 text-[hsl(var(--brand-600))]" />}
                  <span className="text-[12.5px] text-[hsl(var(--slate-700))]">{moduleTypeLabels[m] || m}</span>
                </button>
              )
            })}
          </div>
        ))}
        {filtered.length === 0 && <div className="py-6 text-center text-[12px] text-[hsl(var(--muted-foreground))]">无匹配模块</div>}
      </div>
    </div>
  )
}


export function BlockFlowView() {
  const nodes = useWorkflowStore((s) => s.nodes)
  const edges = useWorkflowStore((s) => s.edges)
  const selectedNodeId = useWorkflowStore((s) => s.selectedNodeId)
  const selectNode = useWorkflowStore((s) => s.selectNode)
  const setGraph = useWorkflowStore((s) => s.setGraph)

  const blocks = useMemo(() => parseGraphToBlocks(nodes, edges), [nodes, edges])
  const [picker, setPicker] = useState<PickerTarget | null>(null)
  const [dropActive, setDropActive] = useState(false)

  // 所有结构化编辑：基于当前图重新解析出可变树 → 编辑 → 重新生成图 → 提交
  // 关键：重新生成只管 moduleNode；分组/便签/子流程头等非模块节点及其相关连线原样保留，避免数据丢失
  const applyEdit = (fn: (tree: Block[]) => Block[]) => {
    const tree = parseGraphToBlocks(nodes, edges)
    const next = fn(tree)
    const g = generateGraphFromBlocks(next)
    const moduleIds = new Set(g.nodes.map((n) => n.id))
    // 保留非模块节点（group/note/subflowHeader 等）
    const preservedNodes = nodes.filter((n) => n.type !== 'moduleNode')
    // 保留涉及非模块节点的连线（如子流程头 → 首个模块）
    const preservedEdges = edges.filter((e) => {
      const sIsModule = moduleIds.has(e.source)
      const tIsModule = moduleIds.has(e.target)
      return !(sIsModule && tIsModule) // 模块↔模块的边由生成器重建，其余保留
    })
    setGraph([...g.nodes, ...preservedNodes], [...g.edges, ...preservedEdges])
  }

  // 统一插入逻辑（点击选择 / 拖拽放入 共用）
  const insertAt = (target: PickerTarget, type: ModuleType, extra?: Partial<NodeData>) => {
    applyEdit((tree) => {
      const neu = createBlock(type, extra)
      if (target.mode === 'after') return insertAfter(tree, target.id, neu)
      return insertIntoContainer(tree, target.id, target.slot, neu)
    })
  }

  // 解析拖拽数据 → {type, extra}
  const parseDrag = (dataStr: string): { type: ModuleType; extra?: Partial<NodeData> } | null => {
    if (!dataStr) return null
    try {
      const parsed = JSON.parse(dataStr)
      if (parsed && parsed.type === 'custom_module' && parsed.moduleId) {
        return { type: 'custom_module' as ModuleType, extra: { customModuleId: parsed.moduleId } as Partial<NodeData> }
      }
    } catch { /* 普通模块字符串 */ }
    return { type: dataStr as ModuleType }
  }

  const handlePick = (type: ModuleType, extra?: Partial<NodeData>) => {
    if (!picker) return
    insertAt(picker, type, extra)
    setPicker(null)
  }

  const handleDelete = (id: string) => applyEdit((tree) => removeBlock(tree, id))
  const handleMove = (id: string, dir: -1 | 1) => applyEdit((tree) => moveBlock(tree, id, dir))

  // 投放到指定插入点（分支内/循环体内/任意位置都可）；支持新建模块 或 移动已有块
  const handleDropAt = (e: React.DragEvent, target: PickerTarget) => {
    const moveId = e.dataTransfer.getData('application/blockmove')
    if (moveId) {
      e.preventDefault()
      e.stopPropagation()
      applyEdit((tree) => moveBlockTo(tree, moveId, target))
      return
    }
    const p = parseDrag(e.dataTransfer.getData('application/reactflow'))
    if (!p) return
    e.preventDefault()
    e.stopPropagation()
    insertAt(target, p.type, p.extra)
  }

  // 从左侧拖模块到空白处：追加到顶层末尾；拖动已有块到空白处：移到末尾
  const handleCanvasDrop = (e: React.DragEvent) => {
    setDropActive(false)
    const moveId = e.dataTransfer.getData('application/blockmove')
    if (moveId) {
      e.preventDefault()
      applyEdit((tree) => moveBlockTo(tree, moveId, { mode: 'after', id: null }))
      return
    }
    const p = parseDrag(e.dataTransfer.getData('application/reactflow'))
    if (!p) return
    e.preventDefault()
    insertAt({ mode: 'after', id: null }, p.type, p.extra)
  }

  const INDENT = 24

  // 插入点：既可点击弹出选择器，也可直接把模块拖进来（投放区）
  const InsertBtn = ({ target, label }: { target: PickerTarget; label?: string }) => {
    const active = picker && JSON.stringify(picker) === JSON.stringify(target)
    const [over, setOver] = useState(false)
    return (
      <div className="relative">
        <div
          onDragOver={(e) => { if (e.dataTransfer.types.includes('application/reactflow') || e.dataTransfer.types.includes('application/blockmove')) { e.preventDefault(); e.stopPropagation(); setOver(true) } }}
          onDragLeave={() => setOver(false)}
          onDrop={(e) => { setOver(false); handleDropAt(e, target) }}
          className={over ? 'rounded-[7px] ring-2 ring-[hsl(var(--brand-500))] bg-[hsl(var(--brand-50))]' : ''}
        >
          <button
            onClick={() => setPicker(active ? null : target)}
            className={
              'flex items-center gap-1 rounded-[7px] text-[11.5px] font-medium transition-all ' +
              (label
                ? 'px-2.5 py-1 border border-dashed border-[hsl(var(--brand-500)/0.4)] text-[hsl(var(--brand-600))] hover:bg-[hsl(var(--brand-50))] hover:border-[hsl(var(--brand-500))]'
                : 'px-1.5 py-0.5 text-[hsl(var(--slate-400))] hover:text-[hsl(var(--brand-600))]')
            }
          >
            <Plus className="w-3.5 h-3.5" />{over ? '松手放入此处' : label}
          </button>
        </div>
        {active && <ModulePicker onPick={(t) => handlePick(t)} onClose={() => setPicker(null)} />}
      </div>
    )
  }


  // 单个模块卡片
  const Card = ({ block, depth, prefix, badge }: { block: Block; depth: number; prefix?: string; badge?: string }) => {
    const node = block.node
    const data = node.data as NodeData
    const type = data.moduleType as ModuleType
    const Icon = moduleIcons[type]
    const borderClass = (moduleColors[type] || '').split(' ').find((c) => c.startsWith('border-')) || 'border-slate-400'
    const summary = getSummary(data)
    const selected = node.id === selectedNodeId
    return (
      <div
        draggable
        onDragStart={(e) => { e.dataTransfer.setData('application/blockmove', block.id); e.dataTransfer.effectAllowed = 'move' }}
        onClick={() => selectNode(node.id)}
        className={
          'group relative flex items-center gap-2.5 rounded-[10px] border-l-4 bg-[hsl(var(--card))] px-3 py-2.5 cursor-grab active:cursor-grabbing ' +
          'shadow-soft transition-all duration-150 hover:shadow-pop ' + borderClass + ' ' +
          (selected ? 'ring-2 ring-[hsl(var(--brand-500))]' : '')
        }
      >
        {depth > 0 && <CornerDownRight className="w-3.5 h-3.5 text-[hsl(var(--slate-300))] flex-shrink-0" />}
        <span className="flex items-center justify-center w-7 h-7 rounded-[7px] bg-[hsl(var(--slate-50))] flex-shrink-0">
          {Icon && <Icon className="w-4 h-4" />}
        </span>
        <div className="flex-1 min-w-0">
          <div className="text-[13px] font-semibold text-[hsl(var(--slate-800))] truncate">
            {prefix}{(data.name as string) || moduleTypeLabels[type] || type}
          </div>
          {summary && <div className="text-[11px] text-[hsl(var(--muted-foreground))] truncate mt-0.5">{summary}</div>}
        </div>
        {badge && <span className="text-[9.5px] font-semibold px-1.5 py-0.5 rounded-full bg-[hsl(var(--warning-50))] text-[hsl(var(--warning-700))] flex-shrink-0">{badge}</span>}
        <div className="flex items-center opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
          <button onClick={(e) => { e.stopPropagation(); handleMove(block.id, -1) }} className="p-1 rounded text-[hsl(var(--slate-400))] hover:text-[hsl(var(--brand-600))] hover:bg-[hsl(var(--brand-50))]" title="上移"><ChevronUp className="w-3.5 h-3.5" /></button>
          <button onClick={(e) => { e.stopPropagation(); handleMove(block.id, 1) }} className="p-1 rounded text-[hsl(var(--slate-400))] hover:text-[hsl(var(--brand-600))] hover:bg-[hsl(var(--brand-50))]" title="下移"><ChevronDown className="w-3.5 h-3.5" /></button>
          <button onClick={(e) => { e.stopPropagation(); handleDelete(block.id) }} className="p-1 rounded text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--danger-600))] hover:bg-[hsl(var(--danger-50))]" title="删除"><Trash2 className="w-3.5 h-3.5" /></button>
        </div>
      </div>
    )
  }

  const Marker = ({ text, depth }: { text: string; depth: number }) => (
    <div style={{ paddingLeft: depth * INDENT }} className="py-0.5">
      <div className="flex items-center px-3 py-1.5 rounded-[8px] bg-[hsl(var(--slate-100))] border border-dashed border-[hsl(var(--slate-300))]">
        <span className="text-[11.5px] font-semibold text-[hsl(var(--slate-500))]">{text}</span>
      </div>
    </div>
  )

  const renderSeq = (seq: Block[], depth: number): React.ReactNode[] => {
    const out: React.ReactNode[] = []
    for (const b of seq) {
      const pad = depth * INDENT
      if (b.kind === 'step') {
        out.push(<div key={b.id} style={{ paddingLeft: pad }} className="py-0.5"><Card block={b} depth={depth} /></div>)
      } else if (b.kind === 'if') {
        out.push(<div key={b.id} style={{ paddingLeft: pad }} className="py-0.5"><Card block={b} depth={depth} prefix="如果　" badge="条件" /></div>)
        out.push(...renderSeq(b.then, depth + 1))
        out.push(<div key={b.id + '+then'} style={{ paddingLeft: (depth + 1) * INDENT }} className="py-0.5"><InsertBtn target={{ mode: 'into', id: b.id, slot: 'then' }} label="添加「是」分支步骤" /></div>)
        out.push(<Marker key={b.id + 'else'} text="否则" depth={depth} />)
        out.push(...renderSeq(b.els, depth + 1))
        out.push(<div key={b.id + '+els'} style={{ paddingLeft: (depth + 1) * INDENT }} className="py-0.5"><InsertBtn target={{ mode: 'into', id: b.id, slot: 'els' }} label="添加「否」分支步骤" /></div>)
        out.push(<Marker key={b.id + 'endif'} text="结束判断" depth={depth} />)
      } else {
        out.push(<div key={b.id} style={{ paddingLeft: pad }} className="py-0.5"><Card block={b} depth={depth} prefix="循环　" badge="循环" /></div>)
        out.push(...renderSeq(b.body, depth + 1))
        out.push(<div key={b.id + '+body'} style={{ paddingLeft: (depth + 1) * INDENT }} className="py-0.5"><InsertBtn target={{ mode: 'into', id: b.id, slot: 'body' }} label="添加循环体步骤" /></div>)
        out.push(<Marker key={b.id + 'endloop'} text="结束循环" depth={depth} />)
      }
      // 每个块之后的插入点（同层）
      out.push(<div key={b.id + '+after'} style={{ paddingLeft: pad }} className="flex justify-start py-0.5"><InsertBtn target={{ mode: 'after', id: b.id }} /></div>)
    }
    return out
  }

  return (
    <div
      className={'h-full w-full overflow-y-auto bg-[hsl(var(--background))] py-6 px-4 ' + (dropActive ? 'ring-2 ring-inset ring-[hsl(var(--brand-500))] bg-[hsl(var(--brand-50))]' : '')}
      onDragOver={(e) => { if (e.dataTransfer.types.includes('application/reactflow') || e.dataTransfer.types.includes('application/blockmove')) { e.preventDefault(); setDropActive(true) } }}
      onDragLeave={() => setDropActive(false)}
      onDrop={handleCanvasDrop}
    >
      <div className="max-w-[700px] mx-auto">
        {blocks.length === 0 && (
          <div className="text-center py-12 text-[13px] text-[hsl(var(--muted-foreground))]">从左侧拖拽模块到这里，或点击下方「添加模块」开始搭建流程</div>
        )}
        {renderSeq(blocks, 0)}
        <div className="flex justify-center mt-3">
          <InsertBtn target={{ mode: 'after', id: null }} label="添加模块" />
        </div>
        <div className="mt-4 text-center text-[11px] text-[hsl(var(--muted-foreground))]">
          条件 / 循环模块会自动生成「是 / 否 / 结束判断」「循环体 / 结束循环」结构，可在各分支内继续添加步骤
        </div>
      </div>
    </div>
  )
}
