import { memo } from 'react'
import { motion } from 'framer-motion'
import { Handle, Position, type NodeProps, useReactFlow } from '@xyflow/react'
import { cn } from '@/lib/utils'
import type { NodeData } from '@/store/workflowStore'
import { useGlobalConfigStore } from '@/store/globalConfigStore'
import { Globe, ExternalLink } from 'lucide-react'
import { moduleIcons } from './ModuleSidebar'
import { moduleColors } from './moduleColors'
import { nodeVariants, spring } from '@/lib/motion'

function ModuleNodeComponent({ data, selected }: NodeProps) {
  const nodeData = data as NodeData
  const { fitView, getNodes, setCenter } = useReactFlow()
  const isDisabled = nodeData.disabled === true
  const isHighlighted = nodeData.isHighlighted === true
  const handleSize = useGlobalConfigStore((state) => state.config.display?.handleSize || 12)

  // 对于自定义模块，使用节点数据中的图标和颜色
  const isCustomModule = nodeData.moduleType === 'custom_module'
  const customIcon = isCustomModule ? (nodeData.icon as string) : null
  const customColor = isCustomModule ? (nodeData.color as string) : null
  
  // 将十六进制颜色转换为RGB，用于生成浅色背景
  const hexToRgb = (hex: string) => {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
    return result ? {
      r: parseInt(result[1], 16),
      g: parseInt(result[2], 16),
      b: parseInt(result[3], 16)
    } : null
  }
  
  const getCustomModuleStyle = () => {
    if (!customColor) return {}
    const rgb = hexToRgb(customColor)
    if (!rgb) return {}
    
    // 计算亮度，决定文字颜色
    // 使用相对亮度公式：(0.299*R + 0.587*G + 0.114*B)
    const brightness = (0.299 * rgb.r + 0.587 * rgb.g + 0.114 * rgb.b)
    
    // 生成浅色背景（类似bg-xxx-100的效果）
    // 将颜色与白色混合，使其变浅（混合比例：20%原色 + 80%白色）
    const lightR = Math.round(rgb.r * 0.2 + 255 * 0.8)
    const lightG = Math.round(rgb.g * 0.2 + 255 * 0.8)
    const lightB = Math.round(rgb.b * 0.2 + 255 * 0.8)
    
    // 文字颜色使用深色版本（类似text-xxx-900的效果）
    // 将颜色变暗（混合比例：80%原色 + 20%黑色）
    const darkR = Math.round(rgb.r * 0.2)
    const darkG = Math.round(rgb.g * 0.2)
    const darkB = Math.round(rgb.b * 0.2)
    
    // 使用浅色背景和深色文字，与内置模块样式一致
    return {
      borderColor: customColor,  // 边框使用原色
      backgroundColor: `rgb(${lightR}, ${lightG}, ${lightB})`,  // 浅色背景
      color: `rgb(${darkR}, ${darkG}, ${darkB})`  // 深色文字
    }
  }
  
  const Icon = isCustomModule ? null : (moduleIcons[nodeData.moduleType] || Globe)
  const colorClass = isCustomModule 
    ? '' 
    : (moduleColors[nodeData.moduleType] || 'border-gray-500 bg-gray-50')

  const handleSubflowDoubleClick = (e: React.MouseEvent) => {
    if (nodeData.moduleType !== 'subflow') return
    e.stopPropagation()
    const subflowName = nodeData.subflowName as string
    if (!subflowName) return
    const nodes = getNodes()
    const targetNode = nodes.find(n =>
      (n.type === 'subflowHeaderNode' && n.data.subflowName === subflowName) ||
      (n.type === 'groupNode' && n.data.isSubflow && n.data.subflowName === subflowName)
    )
    if (targetNode) {
      if (targetNode.type === 'groupNode') {
        // 分组节点用 setCenter 定位到中心
        const w = (targetNode.data.width as number) || (targetNode.width as number) || 400
        const h = (targetNode.data.height as number) || (targetNode.height as number) || 300
        const cx = targetNode.position.x + w / 2
        const cy = targetNode.position.y + h / 2
        setCenter(cx, cy, { duration: 500, zoom: 0.8 })
      } else {
        fitView({ nodes: [targetNode], duration: 500, padding: 0.3 })
      }
      setTimeout(() => {
        const event = new CustomEvent('highlight-node', { detail: { nodeId: targetNode.id } })
        window.dispatchEvent(event)
      }, 100)
    }
  }

  const getSummary = () => {
    if (nodeData.moduleType === 'subflow' && nodeData.subflowName) return `📦 ${nodeData.subflowName}`
    if (nodeData.url) return nodeData.url as string
    if (nodeData.selector) return nodeData.selector as string
    if (nodeData.text) return nodeData.text as string
    if (nodeData.logMessage) return nodeData.logMessage as string
    if (nodeData.variableName) return `→ ${nodeData.variableName}`
    if (nodeData.userPrompt) return nodeData.userPrompt as string
    if (nodeData.requestUrl) return nodeData.requestUrl as string
    return ''
  }

  const truncateText = (text: string, maxLen: number) =>
    text.length <= maxLen ? text : text.slice(0, maxLen) + '...'

  const summary = truncateText(getSummary(), 30)
  const customName = nodeData.name as string | undefined
  const isSubflow = nodeData.moduleType === 'subflow'

  return (
    <motion.div
      variants={nodeVariants}
      initial="initial"
      animate="animate"
      whileHover={
        isDisabled
          ? {}
          : {
              scale: 1.03,
              y: -2,
              boxShadow: '0 12px 32px rgba(0,0,0,0.15)',
              transition: { type: 'spring', stiffness: 400, damping: 25 },
            }
      }
      whileTap={{ scale: 0.98 }}
      className={cn(
        'relative px-4 py-3 rounded-lg border-2 shadow-sm min-w-[180px] max-w-[280px]',
        isDisabled ? 'border-gray-300 bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400' : (isCustomModule ? '' : colorClass),
        selected && 'ring-2 ring-primary ring-offset-2 shadow-lg scale-[1.02]',
        isHighlighted && 'ring-4 ring-amber-500 ring-offset-2 shadow-2xl scale-105 animate-pulse border-amber-500',
        isSubflow && nodeData.subflowName ? 'cursor-pointer' : ''
      )}
      style={
        isDisabled 
          ? { opacity: 0.6 } 
          : isCustomModule && customColor
          ? getCustomModuleStyle()
          : undefined
      }
      onDoubleClick={isSubflow && nodeData.subflowName ? handleSubflowDoubleClick : undefined}
    >
      {/* 禁用标记 */}
      {isDisabled && (
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={spring.bouncy}
          className="absolute -top-2 -right-2 bg-gray-500 text-white text-[10px] px-1.5 py-0.5 rounded-full"
        >
          已禁用
        </motion.div>
      )}

      {/* 子流程跳转图标 */}
      {isSubflow && nodeData.subflowName && (
        <motion.button
          initial={{ scale: 0, rotate: -45 }}
          animate={{ scale: 1, rotate: 0 }}
          transition={spring.bouncy}
          whileHover={{ scale: 1.2, rotate: 10 }}
          className="absolute -top-2 -right-2 bg-emerald-500 text-white p-1 rounded-full shadow-md hover:bg-emerald-600 transition-colors cursor-pointer"
          title="跳转到子流程定义"
          onClick={(e) => {
            e.stopPropagation()
            handleSubflowDoubleClick(e as unknown as React.MouseEvent)
          }}
        >
          <ExternalLink className="w-3 h-3" />
        </motion.button>
      )}

      {/* 输入连接点 */}
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-gray-400 !border-2 !border-white"
        style={{ width: `${handleSize}px`, height: `${handleSize}px` }}
      />

      {/* 节点内容 */}
      <div className="flex items-center gap-2">
        <motion.div
          whileHover={{ rotate: [0, -10, 10, 0], transition: { duration: 0.4 } }}
        >
          {isCustomModule && customIcon ? (
            <span className="text-2xl">{customIcon}</span>
          ) : Icon ? (
            <Icon className="w-5 h-5 text-current" />
          ) : (
            <Globe className="w-5 h-5 text-current" />
          )}
        </motion.div>
        <div className="flex-1 min-w-0">
          <div className="font-semibold text-sm truncate text-current">
            {nodeData.label}
            {customName && (
              <span className="text-amber-600 dark:text-amber-400 font-normal ml-1">
                ({customName})
              </span>
            )}
            {nodeData.remark && (
              <span className="text-amber-500 dark:text-amber-400 font-normal ml-1">
                ({nodeData.remark})
              </span>
            )}
          </div>
          {summary && (
            <div className={cn(
              'text-xs truncate mt-0.5 text-current',
              isSubflow && nodeData.subflowName ? 'text-emerald-600 dark:text-emerald-400 font-bold opacity-100' : 'opacity-75'
            )}>
              {summary}
            </div>
          )}
        </div>
      </div>

      {/* 输出连接点 */}
      {nodeData.moduleType === 'condition' ||
       nodeData.moduleType === 'face_recognition' ||
       nodeData.moduleType === 'element_exists' ||
       nodeData.moduleType === 'element_visible' ||
       nodeData.moduleType === 'image_exists' ||
       nodeData.moduleType === 'phone_image_exists' ||
       nodeData.moduleType === 'probability_trigger' ? (
        <>
          <Handle type="source" position={Position.Bottom} id={nodeData.moduleType === 'probability_trigger' ? 'path1' : 'true'}
            className="!bg-green-500 !border-2 !border-white" style={{ left: '30%', width: `${handleSize}px`, height: `${handleSize}px` }} />
          <div className="absolute -bottom-5 text-[10px] text-green-600 font-medium" style={{ left: '30%', transform: 'translateX(-50%)' }}>
            {nodeData.moduleType === 'probability_trigger' ? '路径1' : nodeData.moduleType === 'face_recognition' ? '匹配' : nodeData.moduleType === 'element_visible' ? '可见' : nodeData.moduleType === 'element_exists' || nodeData.moduleType === 'image_exists' || nodeData.moduleType === 'phone_image_exists' ? '存在' : '是'}
          </div>
          <Handle type="source" position={Position.Bottom} id={nodeData.moduleType === 'probability_trigger' ? 'path2' : 'false'}
            className="!bg-red-500 !border-2 !border-white" style={{ left: '70%', width: `${handleSize}px`, height: `${handleSize}px` }} />
          <div className="absolute -bottom-5 text-[10px] text-red-600 font-medium" style={{ left: '70%', transform: 'translateX(-50%)' }}>
            {nodeData.moduleType === 'probability_trigger' ? '路径2' : nodeData.moduleType === 'face_recognition' ? '不匹配' : nodeData.moduleType === 'element_visible' ? '不可见' : nodeData.moduleType === 'element_exists' || nodeData.moduleType === 'image_exists' || nodeData.moduleType === 'phone_image_exists' ? '不存在' : '否'}
          </div>
          <Handle type="source" position={Position.Right} id="error" className="!bg-orange-500 !border-2 !border-white" style={{ top: '50%', width: `${handleSize * 0.83}px`, height: `${handleSize * 0.83}px` }} />
        </>
      ) : nodeData.moduleType === 'loop' || nodeData.moduleType === 'foreach' || nodeData.moduleType === 'foreach_dict' ? (
        <>
          <Handle type="source" position={Position.Bottom} id="loop" className="!bg-green-500 !border-2 !border-white" style={{ left: '30%', width: `${handleSize}px`, height: `${handleSize}px` }} />
          <div className="absolute -bottom-5 text-[10px] text-green-600 font-medium" style={{ left: '30%', transform: 'translateX(-50%)' }}>循环</div>
          <Handle type="source" position={Position.Bottom} id="done" className="!bg-red-500 !border-2 !border-white" style={{ left: '70%', width: `${handleSize}px`, height: `${handleSize}px` }} />
          <div className="absolute -bottom-5 text-[10px] text-red-600 font-medium" style={{ left: '70%', transform: 'translateX(-50%)' }}>完成</div>
          <Handle type="source" position={Position.Right} id="error" className="!bg-orange-500 !border-2 !border-white" style={{ top: '50%', width: `${handleSize * 0.83}px`, height: `${handleSize * 0.83}px` }} />
        </>
      ) : (
        <>
          <Handle type="source" position={Position.Bottom} className="!bg-gray-400 !border-2 !border-white" style={{ width: `${handleSize}px`, height: `${handleSize}px` }} />
          <Handle type="source" position={Position.Right} id="error" className="!bg-orange-500 !border-2 !border-white" style={{ top: '50%', width: `${handleSize * 0.83}px`, height: `${handleSize * 0.83}px` }} />
        </>
      )}
    </motion.div>
  )
}

export const ModuleNode = memo(ModuleNodeComponent)
