/**
 * 高性能数据表格 - 用虚拟滚动渲染，无论多少行都能 60fps。
 * 仅渲染可视行 + overscan，编辑/删除/列管理保持原有行为。
 */
import { memo, useCallback, useRef, useState } from 'react'
import { Edit2, Trash2, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useVirtualizer } from '@/hooks/useVirtualizer'
import type { DataRow } from '@/store/workflowStore'

const ROW_HEIGHT = 30
const HEADER_HEIGHT = 30

interface DataTableProps {
  data: DataRow[]
  columns: string[]
  onEdit: (rowIndex: number, col: string, value: unknown) => void
  onDeleteRow: (rowIndex: number) => void
  onDeleteColumn: (col: string) => void
}

function formatCellValue(value: unknown): string {
  if (value === null || value === undefined) return ''
  if (typeof value === 'object') {
    try {
      return JSON.stringify(value)
    } catch {
      return String(value)
    }
  }
  return String(value)
}

export const DataTable = memo(function DataTable({
  data,
  columns,
  onEdit,
  onDeleteRow,
  onDeleteColumn,
}: DataTableProps) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const getScrollElement = useCallback(() => scrollRef.current, [])
  const [editingCell, setEditingCell] = useState<{ row: number; col: string } | null>(null)
  const [editValue, setEditValue] = useState('')

  const { virtualItems, totalSize } = useVirtualizer({
    count: data.length,
    getScrollElement,
    estimateSize: ROW_HEIGHT,
    overscan: 8,
  })

  const startEdit = (row: number, col: string, value: unknown) => {
    setEditingCell({ row, col })
    setEditValue(formatCellValue(value))
  }

  const saveEdit = () => {
    if (!editingCell) return
    onEdit(editingCell.row, editingCell.col, editValue)
    setEditingCell(null)
    setEditValue('')
  }

  const cancelEdit = () => {
    setEditingCell(null)
    setEditValue('')
  }

  // 计算列宽（保持每列 min-w-[120px]）
  const columnWidth = 140
  const idColumnWidth = 60
  const actionColumnWidth = 60
  const tableWidth = idColumnWidth + columns.length * columnWidth + actionColumnWidth

  return (
    <div className="flex flex-col h-full">
      {/* 表头 - 固定不滚动 */}
      <div
        className="flex bg-[hsl(var(--muted))] border-b border-[hsl(var(--border))] text-xs font-medium overflow-hidden flex-shrink-0"
        style={{ height: HEADER_HEIGHT, minWidth: tableWidth }}
      >
        <div
          className="flex items-center justify-center border-r border-[hsl(var(--border))] flex-shrink-0"
          style={{ width: idColumnWidth }}
        >
          #
        </div>
        {columns.map((col) => (
          <div
            key={col}
            className="flex items-center justify-between px-2 border-r border-[hsl(var(--border))] flex-shrink-0"
            style={{ width: columnWidth }}
          >
            <span className="truncate" title={col}>{col}</span>
            <Button
              variant="ghost"
              size="icon"
              className="w-5 h-5 opacity-50 hover:opacity-100 flex-shrink-0"
              onClick={() => onDeleteColumn(col)}
            >
              <X className="w-3 h-3" />
            </Button>
          </div>
        ))}
        <div
          className="flex items-center justify-center flex-shrink-0"
          style={{ width: actionColumnWidth }}
        >
          操作
        </div>
      </div>

      {/* 行区 - 虚拟滚动 */}
      <div ref={scrollRef} className="flex-1 overflow-auto">
        <div style={{ height: totalSize, position: 'relative', minWidth: tableWidth }}>
          {virtualItems.map((v) => {
            const row = data[v.index]
            if (!row) return null
            const rowIndex = v.index
            return (
              <div
                key={rowIndex}
                style={{
                  position: 'absolute',
                  top: v.start,
                  left: 0,
                  height: ROW_HEIGHT,
                  width: tableWidth,
                }}
                className="flex border-b border-[hsl(var(--border))] hover:bg-[hsl(var(--muted)/0.5)] text-xs"
              >
                <div
                  className="flex items-center justify-center text-[hsl(var(--muted-foreground))] border-r border-[hsl(var(--border))] flex-shrink-0"
                  style={{ width: idColumnWidth }}
                >
                  {rowIndex + 1}
                </div>
                {columns.map((col) => {
                  const value = row[col]
                  const isEditing = editingCell?.row === rowIndex && editingCell?.col === col
                  return (
                    <div
                      key={col}
                      className="flex items-center px-2 border-r border-[hsl(var(--border))] cursor-pointer hover:bg-[hsl(var(--muted))] group flex-shrink-0"
                      style={{ width: columnWidth }}
                      onClick={() => !isEditing && startEdit(rowIndex, col, value)}
                    >
                      {isEditing ? (
                        <Input
                          value={editValue}
                          onChange={(e) => setEditValue(e.target.value)}
                          className="h-6 text-xs w-full"
                          autoFocus
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') saveEdit()
                            if (e.key === 'Escape') cancelEdit()
                          }}
                          onBlur={saveEdit}
                          onClick={(e) => e.stopPropagation()}
                        />
                      ) : (
                        <>
                          <span className="truncate flex-1" title={formatCellValue(value)}>
                            {formatCellValue(value)}
                          </span>
                          <Edit2 className="w-3 h-3 opacity-0 group-hover:opacity-50 flex-shrink-0" />
                        </>
                      )}
                    </div>
                  )
                })}
                <div
                  className="flex items-center justify-center flex-shrink-0"
                  style={{ width: actionColumnWidth }}
                >
                  <Button
                    variant="ghost"
                    size="icon"
                    className="w-5 h-5"
                    onClick={() => onDeleteRow(rowIndex)}
                  >
                    <Trash2 className="w-3 h-3 text-[hsl(var(--danger-500))]" />
                  </Button>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
})
