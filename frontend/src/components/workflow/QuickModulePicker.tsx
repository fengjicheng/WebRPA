import { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Search, Star } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useModuleStatsStore } from '@/store/moduleStatsStore'
import { pinyinMatch } from '@/lib/pinyin'
import { dialogVariants, overlayVariants, listItemVariants, spring } from '@/lib/motion'
import type { ModuleType } from '@/types'

interface QuickModulePickerProps {
  isOpen: boolean
  position: { x: number; y: number }
  onClose: () => void
  onSelectModule: (moduleType: ModuleType, customModuleId?: string) => void
  availableModules: Array<{
    type: ModuleType
    label: string
    category: string
    icon: React.ElementType
    isCustom?: boolean
    customModuleId?: string
  }>
  favoritesOnly?: boolean
}

export function QuickModulePicker({
  isOpen,
  position,
  onClose,
  onSelectModule,
  availableModules,
  favoritesOnly = false,
}: QuickModulePickerProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const { getStats, toggleFavorite, getSortedModules, stats } = useModuleStatsStore()

  const [sortedModulesCache] = useState(() => {
    const grouped = availableModules.reduce((acc, module) => {
      if (!acc[module.category]) acc[module.category] = []
      acc[module.category].push(module)
      return acc
    }, {} as Record<string, typeof availableModules>)
    Object.keys(grouped).forEach((category) => {
      const moduleTypes = grouped[category].map((m) => m.type)
      const sorted = getSortedModules(moduleTypes)
      grouped[category] = sorted.map((type) => grouped[category].find((m) => m.type === type)!)
    })
    return grouped
  })

  const filteredModules = useMemo(() => {
    let grouped = { ...sortedModulesCache }
    if (favoritesOnly) {
      Object.keys(grouped).forEach((category) => {
        grouped[category] = grouped[category].filter((m) => getStats(m.type).isFavorite)
      })
      Object.keys(grouped).forEach((category) => {
        if (grouped[category].length === 0) delete grouped[category]
      })
    }
    if (searchTerm) {
      const term = searchTerm.trim()
      Object.keys(grouped).forEach((category) => {
        grouped[category] = grouped[category].filter((m) =>
          pinyinMatch(m.label, term) || pinyinMatch(m.category, term) || m.type.toLowerCase().includes(term.toLowerCase())
        )
      })
      Object.keys(grouped).forEach((category) => {
        if (grouped[category].length === 0) delete grouped[category]
      })
    }
    return grouped
  }, [searchTerm, sortedModulesCache, favoritesOnly, getStats, stats])

  const handleModuleClick = (module: typeof availableModules[0]) => {
    if (module.isCustom && module.customModuleId) {
      onSelectModule('custom_module' as ModuleType, module.customModuleId)
    } else {
      onSelectModule(module.type)
    }
    onClose()
  }

  const handleToggleFavorite = (e: React.MouseEvent, moduleType: ModuleType) => {
    e.stopPropagation()
    toggleFavorite(moduleType)
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* 背景遮罩 */}
          <motion.div
            key="overlay"
            variants={overlayVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="fixed inset-0 bg-black/20 z-40"
            onClick={onClose}
          />

          {/* 弹窗 */}
          <motion.div
            key="picker"
            variants={dialogVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="fixed z-50 bg-white rounded-xl shadow-2xl border border-gray-200 w-[500px] max-h-[600px] flex flex-col overflow-hidden"
            style={{
              left: `${position.x}px`,
              top: `${position.y}px`,
              transform: 'translate(-50%, -50%)',
            }}
          >
            {/* 头部 */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-cyan-50">
              <h3 className="font-semibold text-gray-900">
                {favoritesOnly ? '收藏的模块' : '快速选择模块'}
              </h3>
              <motion.button
                onClick={onClose}
                className="p-1.5 hover:bg-white/80 rounded-lg transition-colors"
                whileHover={{ scale: 1.15, rotate: 90 }}
                whileTap={{ scale: 0.9 }}
                transition={spring.snappy}
              >
                <X className="w-4 h-4 text-gray-500" />
              </motion.button>
            </div>

            {/* 搜索框 */}
            <div className="p-3 border-b border-gray-200 bg-gray-50">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="搜索模块（支持拼音）..."
                  className="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-shadow"
                  autoFocus
                />
              </div>
            </div>

            {/* 模块列表 */}
            <div className="flex-1 overflow-y-auto p-3 space-y-4">
              {Object.keys(filteredModules).length === 0 ? (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="text-center py-8 text-gray-500 text-sm"
                >
                  {favoritesOnly ? (
                    <div className="space-y-2">
                      <div>暂无收藏的模块</div>
                      <div className="text-xs">点击模块右侧的 <Star className="w-3 h-3 inline" /> 图标可收藏</div>
                    </div>
                  ) : '无搜索结果'}
                </motion.div>
              ) : (
                Object.entries(filteredModules).map(([category, modules]) => (
                  <div key={category}>
                    <motion.div
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.2 }}
                      className="text-xs font-semibold text-gray-500 mb-2 px-2 uppercase tracking-wide"
                    >
                      {category}
                    </motion.div>
                    <div className="space-y-0.5">
                      {modules.map((module, i) => {
                        const moduleStats = getStats(module.type)
                        const Icon = module.icon
                        return (
                          <motion.button
                            key={module.type}
                            custom={i}
                            variants={listItemVariants}
                            initial="hidden"
                            animate="visible"
                            onClick={() => handleModuleClick(module)}
                            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-blue-50 transition-colors text-left group"
                            whileHover={{ x: 4, backgroundColor: 'rgb(239 246 255)' }}
                            whileTap={{ scale: 0.98 }}
                            transition={spring.snappy}
                          >
                            <motion.div
                              whileHover={{ rotate: [0, -15, 15, 0], transition: { duration: 0.35 } }}
                            >
                              <Icon className="w-4 h-4 text-gray-600 flex-shrink-0" />
                            </motion.div>
                            <div className="flex-1 min-w-0">
                              <div className="text-sm font-medium text-gray-900 truncate">{module.label}</div>
                            </div>
                            <motion.button
                              onClick={(e) => handleToggleFavorite(e, module.type)}
                              className={cn(
                                'p-1 rounded transition-colors flex-shrink-0',
                                moduleStats.isFavorite ? 'text-yellow-500' : 'text-gray-300 opacity-0 group-hover:opacity-100'
                              )}
                              whileHover={{ scale: 1.3, rotate: 15 }}
                              whileTap={{ scale: 0.8 }}
                              transition={spring.snappy}
                            >
                              <Star className={cn('w-4 h-4', moduleStats.isFavorite && 'fill-current')} />
                            </motion.button>
                          </motion.button>
                        )
                      })}
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* 底部提示 */}
            <div className="p-3 border-t border-gray-200 bg-gray-50 text-xs text-gray-500 text-center">
              {favoritesOnly
                ? '双击画布空白区域快速创建收藏的模块 · 右键显示所有模块'
                : '右键画布空白区域可快速打开此面板'}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
