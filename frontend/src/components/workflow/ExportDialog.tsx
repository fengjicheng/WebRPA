import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { X, Code, FileJson, FileText, Download, CheckCircle2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ExportDialogProps {
  isOpen: boolean
  onClose: () => void
  onExport: (format: ExportFormat) => Promise<void>
}

export type ExportFormat = 'playwright' | 'json' | 'markdown'

const exportFormats = [
  {
    id: 'playwright' as ExportFormat,
    name: 'Playwright Python',
    description: '导出为可独立运行的 Playwright Python 脚本',
    icon: Code,
    color: 'text-green-600',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    hoverBg: 'hover:bg-green-100',
  },
  {
    id: 'json' as ExportFormat,
    name: 'JSON 格式',
    description: '导出为 JSON 文件，包含完整的工作流配置',
    icon: FileJson,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    hoverBg: 'hover:bg-blue-100',
  },
  {
    id: 'markdown' as ExportFormat,
    name: 'Markdown 文档',
    description: '导出为 Markdown 文档，便于阅读和分享',
    icon: FileText,
    color: 'text-purple-600',
    bgColor: 'bg-purple-50',
    borderColor: 'border-purple-200',
    hoverBg: 'hover:bg-purple-100',
  },
]

export function ExportDialog({ isOpen, onClose, onExport }: ExportDialogProps) {
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat>('playwright')
  const [exporting, setExporting] = useState(false)

  const handleExport = async () => {
    setExporting(true)
    try {
      await onExport(selectedFormat)
      onClose()
    } catch (error) {
      console.error('导出失败:', error)
    } finally {
      setExporting(false)
    }
  }

  if (!isOpen) return null

  return (
    <AnimatePresence>
      <motion.div
        key="export-overlay"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.2 }}
        className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.92, y: 12 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 8 }}
          transition={{ type: 'spring', stiffness: 380, damping: 28 }}
          className="bg-white text-black rounded-xl shadow-2xl w-full max-w-2xl overflow-hidden"
          onClick={(e) => e.stopPropagation()}
        >
          {/* 标题栏 */}
          <div className="flex items-center justify-between px-6 py-4 border-b">
            <div className="flex items-center gap-2">
              <Download className="w-5 h-5 text-green-600" />
              <h2 className="text-xl font-semibold">导出工作流</h2>
            </div>
            <Button variant="outline" size="icon" onClick={onClose} className="hover:bg-gray-100">
              <X className="w-5 h-5 text-gray-500" />
            </Button>
          </div>

          {/* 内容区 */}
          <div className="p-6">
            <p className="text-sm text-gray-600 mb-4">
              选择导出格式，将工作流导出为不同的文件类型
            </p>

            {/* 格式选择 */}
            <div className="space-y-3">
              {exportFormats.map((format) => {
                const Icon = format.icon
                const isSelected = selectedFormat === format.id

                return (
                  <motion.button
                    key={format.id}
                    onClick={() => setSelectedFormat(format.id)}
                    className={cn(
                      'w-full p-4 rounded-lg border-2 transition-all duration-200 text-left',
                      'flex items-start gap-4',
                      isSelected
                        ? `${format.bgColor} ${format.borderColor} shadow-md`
                        : 'bg-white border-gray-200 hover:border-gray-300 hover:shadow-sm'
                    )}
                    whileHover={{ scale: 1.01 }}
                    whileTap={{ scale: 0.99 }}
                  >
                    {/* 图标 */}
                    <div
                      className={cn(
                        'p-3 rounded-lg',
                        isSelected ? format.bgColor : 'bg-gray-50'
                      )}
                    >
                      <Icon className={cn('w-6 h-6', isSelected ? format.color : 'text-gray-400')} />
                    </div>

                    {/* 文本内容 */}
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className={cn('font-medium', isSelected ? format.color : 'text-gray-900')}>
                          {format.name}
                        </h3>
                        {isSelected && (
                          <CheckCircle2 className={cn('w-4 h-4', format.color)} />
                        )}
                      </div>
                      <p className="text-sm text-gray-600">{format.description}</p>
                    </div>
                  </motion.button>
                )
              })}
            </div>
          </div>

          {/* 底部按钮 */}
          <div className="flex items-center justify-end gap-3 px-6 py-4 border-t bg-gray-50">
            <Button variant="outline" onClick={onClose} disabled={exporting}>
              取消
            </Button>
            <Button
              onClick={handleExport}
              disabled={exporting}
              className="bg-green-600 hover:bg-green-700 text-white"
            >
              {exporting ? (
                <>
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                    className="w-4 h-4 border-2 border-white border-t-transparent rounded-full mr-2"
                  />
                  导出中...
                </>
              ) : (
                <>
                  <Download className="w-4 h-4 mr-2" />
                  导出
                </>
              )}
            </Button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}
