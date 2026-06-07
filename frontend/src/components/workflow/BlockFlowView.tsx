/**
 * 模块条视图（影刀式结构化编辑）
 *
 * 纯模块条模式即可搭建任意工作流（含条件/循环/嵌套），无需切回流程图。
 * 以「结构树」为操作对象，每次编辑后由树重新生成完整的图（自动连线）。
 */
import { useMemo, useState } from 'react'
import { createPortal } from 'react-dom'
import type React from 'react'
import { useWorkflowStore, moduleTypeLabels, type NodeData } from '@/store/workflowStore'
import { moduleIcons, moduleCategories } from './ModuleSidebar'
import { moduleColors } from './moduleColors'
import { Plus, Search, Trash2, X, ChevronUp, ChevronDown } from 'lucide-react'
import type { ModuleType } from '@/types'
import {
  parseGraphToBlocks, generateGraphFromBlocks, createBlock,
  insertAfter, insertBefore, insertIntoContainer, removeBlock, moveBlock, moveBlockTo,
  CONDITION_TYPES, LOOP_TYPES, type Block,
} from './blockFlowModel'

// 插入目标：在某 block 之前/之后，或插入某容器的分支/循环体
type PickerTarget =
  | { mode: 'before'; id: string }
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

/** 模块选择弹层（portal 到 body，fixed 定位，避免被滚动容器裁剪） */
function ModulePicker({ x, y, onPick, onClose }: { x: number; y: number; onPick: (t: ModuleType) => void; onClose: () => void }) {
  const [query, setQuery] = useState('')
  const q = query.trim().toLowerCase()
  const filtered = useMemo(() => moduleCategories
    .map((cat) => ({ ...cat, modules: cat.modules.filter((m) => !q || (moduleTypeLabels[m] || m).toLowerCase().includes(q) || m.toLowerCase().includes(q)) }))
    .filter((cat) => cat.modules.length > 0), [q])
  // 视口内夹取，避免溢出
  const W = 340, H = 420
  const left = Math.max(8, Math.min(x, window.innerWidth - W - 8))
  const top = Math.max(8, Math.min(y, window.innerHeight - H - 8))
  return createPortal(
    <>
      <div className="fixed inset-0 z-[9998]" onClick={onClose} />
      <div
        className="fixed z-[9999] w-[340px] max-h-[420px] overflow-hidden flex flex-col rounded-[12px] border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-pop-2xl animate-scale-in"
        style={{ left, top }}
        onClick={(e) => e.stopPropagation()}
      >
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
    </>,
    document.body,
  )
}


export function BlockFlowView() {
  const nodes = useWorkflowStore((s) => s.nodes)
  const edges = useWorkflowStore((s) => s.edges)
  const selectedNodeId = useWorkflowStore((s) => s.selectedNodeId)
  const selectNode = useWorkflowStore((s) => s.selectNode)
  const setGraph = useWorkflowStore((s) => s.setGraph)

  const blocks = useMemo(() => parseGraphToBlocks(nodes, edges), [nodes, edges])
  const [picker, setPicker] = useState<{ target: PickerTarget; x: number; y: number } | null>(null)
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
      if (target.mode === 'before') return insertBefore(tree, target.id, neu)
      return insertIntoContainer(tree, target.id, target.slot, neu)
    })
  }

  // 打开模块选择弹层（记录锚点坐标，portal 定位）
  const openPicker = (target: PickerTarget, e: React.MouseEvent) => {
    const r = (e.currentTarget as HTMLElement).getBoundingClientRect()
    setPicker({ target, x: r.left, y: r.bottom + 4 })
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
    insertAt(picker.target, type, extra)
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
  void INDENT

  // ===== 影刀风格紧凑步骤行（本身即投放区：按上/下半判断插到该行前/后）=====
  const StepRow = ({ block, num, kind }: { block: Block; num: number; kind: 'step' | 'if' | 'loop' }) => {
    const node = block.node
    const data = node.data as NodeData
    const type = data.moduleType as ModuleType
    const Icon = moduleIcons[type]
    const parts = (moduleColors[type] || '').split(' ')
    const borderCls = parts.find((c) => c.startsWith('border-')) || 'border-slate-300'
    const bgCls = parts.find((c) => c.startsWith('bg-')) || 'bg-slate-50'
    const summary = getSummary(data)
    const selected = node.id === selectedNodeId
    const title = kind === 'if' ? '如果' : kind === 'loop' ? '循环' : ''
    const [dropPos, setDropPos] = useState<'top' | 'bottom' | null>(null)
    const onRowDragOver = (e: React.DragEvent) => {
      if (!(e.dataTransfer.types.includes('application/reactflow') || e.dataTransfer.types.includes('application/blockmove'))) return
      e.preventDefault(); e.stopPropagation()
      const r = e.currentTarget.getBoundingClientRect()
      setDropPos(e.clientY < r.top + r.height / 2 ? 'top' : 'bottom')
    }
    const onRowDrop = (e: React.DragEvent) => {
      const pos = dropPos
      setDropPos(null)
      handleDropAt(e, pos === 'top' ? { mode: 'before', id: block.id } : { mode: 'after', id: block.id })
    }
    return (
      <div
        draggable
        onDragStart={(e) => { e.dataTransfer.setData('application/blockmove', block.id); e.dataTransfer.effectAllowed = 'move' }}
        onDragOver={onRowDragOver}
        onDragLeave={() => setDropPos(null)}
        onDrop={onRowDrop}
        onClick={() => selectNode(node.id)}
        className={
          'group/row relative flex items-center gap-2 pl-1.5 pr-1.5 py-1.5 rounded-[7px] border border-l-[3px] cursor-grab active:cursor-grabbing transition-all ' +
          bgCls + ' ' + borderCls + ' ' +
          (selected ? 'ring-2 ring-[hsl(var(--brand-500)/0.6)] shadow-sm' : 'hover:brightness-[0.97] hover:shadow-sm')
        }
      >
        {dropPos && <div className={'absolute left-1 right-1 h-[2.5px] rounded bg-[hsl(var(--brand-500))] z-10 ' + (dropPos === 'top' ? 'top-0' : 'bottom-0')} />}
        <span className="w-5 text-right text-[10px] font-mono text-[hsl(var(--slate-500))] flex-shrink-0">{num}</span>
        <span className={'flex items-center justify-center w-6 h-6 rounded-[6px] bg-white/85 border ' + borderCls + ' flex-shrink-0'}>
          {Icon && <Icon className="w-3.5 h-3.5 text-[hsl(var(--slate-700))]" />}
        </span>
        <div className="flex-1 min-w-0 flex items-baseline gap-2">
          <span className="text-[12.5px] font-medium text-[hsl(var(--slate-800))] whitespace-nowrap">
            {title && <span className="text-[hsl(var(--brand-700))] font-semibold mr-1">{title}</span>}
            {(data.name as string) || moduleTypeLabels[type] || type}
          </span>
          {summary && <span className="text-[11px] text-[hsl(var(--slate-600))] truncate">{summary}</span>}
        </div>
        <div className="flex items-center gap-0.5 opacity-0 group-hover/row:opacity-100 transition-opacity flex-shrink-0">
          <button onClick={(e) => { e.stopPropagation(); handleMove(block.id, -1) }} className="p-0.5 rounded text-[hsl(var(--slate-400))] hover:text-[hsl(var(--brand-600))] hover:bg-[hsl(var(--brand-50))]" title="上移"><ChevronUp className="w-3.5 h-3.5" /></button>
          <button onClick={(e) => { e.stopPropagation(); handleMove(block.id, 1) }} className="p-0.5 rounded text-[hsl(var(--slate-400))] hover:text-[hsl(var(--brand-600))] hover:bg-[hsl(var(--brand-50))]" title="下移"><ChevronDown className="w-3.5 h-3.5" /></button>
          <button onClick={(e) => { e.stopPropagation(); handleDelete(block.id) }} className="p-0.5 rounded text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--danger-600))] hover:bg-[hsl(var(--danger-50))]" title="删除"><Trash2 className="w-3.5 h-3.5" /></button>
        </div>
      </div>
    )
  }

  // ===== 悬停才显形的细插入线（点击弹选择器；兼作投放区）=====
  const HoverInsert = ({ target }: { target: PickerTarget }) => {
    const [over, setOver] = useState(false)
    return (
      <div
        className="relative group/ins flex items-center h-2.5"
        onDragOver={(e) => { if (e.dataTransfer.types.includes('application/reactflow') || e.dataTransfer.types.includes('application/blockmove')) { e.preventDefault(); e.stopPropagation(); setOver(true) } }}
        onDragLeave={() => setOver(false)}
        onDrop={(e) => { setOver(false); handleDropAt(e, target) }}
      >
        <div className={'flex-1 h-[2px] rounded transition-colors ' + (over ? 'bg-[hsl(var(--brand-500))]' : 'bg-transparent group-hover/ins:bg-[hsl(var(--brand-500)/0.25)]')} />
        <button
          onClick={(e) => { e.stopPropagation(); openPicker(target, e) }}
          className={'absolute left-3 flex items-center justify-center w-4 h-4 rounded-full bg-[hsl(var(--card))] border border-[hsl(var(--brand-500)/0.5)] text-[hsl(var(--brand-600))] transition-opacity ' + (over ? 'opacity-100' : 'opacity-0 group-hover/ins:opacity-100')}
          title="在此处插入模块"
        >
          <Plus className="w-2.5 h-2.5" />
        </button>
      </div>
    )
  }

  // 空分支/循环体的占位（可点可拖入）
  const EmptySlot = ({ target, text }: { target: PickerTarget; text: string }) => {
    const [over, setOver] = useState(false)
    return (
      <div
        onDragOver={(e) => { if (e.dataTransfer.types.includes('application/reactflow') || e.dataTransfer.types.includes('application/blockmove')) { e.preventDefault(); e.stopPropagation(); setOver(true) } }}
        onDragLeave={() => setOver(false)}
        onDrop={(e) => { setOver(false); handleDropAt(e, target) }}
        onClick={(e) => openPicker(target, e)}
        className={'flex items-center gap-1.5 px-2.5 py-1.5 rounded-[7px] border border-dashed cursor-pointer text-[11.5px] transition-colors ' +
          (over ? 'border-[hsl(var(--brand-500))] bg-[hsl(var(--brand-50))] text-[hsl(var(--brand-700))]' : 'border-[hsl(var(--slate-300))] text-[hsl(var(--slate-400))] hover:border-[hsl(var(--brand-500)/0.5)] hover:text-[hsl(var(--brand-600))]')}
      >
        <Plus className="w-3.5 h-3.5" /> {over ? '松手放入此处' : text}
      </div>
    )
  }

  // 渲染一个序列（counter 维护全局序号）
  const renderSeq = (seq: Block[], counter: { n: number }): React.ReactNode[] => {
    const out: React.ReactNode[] = []
    seq.forEach((b) => {
      out.push(<HoverInsert key={b.id + '^before'} target={{ mode: 'before', id: b.id }} />)
      const num = ++counter.n
      if (b.kind === 'step') {
        out.push(<StepRow key={b.id} block={b} num={num} kind="step" />)
      } else if (b.kind === 'if') {
        out.push(
          <div key={b.id} className="rounded-[9px] border border-[hsl(var(--brand-500)/0.25)] bg-[hsl(var(--brand-50)/0.35)] overflow-hidden">
            <StepRow block={b} num={num} kind="if" />
            <div className="ml-3 pl-2 border-l-2 border-[hsl(var(--brand-500)/0.35)] py-1 pr-1">
              {renderSeq(b.then, counter)}
              <EmptySlot target={{ mode: 'into', id: b.id, slot: 'then' }} text="添加「是」分支步骤" />
            </div>
            <div className="px-3 py-1 text-[11px] font-semibold text-[hsl(var(--brand-700))] bg-[hsl(var(--brand-50)/0.6)]">否则</div>
            <div className="ml-3 pl-2 border-l-2 border-[hsl(var(--slate-300))] py-1 pr-1">
              {renderSeq(b.els, counter)}
              <EmptySlot target={{ mode: 'into', id: b.id, slot: 'els' }} text="添加「否」分支步骤" />
            </div>
            <div className="px-3 py-1 text-[10.5px] text-[hsl(var(--slate-400))] border-t border-[hsl(var(--brand-500)/0.15)]">结束判断</div>
          </div>
        )
      } else {
        out.push(
          <div key={b.id} className="rounded-[9px] border border-[hsl(var(--teal-500)/0.3)] bg-[hsl(var(--teal-50)/0.4)] overflow-hidden">
            <StepRow block={b} num={num} kind="loop" />
            <div className="ml-3 pl-2 border-l-2 border-[hsl(var(--teal-500)/0.4)] py-1 pr-1">
              {renderSeq(b.body, counter)}
              <EmptySlot target={{ mode: 'into', id: b.id, slot: 'body' }} text="添加循环体步骤" />
            </div>
            <div className="px-3 py-1 text-[10.5px] text-[hsl(var(--slate-400))] border-t border-[hsl(var(--teal-500)/0.15)]">结束循环</div>
          </div>
        )
      }
    })
    return out
  }

  return (
    <div
      className={'h-full w-full overflow-y-auto bg-[hsl(var(--background))] py-5 px-4 ' + (dropActive ? 'ring-2 ring-inset ring-[hsl(var(--brand-500))]' : '')}
      onDragOver={(e) => { if (e.dataTransfer.types.includes('application/reactflow') || e.dataTransfer.types.includes('application/blockmove')) { e.preventDefault(); setDropActive(true) } }}
      onDragLeave={() => setDropActive(false)}
      onDrop={handleCanvasDrop}
    >
      <div className="w-full max-w-[1280px] mx-auto">
        {blocks.length === 0 && (
          <div className="text-center py-12 text-[13px] text-[hsl(var(--muted-foreground))]">从左侧拖拽模块到这里，或点击下方「添加模块」开始搭建流程</div>
        )}
        {renderSeq(blocks, { n: 0 })}
        <div className="mt-2">
          <EmptySlot target={{ mode: 'after', id: null }} text="添加模块" />
        </div>
      </div>
      {picker && (
        <ModulePicker
          x={picker.x}
          y={picker.y}
          onPick={(t) => handlePick(t)}
          onClose={() => setPicker(null)}
        />
      )}
    </div>
  )
}
