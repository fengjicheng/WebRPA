import { useWorkflowStore } from '@/store/workflowStore'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { SelectNative as Select } from '@/components/ui/select-native'
import { Plus, Trash2, ChevronDown, ChevronRight } from 'lucide-react'
import { useState, useCallback } from 'react'
import type { VariableType } from '@/types'

// 变量类型标签
const typeLabels: Record<VariableType, string> = {
  string: '字符串',
  number: '数字',
  boolean: '布尔',
  array: '列表',
  object: '字典',
}

// 变量类型颜色
const typeColors: Record<VariableType, string> = {
  string: 'bg-blue-100 text-blue-700',
  number: 'bg-green-100 text-green-700',
  boolean: 'bg-purple-100 text-purple-700',
  array: 'bg-orange-100 text-orange-700',
  object: 'bg-pink-100 text-pink-700',
}

// 变量重命名确认弹窗
function RenameConfirmDialog({
  oldName,
  newName,
  usageCount,
  onConfirm,
  onCancel,
}: {
  oldName: string
  newName: string
  usageCount: number
  onConfirm: () => void
  onCancel: () => void
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl w-[420px] mx-4 overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* 顶部渐变装饰 */}
        <div className="h-1.5 bg-gradient-to-r from-blue-500 via-cyan-500 to-teal-500" />
        
        <div className="p-6">
          {/* 图标和标题 */}
          <div className="flex items-center gap-3 mb-5">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-600 flex items-center justify-center shadow-lg shadow-blue-500/25">
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
              </svg>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">变量重命名</h3>
              <p className="text-xs text-gray-500">检测到变量引用需要更新</p>
            </div>
          </div>
          
          {/* 变量变更展示 */}
          <div className="bg-gradient-to-r from-gray-50 to-gray-100/50 rounded-xl p-4 mb-5">
            <div className="flex items-center justify-center gap-3">
              <div className="flex items-center gap-2 px-3 py-2 bg-white rounded-lg shadow-sm border border-gray-200">
                <span className="text-xs text-gray-500">原名</span>
                <code className="text-sm font-mono font-semibold text-red-600">{'{' + oldName + '}'}</code>
              </div>
              <div className="flex items-center justify-center w-8 h-8 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 shadow-md">
                <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </div>
              <div className="flex items-center gap-2 px-3 py-2 bg-white rounded-lg shadow-sm border border-gray-200">
                <span className="text-xs text-gray-500">新名</span>
                <code className="text-sm font-mono font-semibold text-emerald-600">{'{' + newName + '}'}</code>
              </div>
            </div>
          </div>
          
          {/* 引用数量提示 */}
          <div className="flex items-center gap-2 px-4 py-3 bg-amber-50 border border-amber-200 rounded-xl mb-6">
            <svg className="w-5 h-5 text-amber-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-sm text-amber-800">
              发现 <span className="font-bold text-amber-900">{usageCount}</span> 处引用了此变量
            </p>
          </div>
          
          {/* 按钮组 */}
          <div className="flex gap-3">
            <button
              onClick={onCancel}
              className="flex-1 px-4 py-2.5 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-xl transition-all duration-200 hover:shadow-md active:scale-[0.98]"
            >
              仅改名称
            </button>
            <button
              onClick={onConfirm}
              className="flex-1 px-4 py-2.5 text-sm font-medium text-white bg-gradient-to-r from-blue-500 to-cyan-600 hover:from-blue-600 hover:to-cyan-700 rounded-xl transition-all duration-200 shadow-lg shadow-blue-500/25 hover:shadow-xl hover:shadow-blue-500/30 active:scale-[0.98]"
            >
              全部更新
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export function VariablePanel() {
  const variables = useWorkflowStore((state) => state.variables)
  const addVariable = useWorkflowStore((state) => state.addVariable)
  const updateVariable = useWorkflowStore((state) => state.updateVariable)
  const deleteVariable = useWorkflowStore((state) => state.deleteVariable)
  const renameVariable = useWorkflowStore((state) => state.renameVariable)
  const findVariableUsages = useWorkflowStore((state) => state.findVariableUsages)
  const replaceVariableReferences = useWorkflowStore((state) => state.replaceVariableReferences)

  const [newVarName, setNewVarName] = useState('')
  const [newVarValue, setNewVarValue] = useState('')
  const [newVarType, setNewVarType] = useState<VariableType>('string')
  const [expandedVars, setExpandedVars] = useState<Set<string>>(new Set())
  const [selectedVarName, setSelectedVarName] = useState<string | null>(null)
  
  // 变量重命名状态
  const [editingVarName, setEditingVarName] = useState<string | null>(null)
  const [editingNewName, setEditingNewName] = useState('')
  const [renameDialog, setRenameDialog] = useState<{
    oldName: string
    newName: string
    usageCount: number
  } | null>(null)

  // 处理键盘事件（Delete删除选中变量）
  const handleKeyDown = useCallback((e: React.KeyboardEvent, varName: string) => {
    if (e.key === 'Delete' || e.key === 'Backspace') {
      e.preventDefault()
      deleteVariable(varName)
      setSelectedVarName(null)
    }
  }, [deleteVariable])

  // 解析输入值为对应类型
  const parseValue = (value: string, type: VariableType): unknown => {
    try {
      switch (type) {
        case 'number':
          const num = parseFloat(value)
          return isNaN(num) ? 0 : num
        case 'boolean':
          return value.toLowerCase() === 'true' || value === '1'
        case 'array':
          if (!value.trim()) return []
          return JSON.parse(value)
        case 'object':
          if (!value.trim()) return {}
          return JSON.parse(value)
        default:
          return value
      }
    } catch {
      // 解析失败返回默认值
      if (type === 'array') return []
      if (type === 'object') return {}
      return value
    }
  }

  // 获取类型的默认值
  const getDefaultValue = (type: VariableType): string => {
    switch (type) {
      case 'number': return '0'
      case 'boolean': return 'false'
      case 'array': return '[]'
      case 'object': return '{}'
      default: return ''
    }
  }

  const handleAddVariable = () => {
    if (!newVarName.trim()) return

    const value = newVarValue.trim() || getDefaultValue(newVarType)
    const parsedValue = parseValue(value, newVarType)

    addVariable({
      name: newVarName.trim(),
      value: parsedValue,
      type: newVarType,
      scope: 'global',
    })

    setNewVarName('')
    setNewVarValue('')
    setNewVarType('string')
  }

  const handleTypeChange = (type: VariableType) => {
    setNewVarType(type)
    setNewVarValue(getDefaultValue(type))
  }

  const formatValue = (value: unknown): string => {
    if (value === null || value === undefined) return ''
    if (typeof value === 'object') return JSON.stringify(value, null, 2)
    return String(value)
  }

  const formatDisplayValue = (value: unknown, type: VariableType): string => {
    if (value === null || value === undefined) return ''
    if (type === 'array' && Array.isArray(value)) {
      return `[${value.length}项]`
    }
    if (type === 'object' && typeof value === 'object') {
      return `{${Object.keys(value as object).length}个键}`
    }
    if (typeof value === 'object') return JSON.stringify(value)
    return String(value)
  }

  const toggleExpand = (name: string) => {
    const newExpanded = new Set(expandedVars)
    if (newExpanded.has(name)) {
      newExpanded.delete(name)
    } else {
      newExpanded.add(name)
    }
    setExpandedVars(newExpanded)
  }

  const handleUpdateVariable = (name: string, value: string, type: VariableType) => {
    const parsedValue = parseValue(value, type)
    updateVariable(name, parsedValue)
  }

  // 开始编辑变量名
  const startEditingName = (name: string) => {
    setEditingVarName(name)
    setEditingNewName(name)
  }

  // 完成变量名编辑
  const finishEditingName = () => {
    if (!editingVarName || !editingNewName) {
      setEditingVarName(null)
      return
    }
    
    const oldName = editingVarName
    const newName = editingNewName.replace(/[^a-zA-Z0-9_\u4e00-\u9fa5]/g, '')
    
    if (!newName || oldName === newName) {
      setEditingVarName(null)
      return
    }
    
    // 检查新名称是否已存在
    if (variables.some(v => v.name === newName)) {
      setEditingVarName(null)
      return
    }
    
    // 检查是否有引用
    const usages = findVariableUsages(oldName)
    
    if (usages.length > 0) {
      setRenameDialog({
        oldName,
        newName,
        usageCount: usages.length,
      })
    } else {
      renameVariable(oldName, newName)
      setEditingVarName(null)
    }
  }

  // 确认重命名（更新所有引用）
  const handleConfirmRename = () => {
    if (!renameDialog) return
    replaceVariableReferences(renameDialog.oldName, renameDialog.newName)
    renameVariable(renameDialog.oldName, renameDialog.newName)
    setRenameDialog(null)
    setEditingVarName(null)
  }

  // 取消重命名（仅修改变量名）
  const handleCancelRename = () => {
    if (!renameDialog) return
    renameVariable(renameDialog.oldName, renameDialog.newName)
    setRenameDialog(null)
    setEditingVarName(null)
  }

  return (
    <div className="h-full flex flex-col animate-fade-in bg-gradient-to-b from-white to-emerald-50/20">
      <div className="p-3 border-b bg-gradient-to-r from-emerald-50/50 via-cyan-50/30 to-blue-50/50">
        <h3 className="text-sm font-medium mb-2 text-gradient">全局变量</h3>
        <div className="space-y-2">
          <div className="flex gap-2">
            <Input
              value={newVarName}
              onChange={(e) => setNewVarName(e.target.value)}
              placeholder="变量名"
              className="h-8 text-xs flex-1 transition-all duration-200 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
            />
            <Select
              value={newVarType}
              onChange={(e) => handleTypeChange(e.target.value as VariableType)}
              className="h-8 text-xs w-24"
            >
              <option value="string">字符串</option>
              <option value="number">数字</option>
              <option value="boolean">布尔</option>
              <option value="array">列表</option>
              <option value="object">字典</option>
            </Select>
          </div>
          <div className="flex gap-2">
            {newVarType === 'boolean' ? (
              <Select
                value={newVarValue || 'false'}
                onChange={(e) => setNewVarValue(e.target.value)}
                className="h-8 text-xs flex-1"
              >
                <option value="true">true</option>
                <option value="false">false</option>
              </Select>
            ) : (newVarType === 'array' || newVarType === 'object') ? (
              <textarea
                value={newVarValue}
                onChange={(e) => setNewVarValue(e.target.value)}
                placeholder={newVarType === 'array' ? '["item1", "item2"]' : '{"key": "value"}'}
                className="flex-1 h-16 px-2 py-1 text-xs rounded-md border border-input bg-background font-mono resize-none transition-all duration-200 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
              />
            ) : (
              <Input
                value={newVarValue}
                onChange={(e) => setNewVarValue(e.target.value)}
                placeholder={newVarType === 'number' ? '0' : '初始值'}
                type={newVarType === 'number' ? 'number' : 'text'}
                className="h-8 text-xs flex-1 transition-all duration-200 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
              />
            )}
            <Button 
              size="sm" 
              className="h-8 px-2 bg-blue-600 hover:bg-blue-700 text-white transition-all duration-200 hover:scale-105 active:scale-95" 
              onClick={handleAddVariable}
            >
              <Plus className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>

      <ScrollArea className="flex-1 p-2">
        {variables.length === 0 ? (
          <div className="text-center py-8 animate-fade-in">
            <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-gradient-to-br from-blue-50 to-cyan-50 flex items-center justify-center">
              <Plus className="w-6 h-6 text-muted-foreground/40" />
            </div>
            <p className="text-xs text-muted-foreground">
              暂无变量
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {variables.map((variable) => (
              <div
                key={variable.name}
                className={`p-2 rounded bg-muted/50 cursor-pointer outline-none transition-all duration-200 ${
                  selectedVarName === variable.name 
                    ? 'ring-2 ring-primary bg-muted shadow-sm' 
                    : 'hover:bg-muted/70'
                }`}
                tabIndex={0}
                onClick={(e) => {
                  // 只有点击容器本身时才选中，点击内部元素不选中
                  if (e.target === e.currentTarget) {
                    setSelectedVarName(variable.name)
                  }
                }}
                onFocus={() => setSelectedVarName(variable.name)}
                onKeyDown={(e) => handleKeyDown(e, variable.name)}
              >
                <div className="flex items-center gap-2">
                  {(variable.type === 'array' || variable.type === 'object') && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        toggleExpand(variable.name)
                      }}
                      className="p-1 hover:bg-muted rounded transition-colors"
                    >
                      {expandedVars.has(variable.name) ? (
                        <ChevronDown className="w-3 h-3" />
                      ) : (
                        <ChevronRight className="w-3 h-3" />
                      )}
                    </button>
                  )}
                  <div className="flex-1 min-w-0">
                    <div 
                      className="flex items-center gap-2"
                    >
                      {editingVarName === variable.name ? (
                        <Input
                          value={editingNewName}
                          onChange={(e) => setEditingNewName(e.target.value.replace(/[^a-zA-Z0-9_\u4e00-\u9fa5]/g, ''))}
                          onBlur={finishEditingName}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              e.preventDefault()
                              finishEditingName()
                            } else if (e.key === 'Escape') {
                              setEditingVarName(null)
                            }
                            e.stopPropagation()
                          }}
                          autoFocus
                          className="h-5 text-xs font-medium w-24"
                          onClick={(e) => e.stopPropagation()}
                        />
                      ) : (
                        <button
                          type="button"
                          className="px-2 py-1 rounded border border-transparent hover:border-blue-300 hover:bg-blue-50 cursor-text transition-all duration-150 text-left"
                          title="点击编辑变量名"
                          onMouseDown={(e) => {
                            e.stopPropagation()
                            e.preventDefault()
                            startEditingName(variable.name)
                          }}
                        >
                          <span className="text-xs font-medium truncate hover:text-blue-600 select-none">
                            {variable.name}
                          </span>
                        </button>
                      )}
                      <span className={`text-[10px] px-1.5 py-0.5 rounded ${typeColors[variable.type]}`}>
                        {typeLabels[variable.type]}
                      </span>
                    </div>
                    {(variable.type === 'array' || variable.type === 'object') ? (
                      <span className="text-xs text-muted-foreground">
                        {formatDisplayValue(variable.value, variable.type)}
                      </span>
                    ) : variable.type === 'boolean' ? (
                      <Select
                        value={String(variable.value)}
                        onChange={(e) => handleUpdateVariable(variable.name, e.target.value, variable.type)}
                        className="h-6 text-xs mt-1"
                      >
                        <option value="true">true</option>
                        <option value="false">false</option>
                      </Select>
                    ) : (
                      <Input
                        value={formatValue(variable.value)}
                        onChange={(e) => handleUpdateVariable(variable.name, e.target.value, variable.type)}
                        type={variable.type === 'number' ? 'number' : 'text'}
                        className="h-6 text-xs mt-1"
                      />
                    )}
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6 shrink-0 transition-all duration-200 hover:scale-110 hover:bg-red-50 active:scale-95"
                    onClick={(e) => {
                      e.stopPropagation()
                      deleteVariable(variable.name)
                    }}
                  >
                    <Trash2 className="w-3 h-3 text-destructive" />
                  </Button>
                </div>
                {/* 展开显示列表/字典内容 */}
                {expandedVars.has(variable.name) && (variable.type === 'array' || variable.type === 'object') && (
                  <div className="mt-2 pt-2 border-t">
                    <textarea
                      value={formatValue(variable.value)}
                      onChange={(e) => handleUpdateVariable(variable.name, e.target.value, variable.type)}
                      className="w-full h-24 px-2 py-1 text-xs rounded-md border border-input bg-background font-mono resize-none"
                      placeholder={variable.type === 'array' ? '["item1", "item2"]' : '{"key": "value"}'}
                    />
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </ScrollArea>

      {/* 变量引用语法提示 */}
      <div className="p-2 border-t bg-gradient-to-r from-blue-50/50 to-cyan-50/50">
        <p className="text-[10px] text-muted-foreground leading-relaxed">
          <span className="font-medium text-blue-600">引用语法：</span>
          <code className="bg-blue-100 px-1 rounded text-blue-700">{'{变量名}'}</code> · 
          <code className="bg-blue-100 px-1 rounded text-blue-700">{'{列表[0]}'}</code> · 
          <code className="bg-blue-100 px-1 rounded text-blue-700">{'{字典[键名]}'}</code>
        </p>
        <p className="text-[10px] text-muted-foreground mt-1">
          点击变量名可重命名，Delete 键可删除
        </p>
      </div>
      
      {/* 重命名确认弹窗 */}
      {renameDialog && (
        <RenameConfirmDialog
          oldName={renameDialog.oldName}
          newName={renameDialog.newName}
          usageCount={renameDialog.usageCount}
          onConfirm={handleConfirmRename}
          onCancel={handleCancelRename}
        />
      )}
    </div>
  )
}
