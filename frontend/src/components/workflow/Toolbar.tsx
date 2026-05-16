import { motion, AnimatePresence } from 'framer-motion'
import { spring } from '@/lib/motion'
import { useWorkflowStore } from '@/store/workflowStore'
import { useGlobalConfigStore } from '@/store/globalConfigStore'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useConfirm } from '@/components/ui/confirm-dialog'
import { workflowApi } from '@/services/api'
import { socketService } from '@/services/socket'
import { getBackendBaseUrl } from '@/services/config'
import { GlobalConfigDialog } from './GlobalConfigDialog'
import { DocumentationDialog } from './documentation'
import { ExportDialog, type ExportFormat } from './ExportDialog'
import { AutoBrowserDialog } from './AutoBrowserDialog'
import { WorkflowHubDialog } from './WorkflowHubDialog'
import { LocalWorkflowDialog } from './LocalWorkflowDialog'
import { ScheduledTasksDialog } from '../scheduled-tasks/ScheduledTasksDialog'
import { PhoneMirrorDialog } from './PhoneMirrorDialog'
import { VariableTrackingPanel } from './VariableTrackingPanel'
import { ScreenshotNameDialog, ScreenshotErrorDialog } from './ScreenshotNameDialog'
import { useClipboardImageMonitor } from '@/hooks/useClipboardImageMonitor'
import { customModulesApi } from '@/services/api'
import {
  Play,
  Square,
  Save,
  FolderOpen,
  Settings,
  BookOpen,
  Globe,
  Package,
  Code,
  Clock,
  EyeOff,
  Smartphone,
  Activity,
  AlignLeft,
  AlignCenter,
  AlignRight,
  AlignVerticalJustifyStart,
  AlignVerticalJustifyCenter,
  AlignVerticalJustifyEnd,
  AlignHorizontalDistributeCenter,
  AlignVerticalDistributeCenter,
  MoreVertical,
  MoreHorizontal,
  ChevronDown,
  Edit,
  X,
} from 'lucide-react'
import { useState, useEffect, useCallback, useRef } from 'react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from '@/components/ui/dropdown-menu'

export function Toolbar() {
  const [workflowId, setWorkflowId] = useState<string | null>(null)
  const [showGlobalConfig, setShowGlobalConfig] = useState(false)
  const [showDocumentation, setShowDocumentation] = useState(false)
  const [showExportDialog, setShowExportDialog] = useState(false)
  const [showAutoBrowser, setShowAutoBrowser] = useState(false)
  const [showWorkflowHub, setShowWorkflowHub] = useState(false)
  const [showLocalWorkflow, setShowLocalWorkflow] = useState(false)
  const [showScheduledTasks, setShowScheduledTasks] = useState(false)
  const [showPhoneMirror, setShowPhoneMirror] = useState(false)
  const [showVariableTracking, setShowVariableTracking] = useState(false)
  const [defaultFolder, setDefaultFolder] = useState('')
  const [showScreenshotNameDialog, setShowScreenshotNameDialog] = useState(false)
  const [screenshotAsset, setScreenshotAsset] = useState<any>(null)
  const [isScreenshotting, setIsScreenshotting] = useState(false)
  const [screenshotError, setScreenshotError] = useState<{error: string, cancelled?: boolean} | null>(null)
  const [showClipboardImageDialog, setShowClipboardImageDialog] = useState(false)
  const [clipboardImageInfo, setClipboardImageInfo] = useState<{width: number, height: number} | null>(null)
  const [editingCustomModuleId, setEditingCustomModuleId] = useState<string | null>(null)
  const [editingCustomModuleName, setEditingCustomModuleName] = useState<string>('')
  const { confirm, ConfirmDialog } = useConfirm()
  
  // 用于记录输入框聚焦时的初始名称
  const nameOnFocusRef = useRef<string>('')
  
  // 使用选择器确保配置更新时组件重新渲染
  const config = useGlobalConfigStore((state) => state.config)
  
  // 调试：监听配置变化
  useEffect(() => {
    console.log('[Toolbar] 配置已更新:', {
      autoCloseBrowser: config.browser?.autoCloseBrowser,
      fullscreen: config.browser?.fullscreen,
      type: config.browser?.type
    })
  }, [config.browser?.autoCloseBrowser, config.browser?.fullscreen, config.browser?.type])
  
  const name = useWorkflowStore((state) => state.name)
  const nodes = useWorkflowStore((state) => state.nodes)
  const edges = useWorkflowStore((state) => state.edges)
  const variables = useWorkflowStore((state) => state.variables)
  const hasUnsavedChanges = useWorkflowStore((state) => state.hasUnsavedChanges)
  const setWorkflowName = useWorkflowStore((state) => state.setWorkflowName)
  const setWorkflowNameWithHistory = useWorkflowStore((state) => state.setWorkflowNameWithHistory)
  const executionStatus = useWorkflowStore((state) => state.executionStatus)
  const exportWorkflow = useWorkflowStore((state) => state.exportWorkflow)
  const clearWorkflow = useWorkflowStore((state) => state.clearWorkflow)
  const addLog = useWorkflowStore((state) => state.addLog)
  const setExecutionStatus = useWorkflowStore((state) => state.setExecutionStatus)
  const clearLogs = useWorkflowStore((state) => state.clearLogs)
  const clearCollectedData = useWorkflowStore((state) => state.clearCollectedData)
  const setBottomPanelTab = useWorkflowStore((state) => state.setBottomPanelTab)
  const markAsSaved = useWorkflowStore((state) => state.markAsSaved)
  const alignNodes = useWorkflowStore((state) => state.alignNodes)

  const isRunning = executionStatus === 'running'

  // 处理名称输入框聚焦 - 记录初始名称
  const handleNameFocus = useCallback(() => {
    nameOnFocusRef.current = name
  }, [name])

  // 处理名称输入框失焦 - 如果名称有变化则保存历史
  const handleNameBlur = useCallback(() => {
    if (nameOnFocusRef.current !== name) {
      // 名称有变化，使用 setWorkflowNameWithHistory 保存历史
      // 先恢复旧名称，再调用带历史的方法设置新名称
      const newName = name
      setWorkflowName(nameOnFocusRef.current)
      setWorkflowNameWithHistory(newName)
    }
  }, [name, setWorkflowName, setWorkflowNameWithHistory])

  // 获取默认文件夹
  useEffect(() => {
    const loadDefaultFolder = async () => {
      // 等待配置加载完成
      const { preloadConfig } = await import('@/services/config')
      await preloadConfig()
      
      const API_BASE = getBackendBaseUrl()
      fetch(`${API_BASE}/api/local-workflows/default-folder`)
        .then(res => res.json())
        .then(data => {
          if (data.folder) setDefaultFolder(data.folder)
        })
        .catch(console.error)
    }
    
    loadDefaultFolder()
  }, [])

  // 检测是否正在编辑自定义模块
  useEffect(() => {
    const checkEditingModule = () => {
      const moduleId = sessionStorage.getItem('editingCustomModuleId')
      const moduleName = sessionStorage.getItem('editingCustomModuleName')
      
      if (moduleId && moduleName) {
        setEditingCustomModuleId(moduleId)
        setEditingCustomModuleName(moduleName)
        console.log('[Toolbar] 检测到正在编辑自定义模块:', moduleName, moduleId)
      } else {
        setEditingCustomModuleId(null)
        setEditingCustomModuleName('')
      }
    }
    
    // 初始检测
    checkEditingModule()
    
    // 监听storage变化（跨标签页同步）
    window.addEventListener('storage', checkEditingModule)
    
    // 监听自定义事件（同标签页内更新）
    window.addEventListener('editingModuleChanged', checkEditingModule)
    
    return () => {
      window.removeEventListener('storage', checkEditingModule)
      window.removeEventListener('editingModuleChanged', checkEditingModule)
    }
  }, [])

  // 通用执行函数
  const executeWorkflow = useCallback(async (headless: boolean) => {
    if (nodes.length === 0) {
      addLog({ level: 'warning', message: '工作流没有任何节点' })
      return
    }

    clearLogs()
    clearCollectedData()
    setBottomPanelTab('logs')  // 切换到日志栏
    addLog({ level: 'info', message: `正在准备执行工作流${headless ? '（无头模式）' : ''}...` })

    try {
      // 先创建或更新工作流
      let currentWorkflowId = workflowId

      if (!currentWorkflowId) {
        const createResult = await workflowApi.create({
          name,
          nodes: nodes.map(n => ({
            id: n.id,
            type: n.data.moduleType,
            position: n.position,
            data: n.data,
            style: n.style,
          })),
          edges: edges.map(e => ({
            id: e.id,
            source: e.source,
            target: e.target,
            sourceHandle: e.sourceHandle,
            targetHandle: e.targetHandle,
          })),
          variables: variables.map(v => ({
            name: v.name,
            value: v.value,
            type: v.type,
            scope: v.scope,
          })),
        })

        if (createResult.error) {
          addLog({ level: 'error', message: `创建工作流失败: ${createResult.error}` })
          return
        }

        currentWorkflowId = createResult.data!.id
        setWorkflowId(currentWorkflowId)
      } else {
        // 更新现有工作流
        await workflowApi.update(currentWorkflowId, {
          name,
          nodes: nodes.map(n => ({
            id: n.id,
            type: n.data.moduleType,
            position: n.position,
            data: n.data,
            style: n.style,
          })),
          edges: edges.map(e => ({
            id: e.id,
            source: e.source,
            target: e.target,
            sourceHandle: e.sourceHandle,
            targetHandle: e.targetHandle,
          })),
          variables: variables.map(v => ({
            name: v.name,
            value: v.value,
            type: v.type,
            scope: v.scope,
          })),
        })
      }

      // 执行工作流
      // 传递浏览器配置
      const browserConfig = config.browser ? {
        type: config.browser.type || 'msedge',
        executablePath: config.browser.executablePath || undefined,  // 不指定时!
        userDataDir: config.browser.userDataDir || undefined,  // 不指定时!
        fullscreen: config.browser.fullscreen || false,
        autoCloseBrowser: config.browser.autoCloseBrowser,
        launchArgs: config.browser.launchArgs || undefined  // 这个参数也没有!
      } : undefined
      
      console.log('[Toolbar] 执行工作流，无头模式:', headless, '浏览器配置:', browserConfig)
      
      const executeResult = await workflowApi.execute(currentWorkflowId, { 
        headless,
        browserConfig 
      })
      
      if (executeResult.error) {
        addLog({ level: 'error', message: `执行失败: ${executeResult.error}` })
        return
      }

      setExecutionStatus('running')
      addLog({ level: 'info', message: `工作流开始执行${headless ? '（无头模式）' : ''}` })
    } catch (error) {
      addLog({ level: 'error', message: `执行异常: ${error}` })
    }
  }, [nodes, edges, variables, name, workflowId, addLog, clearLogs, clearCollectedData, setBottomPanelTab, setExecutionStatus, config.browser])

  // 普通运行（有头模式）
  const handleRun = useCallback(async () => {
    await executeWorkflow(false)
  }, [executeWorkflow])

  // 无头模式运行
  const handleRunHeadless = useCallback(async () => {
    await executeWorkflow(true)
  }, [executeWorkflow])

  const handleStop = useCallback(async () => {
    if (workflowId) {
      socketService.stopExecution(workflowId)
      await workflowApi.stop(workflowId)
    }
    setExecutionStatus('stopped')
    addLog({ level: 'warning', message: '工作流已停止' })
  }, [workflowId, setExecutionStatus, addLog])

  const handleSave = useCallback(async (skipConfirm = false) => {
    if (nodes.length === 0) {
      if (!skipConfirm) {
        addLog({ level: 'warning', message: '工作流没有任何节点，无法保存' })
      }
      return
    }

    const currentFolder = config.workflow?.localFolder || defaultFolder
    if (!currentFolder) {
      if (!skipConfirm) {
        addLog({ level: 'error', message: '未配置工作流保存路径' })
      }
      return
    }

    // 使用工作流名称作为文件名
    const filename = name || '未命名工作流'
    const workflowData = JSON.parse(exportWorkflow())

    try {
      // 如果不跳过确认，且用户开启了覆盖提示，先检查文件是否已存在
      const showOverwriteConfirm = config.workflow?.showOverwriteConfirm !== false
      console.log('[Toolbar] handleSave 调试:', {
        skipConfirm,
        showOverwriteConfirm,
        configValue: config.workflow?.showOverwriteConfirm,
        willCheckExists: !skipConfirm && showOverwriteConfirm
      })
      
      if (!skipConfirm && showOverwriteConfirm) {
        console.log('[Toolbar] 检查文件是否存在:', filename)
        const API_BASE = getBackendBaseUrl()
        const checkResponse = await fetch(`${API_BASE}/api/local-workflows/check-exists`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            filename,
            content: { _folder: currentFolder }
          })
        })
        const checkData = await checkResponse.json()
        console.log('[Toolbar] 文件检查结果:', checkData)

        // 如果文件已存在，询问用户是否覆盖
        if (checkData.exists) {
          console.log('[Toolbar] 文件已存在，弹出确认对话框')
          const shouldOverwrite = await confirm(
            `工作流 "${checkData.filename}" 已存在，是否覆盖？`,
            { type: 'warning', title: '文件已存在', confirmText: '覆盖', cancelText: '取消' }
          )
          
          console.log('[Toolbar] 用户选择:', shouldOverwrite ? '覆盖' : '取消')
          
          if (!shouldOverwrite) {
            addLog({ level: 'info', message: '已取消保存' })
            return
          }
        } else {
          console.log('[Toolbar] 文件不存在，直接保存')
        }
      }

      // 执行保存
      const API_BASE = getBackendBaseUrl()
      const response = await fetch(`${API_BASE}/api/local-workflows/save-to-folder`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filename,
          content: { ...workflowData, _folder: currentFolder }
        })
      })
      const data = await response.json()

      if (data.success) {
        if (!skipConfirm) {
          addLog({ level: 'success', message: `工作流已保存: ${data.filename}` })
        }
        markAsSaved()  // 标记为已保存
      } else {
        if (!skipConfirm) {
          addLog({ level: 'error', message: `保存失败: ${data.error}` })
        }
      }
    } catch (e) {
      if (!skipConfirm) {
        addLog({ level: 'error', message: `保存出错: ${e}` })
      }
    }
  }, [nodes.length, config.workflow?.localFolder, config.workflow?.showOverwriteConfirm, defaultFolder, name, exportWorkflow, addLog, confirm])

  const handleNewWorkflow = useCallback(() => {
    clearWorkflow()
    setWorkflowId(null)
    addLog({ level: 'info', message: '已创建新工作流' })
  }, [clearWorkflow, addLog])

  // 自动保存逻辑
  useEffect(() => {
    // 如果未开启自动保存，直接返回
    if (!config.workflow?.autoSave) return
    
    // 如果没有节点，不自动保存
    if (nodes.length === 0) return
    
    // 防抖：延迟2秒后自动保存
    const timer = setTimeout(() => {
      handleSave(true) // skipConfirm = true，不弹出覆盖提示
    }, 2000)
    
    return () => clearTimeout(timer)
  }, [nodes, edges, name, config.workflow?.autoSave, handleSave])

  // 快捷键监听（F5/Shift+F5 由后端全局热键处理，前端只拦截防止浏览器刷新）
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // F5 和 Shift+F5：只拦截，不执行任何操作（由后端全局热键处理）
      if (e.key === 'F5') {
        e.preventDefault()
        return
      }
      
      // 如果焦点在输入框中，不处理其他快捷键
      const target = e.target as HTMLElement
      const isInInput = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable
      if (isInInput) return
      
      // Ctrl+S 保存
      if (e.ctrlKey && e.key === 's') {
        e.preventDefault()
        handleSave()
      }
      // Alt+N 新建
      if (e.altKey && e.key === 'n') {
        e.preventDefault()
        handleNewWorkflow()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [handleSave, handleNewWorkflow])
  
  // 页面关闭/刷新前检查未保存的更改
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      // 只有当有节点且有未保存的更改时才提示
      if (nodes.length > 0 && hasUnsavedChanges) {
        e.preventDefault()
        // 现代浏览器会显示标准提示，自定义消息可能不会显示
        e.returnValue = '工作流有未保存的更改，确定要离开吗？'
        return e.returnValue
      }
    }

    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => window.removeEventListener('beforeunload', handleBeforeUnload)
  }, [nodes.length, hasUnsavedChanges])
  
  // 监听剪贴板中的新图片
  useClipboardImageMonitor((width, height) => {
    console.log('[Toolbar] 检测到剪贴板新图片:', width, 'x', height)
    setClipboardImageInfo({ width, height })
    setShowClipboardImageDialog(true)
    addLog({ level: 'info', message: `检测到剪贴板中有新图片 (${width}x${height})，是否保存到图像资源？` })
  })

  // 处理剪贴板图片保存
  const handleClipboardImageConfirm = async (name: string) => {
    const API_BASE = getBackendBaseUrl()
    
    try {
      const response = await fetch(`${API_BASE}/api/system/save-clipboard-image`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name })
      })
      
      const data = await response.json()
      
      if (data.success && data.assetId) {
        addLog({ level: 'success', message: `剪贴板图片已保存: ${name}.png` })
        window.dispatchEvent(new CustomEvent('refresh:image-assets'))
      } else {
        addLog({ level: 'error', message: `保存失败: ${data.error}` })
      }
    } catch (error) {
      console.error('[Toolbar] 保存剪贴板图片失败:', error)
      addLog({ level: 'error', message: `保存剪贴板图片失败: ${error}` })
    }
    
    setShowClipboardImageDialog(false)
    setClipboardImageInfo(null)
  }

  const handleClipboardImageCancel = () => {
    setShowClipboardImageDialog(false)
    setClipboardImageInfo(null)
  }

  // 执行截图的核心逻辑
  const doScreenshot = useCallback(async () => {
    if (isScreenshotting) {
      console.log('[Toolbar] 截图进行中，忽略重复请求')
      return
    }
    console.log('[Toolbar] 准备启动独立截图工具')
    setIsScreenshotting(true)
    setScreenshotError(null)

    const API_BASE = getBackendBaseUrl()
    addLog({ level: 'info', message: '正在启动截图工具，请框选截图区域...' })

    try {
      const response = await fetch(`${API_BASE}/api/system/screenshot-tool`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ saveToAssets: true })
      })

      const data = await response.json()
      console.log('[Toolbar] 截图API响应:', data)

      if (data.success && data.assetId) {
        console.log('[Toolbar] ✅ 截图保存成功, assetId:', data.assetId)
        setScreenshotAsset({
          id: data.assetId,
          originalName: data.fileName || `截图_${new Date().toLocaleTimeString()}.png`
        })
        setShowScreenshotNameDialog(true)
        addLog({ level: 'success', message: '截图成功，请为截图命名' })
      } else if (data.success && data.asset) {
        // 兼容旧版后端
        console.log('[Toolbar] ✅ 截图保存成功 (旧版):', data.asset)
        setScreenshotAsset(data.asset)
        setShowScreenshotNameDialog(true)
        addLog({ level: 'success', message: '截图成功，请为截图命名' })
      } else if (data.cancelled) {
        // 纯取消静默处理
        console.log('[Toolbar] 截图已取消')
      } else if (data.error === 'timeout') {
        console.log('[Toolbar] 截图超时')
        setScreenshotError({ error: 'timeout', cancelled: false })
      } else {
        const errMsg = data.error || '未知错误'
        console.error('[Toolbar] ❌ 截图失败:', errMsg)
        setScreenshotError({ error: errMsg, cancelled: false })
        addLog({ level: 'error', message: `截图失败: ${errMsg}` })
      }
    } catch (error) {
      console.error('[Toolbar] ❌ 调用截图API失败:', error)
      const errMsg = `调用截图工具失败: ${error}`
      setScreenshotError({ error: errMsg, cancelled: false })
      addLog({ level: 'error', message: errMsg })
    } finally {
      setIsScreenshotting(false)
    }
  }, [isScreenshotting, addLog])

  // 全局热键事件监听（后台热键触发）
  // 使用 useRef 来避免频繁重新注册事件监听器
  const isRunningRef = useRef(isRunning)
  const handleRunRef = useRef(handleRun)
  const handleStopRef = useRef(handleStop)
  const doScreenshotRef = useRef(doScreenshot)
  
  // 更新 refs
  useEffect(() => {
    isRunningRef.current = isRunning
    handleRunRef.current = handleRun
    handleStopRef.current = handleStop
    doScreenshotRef.current = doScreenshot
  }, [isRunning, handleRun, handleStop, doScreenshot])
  
  useEffect(() => {
    const handleHotkeyRun = () => {
      if (!isRunningRef.current) {
        handleRunRef.current()
      }
    }

    const handleHotkeyStop = () => {
      if (isRunningRef.current) {
        handleStopRef.current()
      }
    }

    const handleHotkeyScreenshot = () => {
      doScreenshotRef.current()
    }
    
    window.addEventListener('hotkey:run', handleHotkeyRun)
    window.addEventListener('hotkey:stop', handleHotkeyStop)
    window.addEventListener('hotkey:screenshot', handleHotkeyScreenshot)
    
    return () => {
      window.removeEventListener('hotkey:run', handleHotkeyRun)
      window.removeEventListener('hotkey:stop', handleHotkeyStop)
      window.removeEventListener('hotkey:screenshot', handleHotkeyScreenshot)
    }
  }, []) // 空依赖数组，只注册一次
  
  // 通知后端当前工作流ID（用于全局热键控制）
  const handleOpen = () => {
    setShowLocalWorkflow(true)
  }

  // 处理截图命名确认
  const handleScreenshotNameConfirm = async (newName: string) => {
    if (!screenshotAsset) return
    
    const API_BASE = getBackendBaseUrl()
    
    try {
      // 调用API重命名截图
      const response = await fetch(`${API_BASE}/api/image-assets/${screenshotAsset.id}/rename?newName=${encodeURIComponent(newName + '.png')}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' }
      })
      
      if (response.ok) {
        addLog({ level: 'success', message: `截图已保存: ${newName}.png` })
        // 刷新图像资源列表
        window.dispatchEvent(new CustomEvent('refresh:image-assets'))
      } else {
        const error = await response.json().catch(() => ({ detail: '重命名失败' }))
        addLog({ level: 'warning', message: `截图已保存，但重命名失败: ${error.detail}` })
        // 即使重命名失败也刷新列表
        window.dispatchEvent(new CustomEvent('refresh:image-assets'))
      }
    } catch (error) {
      console.error('[Toolbar] 重命名失败:', error)
      addLog({ level: 'warning', message: `截图已保存，但重命名失败` })
      // 即使重命名失败也刷新列表
      window.dispatchEvent(new CustomEvent('refresh:image-assets'))
    }
    
    setShowScreenshotNameDialog(false)
    setScreenshotAsset(null)
  }
  
  // 处理截图命名取消
  const handleScreenshotNameCancel = () => {
    if (screenshotAsset) {
      addLog({ level: 'success', message: `截图已保存: ${screenshotAsset.originalName}` })
      // 刷新图像资源列表
      window.dispatchEvent(new CustomEvent('refresh:image-assets'))
    }
    setShowScreenshotNameDialog(false)
    setScreenshotAsset(null)
  }

  // 导出为 Playwright Python 代码
  const handleExportPlaywright = useCallback(async () => {
    if (nodes.length === 0) {
      addLog({ level: 'warning', message: '工作流没有任何节点，无法导出' })
      return
    }

    try {
      // 先创建或更新工作流
      let currentWorkflowId = workflowId

      if (!currentWorkflowId) {
        const createResult = await workflowApi.create({
          name,
          nodes: nodes.map(n => ({
            id: n.id,
            type: n.data.moduleType,
            position: n.position,
            data: n.data,
            style: n.style,
          })),
          edges: edges.map(e => ({
            id: e.id,
            source: e.source,
            target: e.target,
            sourceHandle: e.sourceHandle,
            targetHandle: e.targetHandle,
          })),
          variables: variables.map(v => ({
            name: v.name,
            value: v.value,
            type: v.type,
            scope: v.scope,
          })),
        })

        if (createResult.error) {
          addLog({ level: 'error', message: `创建工作流失败: ${createResult.error}` })
          return
        }

        currentWorkflowId = createResult.data!.id
        setWorkflowId(currentWorkflowId)
      } else {
        // 更新现有工作流
        await workflowApi.update(currentWorkflowId, {
          name,
          nodes: nodes.map(n => ({
            id: n.id,
            type: n.data.moduleType,
            position: n.position,
            data: n.data,
            style: n.style,
          })),
          edges: edges.map(e => ({
            id: e.id,
            source: e.source,
            target: e.target,
            sourceHandle: e.sourceHandle,
            targetHandle: e.targetHandle,
          })),
          variables: variables.map(v => ({
            name: v.name,
            value: v.value,
            type: v.type,
            scope: v.scope,
          })),
        })
      }

      // 调用导出 API
      const API_BASE = getBackendBaseUrl()
      const response = await fetch(`${API_BASE}/api/workflows/${currentWorkflowId}/export-playwright`)
      const data = await response.json()

      if (data.code) {
        // 创建下载
        const blob = new Blob([data.code], { type: 'text/plain;charset=utf-8' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = data.filename || `${name.replace(/\s+/g, '_')}_playwright.py`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)

        addLog({ level: 'success', message: `已导出 Playwright 代码: ${data.filename}` })
      } else {
        addLog({ level: 'error', message: '导出失败: 未获取到代码' })
      }
    } catch (e) {
      addLog({ level: 'error', message: `导出出错: ${e}` })
    }
  }, [nodes, edges, variables, name, workflowId, addLog])

  // 导出为 JSON
  const handleExportJSON = useCallback(() => {
    if (nodes.length === 0) {
      addLog({ level: 'warning', message: '工作流没有任何节点，无法导出' })
      return
    }

    const workflowData = {
      name,
      nodes: nodes.map(n => ({
        id: n.id,
        type: n.data.moduleType,
        position: n.position,
        data: n.data,
        style: n.style,
        parentId: n.parentId,
      })),
      edges: edges.map(e => ({
        id: e.id,
        source: e.source,
        target: e.target,
        sourceHandle: e.sourceHandle,
        targetHandle: e.targetHandle,
      })),
      variables: variables.map(v => ({
        name: v.name,
        value: v.value,
        type: v.type,
        scope: v.scope,
      })),
      version: '1.0.0',
      exportedAt: new Date().toISOString(),
    }

    const blob = new Blob([JSON.stringify(workflowData, null, 2)], { type: 'application/json;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${name.replace(/\s+/g, '_')}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)

    addLog({ level: 'success', message: `已导出 JSON 文件: ${name}.json` })
  }, [nodes, edges, variables, name, addLog])

  // 导出为 Markdown
  const handleExportMarkdown = useCallback(() => {
    if (nodes.length === 0) {
      addLog({ level: 'warning', message: '工作流没有任何节点，无法导出' })
      return
    }

    let markdown = `# ${name}\n\n`
    markdown += `> 导出时间: ${new Date().toLocaleString('zh-CN')}\n\n`
    markdown += `---\n\n`

    // 变量列表
    if (variables.length > 0) {
      markdown += `## 📦 变量列表\n\n`
      markdown += `| 变量名 | 类型 | 默认值 | 作用域 |\n`
      markdown += `|--------|------|--------|--------|\n`
      variables.forEach(v => {
        markdown += `| ${v.name} | ${v.type} | ${v.value || '-'} | ${v.scope} |\n`
      })
      markdown += `\n`
    }

    // 节点列表
    markdown += `## 🔧 模块列表\n\n`
    markdown += `共 ${nodes.length} 个模块\n\n`
    
    nodes.forEach((node, index) => {
      const data = node.data
      markdown += `### ${index + 1}. ${data.label || data.moduleType}\n\n`
      markdown += `- **类型**: \`${data.moduleType}\`\n`
      markdown += `- **位置**: (${Math.round(node.position.x)}, ${Math.round(node.position.y)})\n`
      
      // 配置信息
      if (data.config && Object.keys(data.config).length > 0) {
        markdown += `- **配置**:\n`
        Object.entries(data.config).forEach(([key, value]) => {
          if (value !== undefined && value !== null && value !== '') {
            markdown += `  - ${key}: \`${JSON.stringify(value)}\`\n`
          }
        })
      }
      markdown += `\n`
    })

    // 连接关系
    if (edges.length > 0) {
      markdown += `## 🔗 连接关系\n\n`
      markdown += `共 ${edges.length} 条连接\n\n`
      edges.forEach((edge, index) => {
        const sourceNode = nodes.find(n => n.id === edge.source)
        const targetNode = nodes.find(n => n.id === edge.target)
        const sourceLabel = sourceNode?.data.label || edge.source
        const targetLabel = targetNode?.data.label || edge.target
        markdown += `${index + 1}. ${sourceLabel} → ${targetLabel}\n`
      })
      markdown += `\n`
    }

    markdown += `---\n\n`
    markdown += `*由 WebRPA 自动生成*\n`

    const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${name.replace(/\s+/g, '_')}.md`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)

    addLog({ level: 'success', message: `已导出 Markdown 文档: ${name}.md` })
  }, [nodes, edges, variables, name, addLog])

  // 统一的导出处理函数
  const handleExport = useCallback(async (format: ExportFormat) => {
    switch (format) {
      case 'playwright':
        await handleExportPlaywright()
        break
      case 'json':
        handleExportJSON()
        break
      case 'markdown':
        handleExportMarkdown()
        break
    }
  }, [handleExportPlaywright, handleExportJSON, handleExportMarkdown])

  const handleBrowserLog = (level: 'info' | 'success' | 'warning' | 'error', message: string) => {
    addLog({ level, message })
  }

  // 保存自定义模块工作流
  const handleSaveCustomModuleWorkflow = useCallback(async () => {
    if (!editingCustomModuleId) {
      addLog({ level: 'error', message: '未检测到正在编辑的自定义模块' })
      return
    }

    if (nodes.length === 0) {
      addLog({ level: 'warning', message: '工作流没有任何节点，无法保存' })
      return
    }

    try {
      addLog({ level: 'info', message: `正在保存模块"${editingCustomModuleName}"的工作流...` })

      // 准备工作流数据
      const workflowData = {
        nodes: nodes.map(n => ({
          id: n.id,
          type: n.data.moduleType,
          position: n.position,
          data: n.data,
          style: n.style,
        })),
        edges: edges.map(e => ({
          id: e.id,
          source: e.source,
          target: e.target,
          sourceHandle: e.sourceHandle,
          targetHandle: e.targetHandle,
        })),
      }

      // 调用API更新模块
      const result = await customModulesApi.update(editingCustomModuleId, {
        workflow: workflowData
      })

      if (result.error) {
        addLog({ level: 'error', message: `保存失败: ${result.error}` })
        return
      }

      addLog({ level: 'success', message: `模块"${editingCustomModuleName}"的工作流已保存` })
      markAsSaved()

      // 询问用户是否继续编辑或退出
      const shouldContinue = await confirm(
        `模块工作流已成功保存！\n\n是否继续编辑？\n\n点击"确定"继续编辑，点击"取消"退出编辑模式。`,
        { 
          type: 'success', 
          title: '保存成功', 
          confirmText: '继续编辑', 
          cancelText: '退出编辑' 
        }
      )

      if (!shouldContinue) {
        // 退出编辑模式
        handleExitCustomModuleEdit()
      }
    } catch (error) {
      console.error('[Toolbar] 保存自定义模块工作流失败:', error)
      addLog({ level: 'error', message: `保存失败: ${error}` })
    }
  }, [editingCustomModuleId, editingCustomModuleName, nodes, edges, addLog, markAsSaved, confirm])

  // 退出自定义模块编辑模式
  const handleExitCustomModuleEdit = useCallback(() => {
    sessionStorage.removeItem('editingCustomModuleId')
    sessionStorage.removeItem('editingCustomModuleName')
    setEditingCustomModuleId(null)
    setEditingCustomModuleName('')
    
    // 触发自定义事件通知其他组件
    window.dispatchEvent(new CustomEvent('editingModuleChanged'))
    
    // 清空画布
    clearWorkflow()
    addLog({ level: 'info', message: '已退出自定义模块编辑模式' })
  }, [clearWorkflow, addLog])

  return (
    <motion.header
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ ...spring.soft, delay: 0.05 }}
      className="h-14 border-b bg-gradient-to-r from-blue-600 via-cyan-600 to-blue-600 bg-[length:200%_100%] animate-gradient flex items-center px-2 sm:px-4 gap-2 sm:gap-4"
    >
      {/* Logo/标题 */}
      <div className="flex items-center gap-2">
        <motion.div
          className="p-1 rounded-lg bg-white/20 backdrop-blur-sm"
          whileHover={{ rotate: 360, scale: 1.1 }}
          transition={{ duration: 0.5, ease: 'easeInOut' }}
        >
          <img src="/logo.png" alt="Logo" className="w-5 h-5" />
        </motion.div>
        <motion.span
          className="hidden sm:inline font-semibold text-lg text-white drop-shadow-sm"
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ ...spring.soft, delay: 0.1 }}
        >
          WebRPA
        </motion.span>
      </div>

      {/* 分隔线 - 小屏幕隐藏 */}
      <div className="hidden md:block h-6 w-px bg-white/30" />

      {/* 自定义模块编辑模式按钮 */}
      {editingCustomModuleId && (
        <>
          <Button
            size="sm"
            className="bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 text-white border-0 shadow-md"
            onClick={handleSaveCustomModuleWorkflow}
            title={`保存"${editingCustomModuleName}"的工作流`}
          >
            <Save className="w-4 h-4 mr-1" />
            保存模块工作流
          </Button>

          <Button
            size="sm"
            variant="outline"
            className="bg-white/90 border-white/50 text-red-700 hover:bg-white hover:text-red-800"
            onClick={async () => {
              const shouldExit = await confirm(
                '确定要退出编辑模式吗？\n\n未保存的修改将会丢失。',
                { type: 'warning', title: '退出编辑', confirmText: '退出', cancelText: '取消' }
              )
              if (shouldExit) {
                handleExitCustomModuleEdit()
              }
            }}
            title="退出编辑模式"
          >
            <X className="w-4 h-4 mr-1" />
            退出编辑
          </Button>

          <div className="hidden md:block h-6 w-px bg-white/30" />
        </>
      )}

      {/* 工作流名称 - 响应式宽度 */}
      <Input
        value={name}
        onChange={(e) => setWorkflowName(e.target.value)}
        onFocus={handleNameFocus}
        onBlur={handleNameBlur}
        className="w-24 sm:w-32 md:w-48 h-8 bg-white/90 border-white/50 text-sm"
        placeholder="工作流名称"
      />

      {/* 分隔线 - 小屏幕隐藏 */}
      <div className="hidden md:block h-6 w-px bg-white/30" />

      {/* 执行控制 - 合并为下拉按钮 */}
      <div className="flex items-center gap-1 sm:gap-2">
        <AnimatePresence mode="wait">
          {!isRunning ? (
            <motion.div
              key="run"
              initial={{ opacity: 0, scale: 0.85 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.85 }}
              transition={spring.snappy}
            >
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    size="sm"
                    className="bg-gradient-to-r from-emerald-500 to-green-500 hover:from-emerald-400 hover:to-green-400 text-white border-0 shadow-md"
                    noMotion
                  >
                    <motion.span
                      className="flex items-center gap-1"
                      whileHover={{ x: 1 }}
                      transition={spring.snappy}
                    >
                      <Play className="w-4 h-4 sm:mr-1" />
                      <span className="hidden sm:inline">运行</span>
                      <span className="hidden lg:inline ml-1.5 text-[10px] opacity-70 font-normal">(F5)</span>
                      <ChevronDown className="w-3 h-3 ml-1" />
                    </motion.span>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="start" className="w-44">
                  <DropdownMenuItem onClick={handleRun}>
                    <Play className="w-4 h-4 mr-2" />
                    运行 (F5)
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={handleRunHeadless}>
                    <EyeOff className="w-4 h-4 mr-2" />
                    无头运行
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </motion.div>
          ) : (
            <motion.div
              key="stop"
              initial={{ opacity: 0, scale: 0.85 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.85 }}
              transition={spring.snappy}
            >
              <Button
                size="sm"
                className="bg-gradient-to-r from-red-500 to-rose-500 hover:from-red-400 hover:to-rose-400 text-white border-0 shadow-md"
                onClick={handleStop}
                noMotion
              >
                <motion.span
                  className="flex items-center gap-1"
                  animate={{ opacity: [1, 0.6, 1] }}
                  transition={{ duration: 1.2, repeat: Infinity }}
                >
                  <Square className="w-4 h-4 sm:mr-1" />
                  <span className="hidden sm:inline">停止</span>
                  <span className="hidden lg:inline ml-1.5 text-[10px] opacity-70 font-normal">(Shift+F5)</span>
                </motion.span>
              </Button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* 分隔线 - 小屏幕隐藏 */}
      <div className="hidden md:block h-6 w-px bg-white/30" />

      {/* 文件操作 - 大屏幕显示全部，小屏幕使用下拉菜单 */}
      <div className="hidden lg:flex items-center gap-1">
        <Button 
          variant="outline" 
          size="sm" 
          className="bg-white/90 border-white/50 text-blue-700 hover:bg-white hover:text-blue-800
            transition-all duration-200 hover:scale-105 hover:shadow-md active:scale-95" 
          onClick={() => {
            console.log('[Toolbar] 保存按钮被点击')
            handleSave()
          }}
        >
          <Save className="w-4 h-4 mr-1" />
          保存
        </Button>
        <Button 
          variant="outline" 
          size="sm" 
          className="bg-white/90 border-white/50 text-blue-700 hover:bg-white hover:text-blue-800
            transition-all duration-200 hover:scale-105 hover:shadow-md active:scale-95" 
          onClick={handleOpen}
        >
          <FolderOpen className="w-4 h-4 mr-1" />
          打开
        </Button>
        <Button 
          variant="outline" 
          size="sm" 
          className="bg-white/90 border-white/50 text-green-700 hover:bg-white hover:text-green-800
            transition-all duration-200 hover:scale-105 hover:shadow-md active:scale-95" 
          onClick={() => setShowExportDialog(true)}
        >
          <Code className="w-4 h-4 mr-1" />
          导出
        </Button>
      </div>

      {/* 文件操作下拉菜单 - 小屏幕显示 */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild className="lg:hidden">
          <Button 
            variant="outline" 
            size="sm" 
            className="bg-white/90 border-white/50 text-blue-700 hover:bg-white hover:text-blue-800
              transition-all duration-200 hover:scale-105 hover:shadow-md active:scale-95"
          >
            <MoreVertical className="w-4 h-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="w-40">
          <DropdownMenuLabel>文件操作</DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => handleSave()}>
            <Save className="w-4 h-4 mr-2" />
            保存
          </DropdownMenuItem>
          <DropdownMenuItem onClick={handleOpen}>
            <FolderOpen className="w-4 h-4 mr-2" />
            打开
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => setShowExportDialog(true)}>
            <Code className="w-4 h-4 mr-2" />
            导出
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      {/* 分隔线 - 小屏幕隐藏 */}
      <div className="hidden md:block h-6 w-px bg-white/30" />

      {/* 节点对齐 - 下拉菜单 */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button 
            variant="outline" 
            size="sm" 
            className="bg-white/90 border-white/50 text-slate-700 hover:bg-white hover:text-slate-800
              transition-all duration-200 hover:scale-105 hover:shadow-md active:scale-95"
            title="节点对齐"
          >
            <AlignCenter className="w-4 h-4" />
            <ChevronDown className="w-3 h-3 ml-1" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="w-40">
          <DropdownMenuLabel>节点对齐</DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => alignNodes('left')}>
            <AlignLeft className="w-4 h-4 mr-2" />
            左对齐
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => alignNodes('center')}>
            <AlignCenter className="w-4 h-4 mr-2" />
            水平居中
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => alignNodes('right')}>
            <AlignRight className="w-4 h-4 mr-2" />
            右对齐
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => alignNodes('top')}>
            <AlignVerticalJustifyStart className="w-4 h-4 mr-2" />
            上对齐
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => alignNodes('middle')}>
            <AlignVerticalJustifyCenter className="w-4 h-4 mr-2" />
            垂直居中
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => alignNodes('bottom')}>
            <AlignVerticalJustifyEnd className="w-4 h-4 mr-2" />
            下对齐
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => alignNodes('distribute-horizontal')}>
            <AlignHorizontalDistributeCenter className="w-4 h-4 mr-2" />
            水平均匀分布
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => alignNodes('distribute-vertical')}>
            <AlignVerticalDistributeCenter className="w-4 h-4 mr-2" />
            垂直均匀分布
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      {/* 右侧操作 - 大屏幕显示部分，小屏幕使用下拉菜单 */}
      <div className="ml-auto flex items-center gap-1 sm:gap-2">
        {/* 工作流仓库 - 直接显示 */}
        <Button 
          variant="outline" 
          size="sm" 
          className="bg-white/90 border-white/50 text-purple-700 hover:bg-white hover:text-purple-800
            transition-all duration-200 hover:scale-105 hover:shadow-md active:scale-95" 
          onClick={() => setShowWorkflowHub(true)}
          title="工作流仓库"
        >
          <Package className="w-4 h-4 sm:mr-1" />
          <span className="hidden lg:inline">工作流仓库</span>
        </Button>

        {/* 自动化浏览器 - 直接显示 */}
        <Button 
          variant="outline" 
          size="sm" 
          className="bg-white/90 border-white/50 text-teal-700 hover:bg-white hover:text-teal-800
            transition-all duration-200 hover:scale-105 hover:shadow-md active:scale-95" 
          onClick={() => setShowAutoBrowser(true)}
          title="自动化浏览器"
        >
          <Globe className="w-4 h-4 sm:mr-1" />
          <span className="hidden lg:inline">自动化浏览器</span>
        </Button>

        {/* 全局配置 - 始终显示 */}
        <Button 
          variant="outline" 
          size="sm" 
          className="bg-white/90 border-white/50 text-gray-700 hover:bg-white hover:text-gray-800" 
          onClick={() => setShowGlobalConfig(true)}
        >
          <motion.span
            className="flex items-center gap-1"
            whileHover={{ rotate: 90 }}
            transition={spring.snappy}
          >
            <Settings className="w-4 h-4 sm:mr-1" />
          </motion.span>
          <span className="hidden sm:inline">全局配置</span>
        </Button>

        {/* 其他操作下拉菜单 */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button 
              variant="outline" 
              size="sm" 
              className="bg-white/90 border-white/50 text-blue-700 hover:bg-white hover:text-blue-800
                transition-all duration-200 hover:scale-105 hover:shadow-md active:scale-95"
              title="更多操作"
            >
              <MoreHorizontal className="w-4 h-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-44">
            <DropdownMenuLabel>工具与功能</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => setShowVariableTracking(true)}>
              <Activity className="w-4 h-4 mr-2" />
              变量追踪
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => setShowPhoneMirror(true)}>
              <Smartphone className="w-4 h-4 mr-2" />
              手机镜像
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => setShowScheduledTasks(true)}>
              <Clock className="w-4 h-4 mr-2" />
              计划任务
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => setShowDocumentation(true)}>
              <BookOpen className="w-4 h-4 mr-2" />
              教学文档
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* 全局配置对话框 */}
      <GlobalConfigDialog isOpen={showGlobalConfig} onClose={() => setShowGlobalConfig(false)} />
      
      {/* 教学文档对话框 */}
      <DocumentationDialog isOpen={showDocumentation} onClose={() => setShowDocumentation(false)} />
      
      {/* 导出对话框 */}
      <ExportDialog isOpen={showExportDialog} onClose={() => setShowExportDialog(false)} onExport={handleExport} />
      
      {/* 自动化浏览器对话框 */}
      <AutoBrowserDialog 
        isOpen={showAutoBrowser} 
        onClose={() => setShowAutoBrowser(false)} 
        onLog={handleBrowserLog}
      />
      
      {/* 工作流仓库对话框 */}
      <WorkflowHubDialog
        open={showWorkflowHub}
        onClose={() => setShowWorkflowHub(false)}
      />
      
      {/* 本地工作流对话框 */}
      <LocalWorkflowDialog
        isOpen={showLocalWorkflow}
        onClose={() => setShowLocalWorkflow(false)}
        onLog={(level, message) => addLog({ level, message })}
      />
      
      {/* 计划任务对话框 */}
      <ScheduledTasksDialog
        open={showScheduledTasks}
        onClose={() => setShowScheduledTasks(false)}
      />
      
      {/* 手机镜像对话框 */}
      <PhoneMirrorDialog
        open={showPhoneMirror}
        onClose={() => setShowPhoneMirror(false)}
      />
      
      {/* 变量追踪面板 */}
      <VariableTrackingPanel
        workflowId={workflowId || ''}
        isOpen={showVariableTracking}
        onClose={() => setShowVariableTracking(false)}
      />
      
      {/* 确认对话框 */}
      <ConfirmDialog />
      
      {/* 截图命名对话框 */}
      {showScreenshotNameDialog && screenshotAsset && (
        <ScreenshotNameDialog
          defaultName={screenshotAsset.originalName}
          onConfirm={handleScreenshotNameConfirm}
          onCancel={handleScreenshotNameCancel}
        />
      )}

      {/* 截图错误/重试对话框 */}
      {screenshotError && (
        <ScreenshotErrorDialog
          error={screenshotError.error}
          cancelled={screenshotError.cancelled}
          onRetry={() => {
            setScreenshotError(null)
            doScreenshot()
          }}
          onCancel={() => setScreenshotError(null)}
        />
      )}

      {/* 剪贴板图片保存对话框 */}
      {showClipboardImageDialog && clipboardImageInfo && (
        <ScreenshotNameDialog
          defaultName={`剪贴板_${new Date().toLocaleTimeString()}`}
          onConfirm={handleClipboardImageConfirm}
          onCancel={handleClipboardImageCancel}
        />
      )}
    </motion.header>
  )
}
