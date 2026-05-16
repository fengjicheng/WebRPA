import { memo, useState, useCallback } from 'react'
import { Handle, Position, NodeResizer, type NodeProps, useReactFlow } from '@xyflow/react'
import { MessageSquare, GripVertical, Workflow } from 'lucide-react'
import type { NodeData } from '@/store/workflowStore'

export interface GroupNodeData {
  label: string
  moduleType: 'group'
  color?: string
  isSubflow?: boolean  // 是否为子流程定义
  subflowName?: string // 子流程名称（用于调用）
  width?: number       // 分组宽度（用于后端计算）
  height?: number      // 分组高度（用于后端计算）
}

const COLORS = [
  { name: '蓝色', value: '#3b82f6', bg: 'rgba(59, 130, 246, 0.1)', border: 'rgba(59, 130, 246, 0.3)' },
  { name: '绿色', value: '#22c55e', bg: 'rgba(34, 197, 94, 0.1)', border: 'rgba(34, 197, 94, 0.3)' },
  { name: '紫色', value: '#a855f7', bg: 'rgba(168, 85, 247, 0.1)', border: 'rgba(168, 85, 247, 0.3)' },
  { name: '橙色', value: '#f97316', bg: 'rgba(249, 115, 22, 0.1)', border: 'rgba(249, 115, 22, 0.3)' },
  { name: '红色', value: '#ef4444', bg: 'rgba(239, 68, 68, 0.1)', border: 'rgba(239, 68, 68, 0.3)' },
  { name: '青色', value: '#06b6d4', bg: 'rgba(6, 182, 212, 0.1)', border: 'rgba(6, 182, 212, 0.3)' },
  { name: '粉色', value: '#ec4899', bg: 'rgba(236, 72, 153, 0.1)', border: 'rgba(236, 72, 153, 0.3)' },
  { name: '灰色', value: '#6b7280', bg: 'rgba(107, 114, 128, 0.1)', border: 'rgba(107, 114, 128, 0.3)' },
]

// 子流程专用颜色
const SUBFLOW_COLOR = { 
  name: '子流程', 
  value: '#10b981', 
  bg: 'rgba(16, 185, 129, 0.15)', 
  border: 'rgba(16, 185, 129, 0.4)' 
}

export const GroupNode = memo(({ id, data, selected }: NodeProps) => {
  const nodeData = data as unknown as GroupNodeData
  const { setNodes } = useReactFlow()
  const [isEditing, setIsEditing] = useState(false)
  const [editValue, setEditValue] = useState(nodeData.label || '')
  
  const isSubflow = nodeData.isSubflow === true
  const colorConfig = isSubflow ? SUBFLOW_COLOR : (COLORS.find(c => c.value === nodeData.color) || COLORS[0])

  const handleDoubleClick = useCallback(() => {
    setIsEditing(true)
    setEditValue(nodeData.label || '')
  }, [nodeData.label])

  const handleBlur = useCallback(() => {
    setIsEditing(false)
    const oldName = nodeData.subflowName || nodeData.label || ''
    const newName = editValue
    
    // 使用 setNodes 正确更新节点数据
    setNodes((nodes) =>
      nodes.map((node) => {
        // 更新当前分组节点
        if (node.id === id) {
          const updatedData: NodeData = {
            ...node.data,
            label: editValue,
            moduleType: node.data.moduleType as any,
          }
          
          // 如果是子流程，同步更新 subflowName
          if (isSubflow && editValue) {
            (updatedData as any).subflowName = editValue
          }
          
          return {
            ...node,
            data: updatedData,
          }
        }
        
        // 如果是子流程且名称改变了，同步更新所有引用该子流程的模块
        if (isSubflow && oldName && oldName !== newName && 
            node.data.moduleType === 'subflow' && node.data.subflowName === oldName) {
          return {
            ...node,
            data: {
              ...node.data,
              subflowName: newName,
            },
          }
        }
        
        return node
      })
    )
  }, [editValue, nodeData, isSubflow, setNodes, id])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleBlur()
    }
    if (e.key === 'Escape') {
      setIsEditing(false)
      setEditValue(nodeData.label || '')
    }
  }, [handleBlur, nodeData.label])

  // 处理尺寸变化结束，将宽高保存到 data 中
  const handleResizeEnd = useCallback((_event: unknown, params: { width: number; height: number }) => {
    setNodes((nodes) =>
      nodes.map((node) =>
        node.id === id
          ? { ...node, data: { ...node.data, width: params.width, height: params.height } }
          : node
      )
    )
  }, [id, setNodes])

  return (
    <>
      <NodeResizer
        minWidth={200}
        minHeight={150}
        isVisible={selected}
        lineClassName={isSubflow ? "!border-emerald-500" : "!border-primary"}
        handleClassName="!w-3 !h-3 !bg-primary !border-2 !border-background"
        onResizeEnd={handleResizeEnd}
      />
      
      <div
        className="w-full h-full rounded-lg relative"
        style={{
          backgroundColor: colorConfig.bg,
          border: `2px ${isSubflow ? 'solid' : 'dashed'} ${selected ? colorConfig.value : colorConfig.border}`,
        }}
      >
        {/* 标题栏 */}
        <div
          className="absolute -top-7 left-0 flex items-center gap-1.5 px-2 py-1 rounded-t-md text-white text-sm font-medium cursor-move"
          style={{ backgroundColor: colorConfig.value }}
          onDoubleClick={handleDoubleClick}
        >
          <GripVertical className="w-3 h-3 opacity-70" />
          {isSubflow ? (
            <Workflow className="w-3.5 h-3.5" />
          ) : (
            <MessageSquare className="w-3.5 h-3.5" />
          )}
          {isEditing ? (
            <input
              type="text"
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              onBlur={handleBlur}
              onKeyDown={handleKeyDown}
              className="bg-transparent border-none outline-none text-white text-sm w-32"
              autoFocus
              onClick={(e) => e.stopPropagation()}
              placeholder={isSubflow ? "子流程名称" : "输入备注"}
            />
          ) : (
            <span>
              {isSubflow && '📦 '}
              {nodeData.label || (isSubflow ? '未命名子流程' : '')}
            </span>
          )}
        </div>
        
        {/* 子流程标识 */}
        {isSubflow && (
          <div className="absolute top-2 right-2 bg-emerald-500 text-white text-[10px] px-1.5 py-0.5 rounded">
            子流程定义
          </div>
        )}
      </div>
      
      {/* 隐藏的连接点（分组节点不需要连接） */}
      <Handle type="target" position={Position.Top} className="!opacity-0 !w-0 !h-0" />
      <Handle type="source" position={Position.Bottom} className="!opacity-0 !w-0 !h-0" />
    </>
  )
})

GroupNode.displayName = 'GroupNode'
