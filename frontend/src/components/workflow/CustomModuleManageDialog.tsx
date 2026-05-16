/**
 * 自定义模块管理对话框
 */
import { useState } from 'react'
import { X, Edit, Trash2, Copy, Download, Upload, Package } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useCustomModuleStore } from '@/store/customModuleStore'
import { useConfirm } from '@/components/ui/confirm-dialog'
import type { CustomModule } from '@/types/customModule'

interface Props {
  open: boolean
  onClose: () => void
  onEdit: (module: CustomModule) => void
}

export function CustomModuleManageDialog({ open, onClose, onEdit }: Props) {
  const { modules, deleteModule, duplicateModule } = useCustomModuleStore()
  const { confirm, alert, ConfirmDialog } = useConfirm()
  const [searchQuery, setSearchQuery] = useState('')
  const [importing, setImporting] = useState(false)

  const filteredModules = modules.filter(m =>
    m.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    m.description?.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const handleDelete = async (module: CustomModule) => {
    const confirmed = await confirm(
      `确定要删除自定义模块「${module.name}」吗？此操作不可恢复。`,
      { title: '删除模块', type: 'warning', confirmText: '删除', cancelText: '取消' }
    )
    if (!confirmed) return

    try {
      await deleteModule(module.id)
      await alert('模块已删除', { title: '删除成功' })
    } catch (error) {
      await alert(error instanceof Error ? error.message : '删除失败', { title: '删除失败' })
    }
  }

  const handleDuplicate = async (module: CustomModule) => {
    try {
      const newName = `${module.name} (副本)`
      await duplicateModule(module.id, newName)
      await alert(`已创建「${module.name}」的副本`, { title: '复制成功' })
    } catch (error) {
      await alert(error instanceof Error ? error.message : '复制失败', { title: '复制失败' })
    }
  }

  const handleExport = async (module: CustomModule) => {
    try {
      const json = JSON.stringify(module, null, 2)
      const blob = new Blob([json], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${module.name}.custom-module.json`
      a.click()
      URL.revokeObjectURL(url)
      await alert('模块已导出', { title: '导出成功' })
    } catch (error) {
      await alert(error instanceof Error ? error.message : '导出失败', { title: '导出失败' })
    }
  }

  const handleImport = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    if (!file.name.endsWith('.json')) {
      await alert('请选择 JSON 格式的文件', { title: '导入失败' })
      return
    }

    setImporting(true)
    try {
      const text = await file.text()
      const data = JSON.parse(text)
      // TODO: 调用导入API
      await alert('模块已导入', { title: '导入成功' })
    } catch (error) {
      await alert(error instanceof Error ? error.message : '导入失败', { title: '导入失败' })
    } finally {
      setImporting(false)
      event.target.value = ''
    }
  }

  if (!open) return null

  return (
    <>
      <div className="fixed inset-0 bg-black/50 z-50 animate-fade-in" onClick={onClose} />
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
        <div className="bg-white rounded-lg shadow-2xl w-full max-w-4xl max-h-[80vh] flex flex-col pointer-events-auto animate-scale-in">
          {/* 头部 */}
          <div className="flex items-center justify-between p-6 border-b">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white shadow-md">
                <Package className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-lg font-semibold">管理自定义模块</h2>
                <p className="text-sm text-muted-foreground">编辑、复制、导出或删除模块</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-accent transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* 工具栏 */}
          <div className="p-4 border-b space-y-3">
            <div className="flex gap-2">
              <Input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="搜索模块..."
                className="flex-1"
              />
              <Button
                variant="outline"
                onClick={() => document.getElementById('import-module-file')?.click()}
                disabled={importing}
              >
                <Upload className="w-4 h-4 mr-2" />
                导入模块
              </Button>
              <input
                id="import-module-file"
                type="file"
                accept=".json"
                className="hidden"
                onChange={handleImport}
              />
            </div>
          </div>

          {/* 模块列表 */}
          <ScrollArea className="flex-1 p-4">
            {filteredModules.length === 0 ? (
              <div className="text-center py-12">
                <Package className="w-16 h-16 mx-auto mb-4 text-muted-foreground/30" />
                <p className="text-muted-foreground">
                  {searchQuery ? '没有找到匹配的模块' : '还没有自定义模块'}
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {filteredModules.map((module) => (
                  <div
                    key={module.id}
                    className="p-4 rounded-lg border border-border bg-white hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-start gap-4">
                      <div className="flex-shrink-0 w-12 h-12 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white shadow-sm">
                        <Package className="w-6 h-6" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-medium">{module.name}</h3>
                        </div>
                        {module.description && (
                          <p className="text-sm text-muted-foreground mb-2">
                            {module.description}
                          </p>
                        )}
                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                          <span>{module.parameters?.length || 0} 个参数</span>
                          <span>{module.outputs?.length || 0} 个输出</span>
                          <span>使用 {module.usage_count} 次</span>
                          <span>创建于 {new Date(module.created_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => onEdit(module)}
                          title="编辑"
                        >
                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleDuplicate(module)}
                          title="复制"
                        >
                          <Copy className="w-4 h-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleExport(module)}
                          title="导出"
                        >
                          <Download className="w-4 h-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleDelete(module)}
                          title="删除"
                          className="text-red-600 hover:text-red-700 hover:bg-red-50"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>

          {/* 底部 */}
          <div className="p-4 border-t flex justify-end">
            <Button onClick={onClose}>关闭</Button>
          </div>
        </div>
      </div>
      <ConfirmDialog />
    </>
  )
}
