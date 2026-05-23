import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { X, Code2, FileJson, FileText, Download, CheckCircle2, Sparkles } from 'lucide-react'
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
    description: '导出为可独立运行的 Playwright Python 自动化脚本',
    badge: '推荐',
    Icon: Code2,
    accent: 'success',
  },
  {
    id: 'json' as ExportFormat,
    name: 'JSON 格式',
    description: '导出为 JSON 文件，包含完整的工作流配置数据',
    badge: '通用',
    Icon: FileJson,
    accent: 'brand',
  },
  {
    id: 'markdown' as ExportFormat,
    name: 'Markdown 文档',
    description: '导出为 Markdown 文档，便于阅读、分享和归档',
    badge: '可读性',
    Icon: FileText,
    accent: 'violet',
  },
] as const

const accentMap = {
  success: {
    iconChip: 'icon-chip icon-chip-success',
    activeBg: 'bg-[hsl(var(--success-50))]',
    activeBorder: 'border-[hsl(var(--success-500))]',
    activeRing: 'shadow-success-glow',
    activeText: 'text-[hsl(var(--success-700))]',
    badge: 'badge-success',
    btnVariant: 'success' as const,
  },
  brand: {
    iconChip: 'icon-chip icon-chip-brand',
    activeBg: 'bg-[hsl(var(--brand-50))]',
    activeBorder: 'border-[hsl(var(--brand-500))]',
    activeRing: 'shadow-brand-glow',
    activeText: 'text-[hsl(var(--brand-700))]',
    badge: 'badge-brand',
    btnVariant: 'default' as const,
  },
  violet: {
    iconChip: 'icon-chip icon-chip-violet',
    activeBg: 'bg-[hsl(var(--violet-50))]',
    activeBorder: 'border-[hsl(var(--violet-500))]',
    activeRing: 'shadow-pop',
    activeText: 'text-[hsl(var(--violet-700))]',
    badge: '!bg-[hsl(var(--violet-50))] !text-[hsl(var(--violet-700))] !border-[hsl(var(--violet-500)/0.3)]',
    btnVariant: 'default' as const,
  },
} as const

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
        className="fixed inset-0 z-50 bg-[hsl(217_45%_15%_/_0.55)] backdrop-blur-[3px] flex items-center justify-center p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.92, y: 12 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 8 }}
          transition={{ type: 'spring', stiffness: 380, damping: 28 }}
          className="modern-dialog w-full max-w-xl"
          onClick={(e) => e.stopPropagation()}
        >
          {/* 标题栏 */}
          <div className="modern-dialog-header">
            <div className="modern-dialog-header-icon modern-dialog-header-icon-success">
              <Download className="w-5 h-5" strokeWidth={2.2} />
            </div>
            <div className="flex-1">
              <h2 className="modern-dialog-title">导出工作流</h2>
              <div className="modern-dialog-subtitle">选择最合适的格式分享或备份</div>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 rounded-[7px] text-[hsl(var(--slate-500))] hover:bg-[hsl(var(--danger-50))] hover:text-[hsl(var(--danger-600))] hover:border-[hsl(var(--danger-500)/0.3)] border border-transparent transition-all duration-150 active:scale-90"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* 内容区 */}
          <div className="px-5 py-4">
            <div className="space-y-2">
              {exportFormats.map((format, idx) => {
                const isSelected = selectedFormat === format.id
                const accent = accentMap[format.accent]
                const Icon = format.Icon

                return (
                  <motion.button
                    key={format.id}
                    onClick={() => setSelectedFormat(format.id)}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.06 }}
                    className={cn(
                      'w-full p-3.5 rounded-[12px] border-[1.5px] transition-all duration-200 ease-[cubic-bezier(0.25,1,0.5,1)] text-left flex items-start gap-3.5',
                      isSelected
                        ? `${accent.activeBg} ${accent.activeBorder} ${accent.activeRing}`
                        : 'bg-[hsl(var(--card))] border-[hsl(var(--border))] hover:border-[hsl(var(--brand-500)/0.4)] hover:bg-[hsl(var(--brand-50)/0.4)] hover:shadow-soft hover:translate-x-1'
                    )}
                    whileHover={{ scale: 1.005 }}
                    whileTap={{ scale: 0.99 }}
                  >
                    <div className={cn(accent.iconChip, '!w-10 !h-10 !rounded-[10px]')}>
                      <Icon className="w-4.5 h-4.5" strokeWidth={2.2} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className={cn('text-[14px] font-bold', isSelected ? accent.activeText : 'text-[hsl(var(--slate-900))]')}>
                          {format.name}
                        </h3>
                        <span className={cn('badge', accent.badge)}>
                          {format.badge}
                        </span>
                        {isSelected && (
                          <CheckCircle2 className={cn('w-4 h-4 ml-auto animate-scale-in', accent.activeText)} strokeWidth={2.4} />
                        )}
                      </div>
                      <p className="text-[12px] text-[hsl(var(--muted-foreground))] leading-relaxed">
                        {format.description}
                      </p>
                    </div>
                  </motion.button>
                )
              })}
            </div>

            <div className="status-row status-row-info mt-4 !py-2">
              <Sparkles className="w-3 h-3" />
              <span className="text-[11px]">提示：导出后可重新通过工作流仓库或本地文件再次打开</span>
            </div>
          </div>

          {/* 底部按钮 */}
          <div className="dialog-footer-bar">
            <Button variant="secondary" size="sm" onClick={onClose} disabled={exporting}>
              取消
            </Button>
            <Button
              onClick={handleExport}
              disabled={exporting}
              loading={exporting}
              size="sm"
              variant="success"
            >
              {!exporting && <Download className="w-3.5 h-3.5" />}
              {exporting ? '导出中...' : '立即导出'}
            </Button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}
