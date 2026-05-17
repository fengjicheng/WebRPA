import { useWorkflowStore, type DataRow } from '@/store/workflowStore'
import { motion } from 'framer-motion'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { SelectNative as Select } from '@/components/ui/select-native'
import { useConfirm } from '@/components/ui/confirm-dialog'
import { workflowApi } from '@/services/api'
import { 
  Trash2, 
  Download, 
  ChevronUp, 
  ChevronDown, 
  Plus, 
  X, 
  FileSpreadsheet,
  Edit2,
  Check,
  FileText,
  Variable,
  Search,
  Filter,
  ImageIcon,
  Database,
  Upload,
  FileDown,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useState, useCallback, useMemo, useRef, useEffect } from 'react'
import type { LogLevel, VariableType } from '@/types'
import { ExcelAssetsPanel } from './ExcelAssetsPanel'
import { ImageAssetsPanel } from './ImageAssetsPanel'
import { LogList } from './LogList'
import { DataTable } from './DataTable'

interface LogPanelProps {
  onLogClick?: (nodeId: string) => void
}

export function LogPanel({ onLogClick }: LogPanelProps) {
  const logs = useWorkflowStore((state) => state.logs)
  const clearLogs = useWorkflowStore((state) => state.clearLogs)
  const selectNode = useWorkflowStore((state) => state.selectNode)
  const variables = useWorkflowStore((state) => state.variables)
  const addVariable = useWorkflowStore((state) => state.addVariable)
  const updateVariable = useWorkflowStore((state) => state.updateVariable)
  const deleteVariable = useWorkflowStore((state) => state.deleteVariable)
  const renameVariable = useWorkflowStore((state) => state.renameVariable)
  const findVariableUsages = useWorkflowStore((state) => state.findVariableUsages)
  const replaceVariableReferences = useWorkflowStore((state) => state.replaceVariableReferences)
  const { 
    collectedData, 
    setCollectedData,
    updateDataRow, 
    deleteDataRow, 
    addDataRow,
    clearCollectedData,
    name: workflowName,
    dataAssets,
    bottomPanelTab: activeTab,
    setBottomPanelTab: setActiveTab,
    verboseLog,
    setVerboseLog,
    maxLogCount,
    setMaxLogCount,
    currentExecutionWorkflowId,
  } = useWorkflowStore()

  const { alert, ConfirmDialog } = useConfirm()
  const logEndRef = useRef<HTMLDivElement>(null)

  const [isCollapsed, setIsCollapsed] = useState(false)
  const [newColumnName, setNewColumnName] = useState('')
  const [isAddingColumn, setIsAddingColumn] = useState(false)
  
  // 日志搜索和筛选 - 改为多选模式
  const [logSearchQuery, setLogSearchQuery] = useState('')
  const [logLevelFilters, setLogLevelFilters] = useState<Set<LogLevel>>(new Set(['debug', 'info', 'success', 'warning', 'error']))
  const [showFilterDropdown, setShowFilterDropdown] = useState(false)
  
  // 变量相关状态
  const [isAddingVar, setIsAddingVar] = useState(false)
  const [newVarName, setNewVarName] = useState('')
  const [newVarValue, setNewVarValue] = useState('')
  const [newVarType, setNewVarType] = useState<VariableType>('string')
  const [editingVar, setEditingVar] = useState<string | null>(null)
  const [editVarValue, setEditVarValue] = useState('')
  
  // 变量名编辑状态
  const [editingVarName, setEditingVarName] = useState<string | null>(null)
  const [editVarNameValue, setEditVarNameValue] = useState('')
  const [renameDialog, setRenameDialog] = useState<{
    oldName: string
    newName: string
    usageCount: number
  } | null>(null)

  // 切换日志级别筛选
  const toggleLogLevelFilter = (level: LogLevel) => {
    setLogLevelFilters(prev => {
      const newFilters = new Set(prev)
      if (newFilters.has(level)) {
        newFilters.delete(level)
      } else {
        newFilters.add(level)
      }
      return newFilters
    })
  }

  // 全选/取消全选
  const toggleAllFilters = () => {
    if (logLevelFilters.size === 5) {
      setLogLevelFilters(new Set())
    } else {
      setLogLevelFilters(new Set(['debug', 'info', 'success', 'warning', 'error']))
    }
  }

  // 过滤后的日志
  const filteredLogs = useMemo(() => {
    const filtered = logs.filter(log => {
      // 类型筛选 - 多选模式
      if (logLevelFilters.size > 0 && !logLevelFilters.has(log.level)) {
        return false
      }
      // 搜索筛选
      if (logSearchQuery.trim()) {
        const query = logSearchQuery.toLowerCase()
        return log.message.toLowerCase().includes(query)
      }
      return true
    })
    // 只显示最近的日志，避免渲染过多DOM
    return filtered.slice(-maxLogCount)
  }, [logs, logLevelFilters, logSearchQuery, maxLogCount])

  // 自动滚动到最新日志
  useEffect(() => {
    // 每次 filteredLogs 变化都滚动到底部
    if (logEndRef.current && activeTab === 'logs' && filteredLogs.length > 0) {
      requestAnimationFrame(() => {
        logEndRef.current?.scrollIntoView({ behavior: 'auto' })
      })
    }
  }, [filteredLogs, activeTab])

  // 获取所有列名
  const columns = Array.from(
    new Set(collectedData.flatMap(row => Object.keys(row)))
  )

  const handleExportLogs = () => {
    const logText = filteredLogs
      .map((log) => `[${log.timestamp}] [${log.level.toUpperCase()}] ${log.message}`)
      .join('\n')
    
    const blob = new Blob([logText], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `workflow-logs-${new Date().toISOString().slice(0, 10)}.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleLogClick = (nodeId?: string) => {
    if (nodeId) {
      // 选中节点
      selectNode(nodeId)
      
      // 调用父组件传入的回调函数来定位节点
      if (onLogClick) {
        onLogClick(nodeId)
      }
    }
  }

  // 数据表格相关方法
  const handleAddRow = () => {
    const newRow: DataRow = {}
    columns.forEach(col => { newRow[col] = '' })
    if (columns.length === 0) {
      newRow['列1'] = ''
    }
    addDataRow(newRow)
  }

  const handleAddColumn = () => {
    if (!newColumnName.trim()) return
    const updatedData = collectedData.map(row => ({
      ...row,
      [newColumnName]: ''
    }))
    setCollectedData(updatedData.length > 0 ? updatedData : [{ [newColumnName]: '' }])
    setNewColumnName('')
    setIsAddingColumn(false)
  }

  const handleDeleteColumn = (colName: string) => {
    const updatedData = collectedData.map(row => {
      const newRow = { ...row }
      delete newRow[colName]
      return newRow
    })
    setCollectedData(updatedData)
  }

  const handleDownloadCSV = useCallback(async () => {
    if (collectedData.length === 0) {
      await alert('暂无数据可下载')
      return
    }
    const headers = columns.join(',')
    const rows = collectedData.map(row => 
      columns.map(col => {
        const value = String(row[col] ?? '')
        if (value.includes(',') || value.includes('"') || value.includes('\n')) {
          return `"${value.replace(/"/g, '""')}"`
        }
        return value
      }).join(',')
    )
    const BOM = '\uFEFF'
    const csvContent = BOM + [headers, ...rows].join('\n')
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${workflowName || '数据'}_${new Date().toISOString().slice(0, 10)}.csv`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }, [collectedData, columns, workflowName])

  // 下载完整数据（不受 20 条预览上限限制，从后端取全量）
  const [downloading, setDownloading] = useState(false)
  const handleDownloadFullData = useCallback(async () => {
    if (!currentExecutionWorkflowId) {
      await alert('暂无完整数据可下载，请先执行一次工作流')
      return
    }
    setDownloading(true)
    try {
      const result = await workflowApi.getFullData(currentExecutionWorkflowId)
      if (!result.success || !result.data) {
        await alert(result.error || '获取完整数据失败')
        return
      }
      const { rows, columns: serverColumns, total } = result.data
      if (!total || rows.length === 0) {
        await alert('本次执行没有收集到数据')
        return
      }
      // 列顺序：优先后端列顺序，缺失的列再从行数据中补齐
      const finalCols: string[] = [...serverColumns]
      const seen = new Set<string>(finalCols)
      rows.forEach(r => {
        Object.keys(r).forEach(k => {
          if (!seen.has(k)) {
            seen.add(k)
            finalCols.push(k)
          }
        })
      })
      const headers = finalCols.join(',')
      const csvRows = rows.map(row =>
        finalCols.map(col => {
          const value = String(row[col] ?? '')
          if (value.includes(',') || value.includes('"') || value.includes('\n')) {
            return `"${value.replace(/"/g, '""')}"`
          }
          return value
        }).join(',')
      )
      const BOM = '\uFEFF'
      const csvContent = BOM + [headers, ...csvRows].join('\n')
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `${workflowName || '数据'}_完整_${new Date().toISOString().slice(0, 10)}.csv`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
    } catch (e) {
      await alert(`下载完整数据失败: ${e}`)
    } finally {
      setDownloading(false)
    }
  }, [currentExecutionWorkflowId, workflowName, alert])

  // 变量相关方法
  const parseVariableValue = (value: string, type: VariableType): unknown => {
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
      if (type === 'array') return []
      if (type === 'object') return {}
      return value
    }
  }

  const handleAddVariable = () => {
    if (!newVarName.trim()) return
    const parsedValue = parseVariableValue(newVarValue, newVarType)
    addVariable({ name: newVarName.trim(), value: parsedValue, type: newVarType, scope: 'global' })
    setNewVarName('')
    setNewVarValue('')
    setNewVarType('string')
    setIsAddingVar(false)
  }

  const formatVariableValue = (value: unknown, type: VariableType): string => {
    if (value === null || value === undefined) return ''
    if (type === 'array' || type === 'object' || typeof value === 'object') {
      try {
        return JSON.stringify(value)
      } catch {
        return String(value)
      }
    }
    return String(value)
  }

  const startEditVar = (name: string, value: unknown, type: VariableType) => {
    setEditingVar(name)
    setEditVarValue(formatVariableValue(value, type))
  }

  const saveEditVar = () => {
    if (editingVar) {
      const variable = variables.find(v => v.name === editingVar)
      if (variable) {
        const parsedValue = parseVariableValue(editVarValue, variable.type)
        updateVariable(editingVar, parsedValue)
      }
      setEditingVar(null)
      setEditVarValue('')
    }
  }

  const startEditVarName = (name: string) => {
    setEditingVarName(name)
    setEditVarNameValue(name)
  }

  const saveEditVarName = () => {
    if (!editingVarName || !editVarNameValue) {
      setEditingVarName(null)
      return
    }
    
    const oldName = editingVarName
    const newName = editVarNameValue.replace(/[^a-zA-Z0-9_\u4e00-\u9fa5]/g, '')
    
    if (!newName || oldName === newName) {
      setEditingVarName(null)
      return
    }
    
    if (variables.some(v => v.name === newName)) {
      setEditingVarName(null)
      return
    }
    
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

  const handleConfirmRename = () => {
    if (!renameDialog) return
    replaceVariableReferences(renameDialog.oldName, renameDialog.newName)
    renameVariable(renameDialog.oldName, renameDialog.newName)
    setRenameDialog(null)
    setEditingVarName(null)
  }

  const handleCancelRename = () => {
    if (!renameDialog) return
    renameVariable(renameDialog.oldName, renameDialog.newName)
    setRenameDialog(null)
    setEditingVarName(null)
  }

  return (
    <motion.footer
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: 'spring', stiffness: 260, damping: 30, delay: 0.1 }}
      className={cn(
        'border-t bg-card transition-all',
        isCollapsed ? 'h-10' : 'h-64'
      )}
    >
      <div className="bg-[hsl(var(--card))] h-10 px-2 sm:px-4 flex items-center justify-between border-b border-[hsl(var(--border))] overflow-x-auto">
        <div className="flex items-center gap-2 sm:gap-4 min-w-0">
          {/* 分页标签 - 响应式显示 */}
          <div className="flex items-center gap-1">
            <button
              className={cn(
                'flex items-center gap-1 sm:gap-1.5 px-2 sm:px-3 py-1 text-xs sm:text-sm rounded-md transition-colors whitespace-nowrap border',
                activeTab === 'logs' 
                  ? 'bg-[hsl(var(--brand-50))] text-[hsl(var(--brand-700))] font-medium border-[hsl(var(--brand-500)/0.3)]' 
                  : 'text-[hsl(var(--muted-foreground))] border-transparent hover:bg-[hsl(var(--muted))]'
              )}
              onClick={() => setActiveTab('logs')}
            >
              <FileText className={cn('w-3 h-3 sm:w-3.5 sm:h-3.5', activeTab === 'logs' ? 'text-[hsl(var(--brand-600))]' : 'text-[hsl(217_91%_60%)]')} />
              <span className="hidden sm:inline">执行日志</span>
              <span className="sm:hidden">日志</span>
              <span className="text-[10px] sm:text-xs opacity-70">({logs.length})</span>
            </button>
            <button
              className={cn(
                'flex items-center gap-1 sm:gap-1.5 px-2 sm:px-3 py-1 text-xs sm:text-sm rounded-md transition-colors whitespace-nowrap border',
                activeTab === 'data' 
                  ? 'bg-[hsl(199_95%_94%)] text-[hsl(199_89%_38%)] font-medium border-[hsl(199_89%_48%/0.3)]' 
                  : 'text-[hsl(var(--muted-foreground))] border-transparent hover:bg-[hsl(var(--muted))]'
              )}
              onClick={() => setActiveTab('data')}
            >
              <FileSpreadsheet className={cn('w-3 h-3 sm:w-3.5 sm:h-3.5', activeTab === 'data' ? 'text-[hsl(199_89%_48%)]' : 'text-[hsl(199_70%_55%)]')} />
              <span className="hidden sm:inline">数据表格</span>
              <span className="sm:hidden">数据</span>
              <span className="text-[10px] sm:text-xs opacity-70">({collectedData.length})</span>
            </button>
            <button
              className={cn(
                'flex items-center gap-1 sm:gap-1.5 px-2 sm:px-3 py-1 text-xs sm:text-sm rounded-md transition-colors whitespace-nowrap border',
                activeTab === 'variables' 
                  ? 'bg-[hsl(270_100%_95%)] text-[hsl(270_60%_45%)] font-medium border-[hsl(270_60%_55%/0.3)]' 
                  : 'text-[hsl(var(--muted-foreground))] border-transparent hover:bg-[hsl(var(--muted))]'
              )}
              onClick={() => setActiveTab('variables')}
            >
              <Variable className={cn('w-3 h-3 sm:w-3.5 sm:h-3.5', activeTab === 'variables' ? 'text-[hsl(270_60%_55%)]' : 'text-[hsl(270_50%_60%)]')} />
              <span className="hidden sm:inline">全局变量</span>
              <span className="sm:hidden">变量</span>
              <span className="text-[10px] sm:text-xs opacity-70">({variables.length})</span>
            </button>
            <button
              className={cn(
                'flex items-center gap-1 sm:gap-1.5 px-2 sm:px-3 py-1 text-xs sm:text-sm rounded-md transition-colors whitespace-nowrap border',
                activeTab === 'assets' 
                  ? 'bg-[hsl(var(--success-50))] text-[hsl(142_71%_28%)] font-medium border-[hsl(var(--success-500)/0.3)]' 
                  : 'text-[hsl(var(--muted-foreground))] border-transparent hover:bg-[hsl(var(--muted))]'
              )}
              onClick={() => setActiveTab('assets')}
            >
              <Database className={cn('w-3 h-3 sm:w-3.5 sm:h-3.5', activeTab === 'assets' ? 'text-[hsl(var(--success-500))]' : 'text-[hsl(142_50%_50%)]')} />
              <span className="hidden md:inline">Excel资源</span>
              <span className="md:hidden">Excel</span>
              <span className="text-[10px] sm:text-xs opacity-70">({dataAssets.length})</span>
            </button>
            <button
              className={cn(
                'flex items-center gap-1 sm:gap-1.5 px-2 sm:px-3 py-1 text-xs sm:text-sm rounded-md transition-colors whitespace-nowrap border',
                activeTab === 'images' 
                  ? 'bg-[hsl(var(--warning-50))] text-[hsl(32_95%_38%)] font-medium border-[hsl(var(--warning-500)/0.3)]' 
                  : 'text-[hsl(var(--muted-foreground))] border-transparent hover:bg-[hsl(var(--muted))]'
              )}
              onClick={() => setActiveTab('images')}
            >
              <ImageIcon className={cn('w-3 h-3 sm:w-3.5 sm:h-3.5', activeTab === 'images' ? 'text-[hsl(var(--warning-500))]' : 'text-[hsl(32_70%_55%)]')} />
              <span className="hidden md:inline">图像资源</span>
              <span className="md:hidden">图像</span>
              <span className="text-[10px] sm:text-xs opacity-70">({useWorkflowStore.getState().imageAssets.length})</span>
            </button>
          </div>
        </div>
        <div className="flex items-center gap-1">
          {activeTab === 'logs' && (
            <>
              {/* 详细日志开关 */}
              <button
                className={cn(
                  'h-7 px-2 text-xs rounded-md flex items-center gap-1.5 transition-colors border',
                  verboseLog 
                    ? 'bg-[hsl(var(--success-50))] text-[hsl(var(--success-500))] border-[hsl(var(--success-500)/0.25)]' 
                    : 'bg-transparent text-[hsl(var(--muted-foreground))] border-[hsl(var(--border))] hover:bg-[hsl(var(--muted))]'
                )}
                onClick={() => setVerboseLog(!verboseLog)}
                title={verboseLog ? '切换为简洁日志' : '切换为详细日志'}
              >
                {verboseLog ? (
                  <>
                    <span className="w-2 h-2 rounded-full bg-[hsl(var(--success-500))]" />
                    详细日志
                  </>
                ) : (
                  <>
                    <span className="w-2 h-2 rounded-full bg-[hsl(var(--slate-400))]" />
                    简洁日志
                  </>
                )}
              </button>
              <Button variant="outline" size="sm" className="h-7 text-xs" onClick={handleExportLogs} title="下载日志">
                <Download className="w-3.5 h-3.5 mr-1" />
                下载
              </Button>
              <Button variant="outline" size="icon" className="h-7 w-7 text-[hsl(var(--danger-500))]" onClick={clearLogs} title="清空日志">
                <Trash2 className="w-4 h-4" />
              </Button>
            </>
          )}
          {activeTab === 'data' && (
            <>
              <Button variant="default" size="sm" className="h-7 text-xs" onClick={handleAddRow}>
                <Plus className="w-3.5 h-3.5 mr-1" />行
              </Button>
              {isAddingColumn ? (
                <div className="flex items-center gap-1">
                  <Input value={newColumnName} onChange={(e) => setNewColumnName(e.target.value)}
                    placeholder="列名" className="w-20 h-7 text-xs" onKeyDown={(e) => e.key === 'Enter' && handleAddColumn()} />
                  <Button size="icon" variant="default" className="h-7 w-7" onClick={handleAddColumn}><Check className="w-3.5 h-3.5" /></Button>
                  <Button size="icon" variant="outline" className="h-7 w-7" onClick={() => setIsAddingColumn(false)}><X className="w-3.5 h-3.5" /></Button>
                </div>
              ) : (
                <Button variant="default" size="sm" className="h-7 text-xs" onClick={() => setIsAddingColumn(true)}>
                  <Plus className="w-3.5 h-3.5 mr-1" />列
                </Button>
              )}
              <Button variant="outline" size="icon" className="h-7 w-7 text-[hsl(var(--danger-500))]" onClick={clearCollectedData} title="清空数据"><Trash2 className="w-4 h-4" /></Button>
              <Button variant="outline" size="icon" className="h-7 w-7" onClick={handleDownloadCSV} title="下载预览数据(最多20条)"><Download className="w-4 h-4" /></Button>
              <Button
                variant="success"
                size="sm"
                className="h-7 text-xs"
                onClick={handleDownloadFullData}
                disabled={downloading || !currentExecutionWorkflowId}
                title="下载本次执行收集到的完整数据（不受20条限制）"
              >
                <FileDown className="w-3.5 h-3.5 mr-1" />
                {downloading ? '下载中...' : '下载数据'}
              </Button>
            </>
          )}
          {activeTab === 'variables' && (
            <>
              {isAddingVar ? (
                <div className="flex items-center gap-1">
                  <Input value={newVarName} onChange={(e) => setNewVarName(e.target.value)}
                    placeholder="变量名" className="w-20 h-7 text-xs" />
                  <Select 
                    value={newVarType} 
                    onChange={(e) => setNewVarType(e.target.value as VariableType)}
                    className="w-16 h-7 text-xs"
                  >
                    <option value="string">字符串</option>
                    <option value="number">数字</option>
                    <option value="boolean">布尔</option>
                    <option value="array">列表</option>
                    <option value="object">字典</option>
                  </Select>
                  {newVarType === 'boolean' ? (
                    <Select 
                      value={newVarValue || 'false'} 
                      onChange={(e) => setNewVarValue(e.target.value)}
                      className="w-16 h-7 text-xs"
                    >
                      <option value="true">true</option>
                      <option value="false">false</option>
                    </Select>
                  ) : (
                    <Input value={newVarValue} onChange={(e) => setNewVarValue(e.target.value)}
                      placeholder={newVarType === 'number' ? '0' : newVarType === 'array' ? '[]' : newVarType === 'object' ? '{}' : '值'} 
                      className="w-20 h-7 text-xs" 
                      onKeyDown={(e) => e.key === 'Enter' && handleAddVariable()} />
                  )}
                  <Button size="icon" variant="outline" className="h-7 w-7" onClick={handleAddVariable}><Check className="w-3.5 h-3.5" /></Button>
                  <Button size="icon" variant="outline" className="h-7 w-7" onClick={() => setIsAddingVar(false)}><X className="w-3.5 h-3.5" /></Button>
                </div>
              ) : (
                <Button variant="default" size="sm" className="h-7 text-xs" onClick={() => setIsAddingVar(true)}>
                  <Plus className="w-3.5 h-3.5 mr-1" />添加变量
                </Button>
              )}
            </>
          )}
          {activeTab === 'assets' && (
            <Button 
              variant="success" 
              size="sm" 
              className="h-7 text-xs" 
              onClick={() => {
                // 调用ExcelAssetsPanel的上传函数
                if ((window as any).__excelUploadTrigger) {
                  (window as any).__excelUploadTrigger()
                }
              }}
            >
              <Upload className="w-3.5 h-3.5 mr-1" />
              上传Excel
            </Button>
          )}
          {activeTab === 'images' && (
            <Button 
              variant="warning" 
              size="sm" 
              className="h-7 text-xs" 
              onClick={() => {
                // 调用ImageAssetsPanel的上传函数
                if ((window as any).__imageUploadTrigger) {
                  (window as any).__imageUploadTrigger()
                }
              }}
            >
              <Upload className="w-3.5 h-3.5 mr-1" />
              上传图像
            </Button>
          )}
          <Button variant="outline" size="icon" className="h-7 w-7" onClick={() => setIsCollapsed(!isCollapsed)} title={isCollapsed ? '展开' : '收起'}>
            {isCollapsed ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </Button>
        </div>
      </div>

      {!isCollapsed && (
        <div className="h-[calc(100%-2.5rem)] animate-fade-in">
          {activeTab === 'logs' && (
            <div className="h-full flex flex-col">
              {/* 日志搜索和筛选栏 */}
              <div className="flex items-center gap-2 px-2 py-1.5 border-b bg-muted/30">
                <div className="relative flex-1 max-w-xs group">
                  <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground group-focus-within:text-blue-500 transition-colors" />
                  <Input
                    value={logSearchQuery}
                    onChange={(e) => setLogSearchQuery(e.target.value)}
                    placeholder="搜索日志..."
                    className="pl-7 h-7 text-xs"
                  />
                  {logSearchQuery && (
                    <button
                      className="absolute right-2 top-1/2 -translate-y-1/2 p-0.5 rounded-full hover:bg-blue-100 text-muted-foreground hover:text-blue-600 transition-all"
                      onClick={() => setLogSearchQuery('')}
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
                <div className="relative flex items-center gap-1">
                  <Filter className="w-3.5 h-3.5 text-blue-500" />
                  <button
                    onClick={() => setShowFilterDropdown(!showFilterDropdown)}
                    className="h-7 px-2 text-xs border rounded hover:bg-gray-50 transition-colors flex items-center gap-1"
                  >
                    <span>筛选 ({logLevelFilters.size})</span>
                    <ChevronDown className="w-3 h-3" />
                  </button>
                  {showFilterDropdown && (
                    <>
                      <div 
                        className="fixed inset-0 z-40" 
                        onClick={() => setShowFilterDropdown(false)}
                      />
                      <div className="absolute top-full left-0 mt-1 bg-white border rounded-lg shadow-lg p-2 z-50 min-w-[140px]">
                        <div className="space-y-1">
                          <label className="flex items-center gap-2 px-2 py-1 hover:bg-gray-50 rounded cursor-pointer text-xs">
                            <input
                              type="checkbox"
                              checked={logLevelFilters.size === 5}
                              onChange={toggleAllFilters}
                              className="rounded"
                            />
                            <span className="font-medium">全选/取消</span>
                          </label>
                          <div className="border-t my-1" />
                          <label className="flex items-center gap-2 px-2 py-1 hover:bg-gray-50 rounded cursor-pointer text-xs">
                            <input
                              type="checkbox"
                              checked={logLevelFilters.has('debug')}
                              onChange={() => toggleLogLevelFilter('debug')}
                              className="rounded"
                            />
                            <span className="text-gray-600">调试</span>
                          </label>
                          <label className="flex items-center gap-2 px-2 py-1 hover:bg-gray-50 rounded cursor-pointer text-xs">
                            <input
                              type="checkbox"
                              checked={logLevelFilters.has('info')}
                              onChange={() => toggleLogLevelFilter('info')}
                              className="rounded"
                            />
                            <span className="text-blue-600">ℹ️ 信息</span>
                          </label>
                          <label className="flex items-center gap-2 px-2 py-1 hover:bg-gray-50 rounded cursor-pointer text-xs">
                            <input
                              type="checkbox"
                              checked={logLevelFilters.has('success')}
                              onChange={() => toggleLogLevelFilter('success')}
                              className="rounded"
                            />
                            <span className="text-green-600">✓ 成功</span>
                          </label>
                          <label className="flex items-center gap-2 px-2 py-1 hover:bg-gray-50 rounded cursor-pointer text-xs">
                            <input
                              type="checkbox"
                              checked={logLevelFilters.has('warning')}
                              onChange={() => toggleLogLevelFilter('warning')}
                              className="rounded"
                            />
                            <span className="text-yellow-600">警告</span>
                          </label>
                          <label className="flex items-center gap-2 px-2 py-1 hover:bg-gray-50 rounded cursor-pointer text-xs">
                            <input
                              type="checkbox"
                              checked={logLevelFilters.has('error')}
                              onChange={() => toggleLogLevelFilter('error')}
                              className="rounded"
                            />
                            <span className="text-red-600">✕ 错误</span>
                          </label>
                        </div>
                      </div>
                    </>
                  )}
                </div>
                <div className="flex items-center gap-1">
                  <span className="text-xs text-muted-foreground">显示</span>
                  <Select
                    value={String(maxLogCount)}
                    onChange={(e) => setMaxLogCount(Number(e.target.value))}
                    className="h-7 text-xs w-20"
                  >
                    <option value="100">100条</option>
                    <option value="200">200条</option>
                    <option value="300">300条</option>
                    <option value="400">400条</option>
                    <option value="500">500条</option>
                  </Select>
                </div>
                <span className="text-xs text-blue-600 font-medium">
                  {filteredLogs.length}/{logs.length}
                </span>
                
                {/* 日志延迟提示 */}
                <div className="flex items-center gap-1 px-2 py-1 bg-amber-50 border border-amber-200 rounded-md ml-auto">
                  <svg className="w-3.5 h-3.5 text-amber-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span className="text-xs text-amber-700 whitespace-nowrap">
                    日志展示有一定的延迟，建议添加"提示音"模块以判断流程是否执行完毕
                  </span>
                </div>
              </div>
              
              {filteredLogs.length === 0 ? (
                <div className="flex-1 flex flex-col items-center justify-center animate-fade-in">
                  {logs.length === 0 ? (
                    <>
                      <div className="w-16 h-16 rounded-full bg-[hsl(var(--muted))] flex items-center justify-center mb-3">
                        <FileText className="w-8 h-8 text-[hsl(var(--muted-foreground))]" />
                      </div>
                      <p className="text-sm text-muted-foreground">暂无日志</p>
                      <p className="text-xs text-muted-foreground/70 mt-2 text-center px-4">
                        提示：默认只显示"打印日志"模块的内容，开启"详细日志"可查看所有模块执行日志
                      </p>
                    </>
                  ) : (
                    <>
                      <div className="w-16 h-16 rounded-full bg-[hsl(var(--muted))] flex items-center justify-center mb-3">
                        <Search className="w-8 h-8 text-[hsl(var(--muted-foreground))]" />
                      </div>
                      <p className="text-sm text-muted-foreground">未找到匹配的日志</p>
                      <p className="text-xs text-muted-foreground mt-1">试试其他关键词或筛选条件</p>
                    </>
                  )}
                </div>
              ) : (
                <LogList
                  logs={filteredLogs}
                  searchQuery={logSearchQuery}
                  onLogClick={handleLogClick}
                />
              )}
            </div>
          )}

          {activeTab === 'data' && (
            <div className="h-full flex flex-col">
              {collectedData.length === 0 && columns.length === 0 ? (
                <div className="flex-1 flex flex-col items-center justify-center text-muted-foreground animate-fade-in">
                  <div className="w-16 h-16 rounded-full bg-[hsl(var(--muted))] flex items-center justify-center mb-3">
                    <FileSpreadsheet className="w-8 h-8 text-[hsl(var(--muted-foreground))]" />
                  </div>
                  <p className="text-sm">暂无数据</p>
                  <p className="text-xs mt-1">执行工作流后，收集的数据将显示在这里</p>
                  <p className="text-xs text-muted-foreground/70 mt-2 text-center px-4">
                    此处最多实时预览20条数据，完整数据请点击"下载数据"按钮或使用"导出数据表"模块导出
                  </p>
                </div>
              ) : (
                <DataTable
                  data={collectedData}
                  columns={columns}
                  onEdit={(rowIndex, col, value) => {
                    updateDataRow(rowIndex, { ...collectedData[rowIndex], [col]: value })
                  }}
                  onDeleteRow={(rowIndex) => deleteDataRow(rowIndex)}
                  onDeleteColumn={(col) => handleDeleteColumn(col)}
                />
              )}
            </div>
          )}

          {activeTab === 'variables' && (
            <ScrollArea className="h-full p-2">
              {variables.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-muted-foreground animate-fade-in">
                  <div className="w-16 h-16 rounded-full bg-[hsl(var(--muted))] flex items-center justify-center mb-3">
                    <Variable className="w-8 h-8 text-[hsl(var(--muted-foreground))]" />
                  </div>
                  <p className="text-sm">暂无全局变量</p>
                  <p className="text-xs mt-1">点击"添加变量"创建全局变量</p>
                  <p className="text-[10px] mt-2 text-center opacity-70">
                    引用语法：{'{变量名}'} · {'{列表[0]}'} · {'{列表[-1]}'} · {'{字典[键名]}'}
                  </p>
                </div>
              ) : (
                <div className="flex flex-col h-full">
                  <div className="overflow-x-auto flex-1">
                    <table className="w-full border-collapse text-xs">
                      <thead>
                        <tr className="bg-muted/50">
                          <th className="border px-2 py-1.5 text-left font-medium w-32">变量名</th>
                          <th className="border px-2 py-1.5 text-left font-medium">值</th>
                          <th className="border px-2 py-1.5 text-left font-medium w-20">类型</th>
                          <th className="border px-2 py-1.5 w-12">操作</th>
                        </tr>
                      </thead>
                      <tbody>
                        {variables.map((v) => (
                          <tr key={v.name} className="hover:bg-muted/30">
                            <td className="border px-2 py-1 cursor-pointer hover:bg-muted/50" onClick={() => startEditVarName(v.name)}>
                              {editingVarName === v.name ? (
                                <Input 
                                  value={editVarNameValue} 
                                  onChange={(e) => setEditVarNameValue(e.target.value.replace(/[^a-zA-Z0-9_\u4e00-\u9fa5]/g, ''))} 
                                  className="h-6 text-xs font-mono" 
                                  autoFocus
                                  onKeyDown={(e) => { 
                                    if (e.key === 'Enter') saveEditVarName(); 
                                    if (e.key === 'Escape') setEditingVarName(null); 
                                  }} 
                                  onBlur={saveEditVarName} 
                                />
                              ) : (
                                <div className="flex items-center justify-between group">
                                  <span className="font-mono text-blue-600">{v.name}</span>
                                  <Edit2 className="w-3 h-3 opacity-0 group-hover:opacity-50" />
                                </div>
                              )}
                            </td>
                            <td className="border px-2 py-1 cursor-pointer hover:bg-muted/50" onClick={() => startEditVar(v.name, v.value, v.type)}>
                              {editingVar === v.name ? (
                                <Input value={editVarValue} onChange={(e) => setEditVarValue(e.target.value)} className="h-6 text-xs" autoFocus
                                  onKeyDown={(e) => { if (e.key === 'Enter') saveEditVar(); if (e.key === 'Escape') setEditingVar(null); }} onBlur={saveEditVar} />
                              ) : (
                                <div className="flex items-center justify-between group">
                                  <span className="truncate max-w-[200px]" title={formatVariableValue(v.value, v.type)}>{formatVariableValue(v.value, v.type)}</span>
                                  <Edit2 className="w-3 h-3 opacity-0 group-hover:opacity-50" />
                                </div>
                              )}
                            </td>
                            <td className="border px-2 py-1 text-muted-foreground">{v.type}</td>
                            <td className="border px-2 py-1 text-center">
                              <Button variant="ghost" size="icon" className="w-5 h-5" onClick={() => deleteVariable(v.name)}>
                                <Trash2 className="w-3 h-3 text-destructive" />
                              </Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <div className="pt-2 border-t mt-2 text-[10px] text-muted-foreground">
                    <span className="font-medium">引用语法：</span>
                    {'{变量名}'} · {'{列表[0]}'} · {'{列表[-1]}'} · {'{字典[键名]}'} · {'{数据[0][name]}'}
                  </div>
                </div>
              )}
            </ScrollArea>
          )}

          {activeTab === 'assets' && <ExcelAssetsPanel />}

          {activeTab === 'images' && <ImageAssetsPanel />}
        </div>
      )}

      {/* 变量重命名确认弹窗 */}
      {renameDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl w-[420px] mx-4 overflow-hidden animate-in fade-in zoom-in-95 duration-200">
            <div className="bg-[hsl(var(--card))] h-1.5" />
            <div className="p-6">
              <div className="flex items-center gap-3 mb-5">
                <div className="bg-[hsl(var(--card))] w-10 h-10 rounded-xl flex items-center justify-center shadow-lg">
                  <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">变量重命名</h3>
                  <p className="text-xs text-gray-500">检测到变量引用需要更新</p>
                </div>
              </div>
              <div className="bg-[hsl(var(--card))] rounded-xl p-4 mb-5">
                <div className="flex items-center justify-center gap-3">
                  <div className="flex items-center gap-2 px-3 py-2 bg-white rounded-lg shadow-sm border border-gray-200">
                    <span className="text-xs text-gray-500">原名</span>
                    <code className="text-sm font-mono font-semibold text-red-600">{'{' + renameDialog.oldName + '}'}</code>
                  </div>
                  <div className="bg-[hsl(var(--card))] flex items-center justify-center w-8 h-8 rounded-full shadow-md">
                    <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                    </svg>
                  </div>
                  <div className="flex items-center gap-2 px-3 py-2 bg-white rounded-lg shadow-sm border border-gray-200">
                    <span className="text-xs text-gray-500">新名</span>
                    <code className="text-sm font-mono font-semibold text-emerald-600">{'{' + renameDialog.newName + '}'}</code>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2 px-4 py-3 bg-amber-50 border border-amber-200 rounded-xl mb-6">
                <svg className="w-5 h-5 text-amber-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="text-sm text-amber-800">
                  发现 <span className="font-bold text-amber-900">{renameDialog.usageCount}</span> 处引用了此变量
                </p>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={handleCancelRename}
                  className="flex-1 px-4 py-2.5 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-xl transition-all duration-200 hover:shadow-md active:scale-[0.98]"
                >
                  仅改名称
                </button>
                <button
                  onClick={handleConfirmRename}
                  className="bg-[hsl(var(--brand-600))] flex-1 px-4 py-2.5 text-sm font-medium text-white rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl active:scale-[0.98]"
                >
                  全部更新
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* 确认对话框 */}
      <ConfirmDialog />
    </motion.footer>
  )
}
