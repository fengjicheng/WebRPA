/**
 * 前端 Skills 派发器
 *
 * 当后端 AI 助手返回 client_action 工具调用时，由这个文件负责实际操作 WebRPA。
 * 它会从 zustand store 中拿到当前 workflow 状态、并直接调用 store 的 actions。
 *
 * 设计原则：把所有用户能在 UI 上做的事都暴露成 action，
 * 让小助手具有完全的前端操作能力。
 */
import { useWorkflowStore } from '@/store/workflowStore'
import { useGlobalConfigStore } from '@/store/globalConfigStore'
import { localWorkflowApi, workflowApi } from '@/services/api'
import { socketService } from '@/services/socket'

export interface ClientActionPayload {
  action: string
  payload?: Record<string, any>
}

export interface ClientActionResult {
  success: boolean
  message?: string
  data?: any
  error?: string
}

/**
 * 跨组件通信：让外部 UI 组件订阅事件来响应小助手的指令
 */
const listeners = new Map<string, Set<(payload: any) => void>>()

export function onAssistantUiEvent(event: string, handler: (payload: any) => void) {
  let set = listeners.get(event)
  if (!set) {
    set = new Set()
    listeners.set(event, set)
  }
  set.add(handler)
  return () => {
    set!.delete(handler)
  }
}

function emitAssistantUiEvent(event: string, payload: any) {
  const set = listeners.get(event)
  if (!set) return
  set.forEach((h) => {
    try {
      h(payload)
    } catch (err) {
      console.error('[AssistantUiEvent]', event, err)
    }
  })
}

/**
 * 执行客户端操作。返回执行结果，便于把结果通过下一轮对话告诉 LLM。
 */
export async function executeClientAction(
  action: string,
  payload: Record<string, any> = {}
): Promise<ClientActionResult> {
  try {
    switch (action) {
      // ============================================================
      // 画布操作
      // ============================================================
      case 'new_workflow': {
        useWorkflowStore.getState().clearWorkflow()
        return { success: true, message: '已新建空白工作流' }
      }

      case 'add_nodes': {
        const nodes = (payload.nodes as any[]) || []
        const edges = (payload.edges as any[]) || []
        if (!Array.isArray(nodes) || nodes.length === 0) {
          return { success: false, error: '没有可添加的节点' }
        }
        const store = useWorkflowStore.getState()
        const xyNodes = nodes.map((n) => ({
          id: n.id,
          type: n.type,
          position: n.position || { x: 200, y: 200 },
          data: {
            label: n.data?.label || n.type,
            moduleType: n.type,
            ...(n.data?.config || {}),
          },
        }))
        const xyEdges = edges.map((e: any) => ({
          id: e.id,
          source: e.source,
          target: e.target,
          sourceHandle: e.sourceHandle,
          targetHandle: e.targetHandle,
        }))
        store.loadWorkflow({
          nodes: [...store.nodes, ...xyNodes] as any,
          edges: [...store.edges, ...xyEdges] as any,
          name: store.name,
        })
        return { success: true, message: `已添加 ${xyNodes.length} 个节点` }
      }

      case 'load_workflow_from_data': {
        const nodes = (payload.nodes as any[]) || []
        const edges = (payload.edges as any[]) || []
        const name = (payload.name as string) || '未命名工作流'
        const xyNodes = nodes.map((n) => ({
          id: n.id,
          type: n.type,
          position: n.position || { x: 200, y: 200 },
          data: {
            label: n.data?.label || n.type,
            moduleType: n.type,
            ...(n.data?.config || {}),
          },
        }))
        useWorkflowStore.getState().loadWorkflow({
          nodes: xyNodes as any,
          edges: edges as any,
          name,
        })
        return { success: true, message: `已载入工作流「${name}」（${nodes.length} 节点）` }
      }

      case 'load_workflow': {
        const filename = payload.filename as string
        if (!filename) return { success: false, error: '缺少 filename' }
        const fileWithExt = filename.endsWith('.json') ? filename : `${filename}.json`
        const res: any = await localWorkflowApi.get(fileWithExt)
        const content = res?.data?.content
        if (!content) {
          return { success: false, error: res?.error || '文件不存在或读取失败' }
        }
        useWorkflowStore.getState().loadWorkflow({
          nodes: content.nodes || [],
          edges: content.edges || [],
          name: content.name || filename,
        })
        return { success: true, message: `已载入工作流：${filename}` }
      }

      case 'save_workflow': {
        emitAssistantUiEvent('save_workflow', { filename: payload.filename })
        return { success: true, message: '已发起保存' }
      }

      case 'run_workflow': {
        emitAssistantUiEvent('run_workflow', { headless: false })
        return { success: true, message: '已发起运行（有头模式）' }
      }

      case 'run_workflow_headless': {
        emitAssistantUiEvent('run_workflow', { headless: true })
        return { success: true, message: '已发起运行（无头模式）' }
      }

      case 'stop_workflow': {
        const id = useWorkflowStore.getState().currentExecutionWorkflowId
        if (id) {
          await workflowApi.stop(id)
        }
        emitAssistantUiEvent('stop_workflow', {})
        return { success: true, message: '已发起停止' }
      }

      case 'export_workflow': {
        // payload.format: 'json' | 'playwright' | 'markdown'
        const format = (payload.format as string) || 'json'
        emitAssistantUiEvent('export_workflow', { format })
        return { success: true, message: `已发起导出（${format}）` }
      }

      // ============================================================
      // 节点操作
      // ============================================================
      case 'delete_node': {
        const nodeId = payload.node_id as string
        if (!nodeId) return { success: false, error: '缺少 node_id' }
        useWorkflowStore.getState().deleteNode(nodeId)
        return { success: true, message: `已删除节点 ${nodeId}` }
      }

      case 'delete_nodes': {
        const nodeIds = (payload.node_ids as string[]) || []
        if (!Array.isArray(nodeIds) || nodeIds.length === 0) {
          return { success: false, error: '缺少 node_ids' }
        }
        const store = useWorkflowStore.getState()
        nodeIds.forEach((id) => store.deleteNode(id))
        return { success: true, message: `已删除 ${nodeIds.length} 个节点` }
      }

      case 'update_node_config': {
        const nodeId = payload.node_id as string
        const config = (payload.config as Record<string, any>) || {}
        if (!nodeId) return { success: false, error: '缺少 node_id' }
        useWorkflowStore.getState().updateNodeData(nodeId, config as any)
        return { success: true, message: `已更新节点 ${nodeId}` }
      }

      case 'focus_node': {
        const nodeId = payload.node_id as string
        if (!nodeId) return { success: false, error: '缺少 node_id' }
        useWorkflowStore.getState().selectNode(nodeId)
        emitAssistantUiEvent('focus_node', { node_id: nodeId })
        return { success: true, message: `已聚焦节点 ${nodeId}` }
      }

      case 'toggle_node_disabled': {
        const nodeIds = (payload.node_ids as string[]) || (payload.node_id ? [payload.node_id] : [])
        if (nodeIds.length === 0) return { success: false, error: '缺少 node_ids' }
        useWorkflowStore.getState().toggleNodesDisabled(nodeIds)
        return { success: true, message: `已切换 ${nodeIds.length} 个节点的禁用状态` }
      }

      case 'align_nodes': {
        // type: 'left' | 'center' | 'right' | 'top' | 'middle' | 'bottom' | 'distribute-horizontal' | 'distribute-vertical'
        const alignType = payload.type as any
        if (!alignType) return { success: false, error: '缺少 type' }
        useWorkflowStore.getState().alignNodes(alignType)
        return { success: true, message: `已对齐：${alignType}` }
      }

      case 'copy_nodes': {
        const nodeIds = (payload.node_ids as string[]) || []
        if (nodeIds.length === 0) return { success: false, error: '缺少 node_ids' }
        useWorkflowStore.getState().copyNodes(nodeIds)
        return { success: true, message: `已复制 ${nodeIds.length} 个节点` }
      }

      case 'paste_nodes': {
        const position = payload.position as { x: number; y: number } | undefined
        useWorkflowStore.getState().pasteNodes(position)
        return { success: true, message: '已粘贴节点' }
      }

      case 'undo': {
        const s = useWorkflowStore.getState()
        if (!s.canUndo()) return { success: false, error: '没有可撤销的步骤' }
        s.undo()
        return { success: true, message: '已撤销' }
      }

      case 'redo': {
        const s = useWorkflowStore.getState()
        if (!s.canRedo()) return { success: false, error: '没有可重做的步骤' }
        s.redo()
        return { success: true, message: '已重做' }
      }

      // ============================================================
      // 工作流名称
      // ============================================================
      case 'rename_workflow': {
        const name = payload.name as string
        if (!name) return { success: false, error: '缺少 name' }
        useWorkflowStore.getState().setWorkflowNameWithHistory(name)
        return { success: true, message: `已改名为「${name}」` }
      }

      // ============================================================
      // 变量操作
      // ============================================================
      case 'add_variable': {
        const name = payload.name as string
        const value = payload.value
        const type = (payload.type as any) || 'string'
        const scope = (payload.scope as any) || 'global'
        if (!name) return { success: false, error: '缺少变量名' }
        useWorkflowStore.getState().addVariable({ name, value, type, scope })
        return { success: true, message: `已新增变量 ${name}` }
      }

      case 'update_variable': {
        const name = payload.name as string
        const value = payload.value
        if (!name) return { success: false, error: '缺少变量名' }
        useWorkflowStore.getState().updateVariable(name, value)
        return { success: true, message: `已更新变量 ${name}` }
      }

      case 'delete_variable': {
        const name = payload.name as string
        if (!name) return { success: false, error: '缺少变量名' }
        useWorkflowStore.getState().deleteVariable(name)
        return { success: true, message: `已删除变量 ${name}` }
      }

      case 'rename_variable': {
        const oldName = payload.old_name as string
        const newName = payload.new_name as string
        if (!oldName || !newName) return { success: false, error: '缺少 old_name / new_name' }
        useWorkflowStore.getState().renameVariable(oldName, newName)
        return { success: true, message: `已重命名变量：${oldName} → ${newName}` }
      }

      case 'list_variables': {
        const variables = useWorkflowStore.getState().variables
        return { success: true, data: variables }
      }

      // ============================================================
      // 日志 / 数据 / 资源
      // ============================================================
      case 'clear_logs': {
        useWorkflowStore.getState().clearLogs()
        return { success: true, message: '已清空日志' }
      }

      case 'clear_data': {
        useWorkflowStore.getState().clearCollectedData()
        return { success: true, message: '已清空数据' }
      }

      case 'set_verbose_log': {
        const enabled = !!payload.enabled
        useWorkflowStore.getState().setVerboseLog(enabled)
        return { success: true, message: enabled ? '已开启详细日志' : '已切换为简洁日志' }
      }

      case 'set_max_log_count': {
        const count = Number(payload.count)
        if (!Number.isFinite(count) || count <= 0) return { success: false, error: 'count 必须是正数' }
        useWorkflowStore.getState().setMaxLogCount(count)
        return { success: true, message: `日志最大条数：${count}` }
      }

      case 'export_logs': {
        emitAssistantUiEvent('export_logs', {})
        return { success: true, message: '已发起日志下载' }
      }

      case 'download_data': {
        emitAssistantUiEvent('download_data', {})
        return { success: true, message: '已发起数据下载' }
      }

      case 'upload_excel': {
        emitAssistantUiEvent('upload_excel', {})
        return { success: true, message: '已触发 Excel 上传文件选择' }
      }

      case 'upload_image': {
        emitAssistantUiEvent('upload_image', {})
        return { success: true, message: '已触发图像上传文件选择' }
      }

      // ============================================================
      // 底栏 Tab / 全局界面切换
      // ============================================================
      case 'switch_bottom_panel': {
        const tab = payload.tab as any
        if (!tab) return { success: false, error: '缺少 tab' }
        useWorkflowStore.getState().setBottomPanelTab(tab)
        return { success: true, message: `已切换到 ${tab} 面板` }
      }

      // ============================================================
      // 工作流详情查询
      // ============================================================
      case 'get_workflow_detail': {
        const s = useWorkflowStore.getState()
        return {
          success: true,
          data: {
            name: s.name,
            nodes: s.nodes.map((n) => ({
              id: n.id,
              type: n.type,
              position: n.position,
              data: n.data,
            })),
            edges: s.edges,
            variables: s.variables,
            executionStatus: s.executionStatus,
            currentExecutionWorkflowId: s.currentExecutionWorkflowId,
            hasUnsavedChanges: s.hasUnsavedChanges,
          },
        }
      }

      case 'get_logs': {
        const s = useWorkflowStore.getState()
        const limit = Math.max(1, Math.min(500, Number(payload.limit) || 100))
        return {
          success: true,
          data: s.logs.slice(-limit),
        }
      }

      case 'get_collected_data': {
        const s = useWorkflowStore.getState()
        return {
          success: true,
          data: s.collectedData,
        }
      }

      // ============================================================
      // 全局配置（读 + 写）
      // ============================================================
      case 'get_global_config': {
        const cfg = useGlobalConfigStore.getState().config
        return { success: true, data: cfg }
      }

      case 'update_global_config': {
        const section = payload.section as string
        const values = (payload.values as Record<string, any>) || {}
        const cfgStore = useGlobalConfigStore.getState() as any
        const updateMap: Record<string, string> = {
          system: 'updateSystemConfig',
          ai: 'updateAIConfig',
          aiAssistant: 'updateAIAssistantConfig',
          aiScraper: 'updateAIScraperConfig',
          email: 'updateEmailConfig',
          emailTrigger: 'updateEmailTriggerConfig',
          apiTrigger: 'updateApiTriggerConfig',
          fileTrigger: 'updateFileTriggerConfig',
          workflow: 'updateWorkflowConfig',
          database: 'updateDatabaseConfig',
          qq: 'updateQQConfig',
          feishu: 'updateFeishuConfig',
          display: 'updateDisplayConfig',
          browser: 'updateBrowserConfig',
        }
        const fnName = updateMap[section]
        if (!fnName || typeof cfgStore[fnName] !== 'function') {
          return { success: false, error: `未知配置段：${section}` }
        }
        cfgStore[fnName](values)
        return { success: true, message: `已更新配置 ${section}` }
      }

      // ============================================================
      // 弹窗 / 面板 打开/关闭
      // ============================================================
      case 'open_global_config':
        emitAssistantUiEvent('open_global_config', payload)
        return { success: true, message: '已打开全局配置' }

      case 'close_global_config':
        emitAssistantUiEvent('close_global_config', payload)
        return { success: true, message: '已关闭全局配置' }

      case 'open_local_workflow_dialog':
        emitAssistantUiEvent('open_local_workflow', payload)
        return { success: true, message: '已打开本地工作流对话框' }

      case 'close_local_workflow_dialog':
        emitAssistantUiEvent('close_local_workflow', payload)
        return { success: true, message: '已关闭本地工作流对话框' }

      case 'open_scheduled_tasks':
        emitAssistantUiEvent('open_scheduled_tasks', payload)
        return { success: true, message: '已打开计划任务面板' }

      case 'close_scheduled_tasks':
        emitAssistantUiEvent('close_scheduled_tasks', payload)
        return { success: true, message: '已关闭计划任务面板' }

      case 'open_documentation':
        emitAssistantUiEvent('open_documentation', payload)
        return { success: true, message: '已打开使用文档' }

      case 'close_documentation':
        emitAssistantUiEvent('close_documentation', payload)
        return { success: true, message: '已关闭使用文档' }

      case 'open_workflow_hub':
        emitAssistantUiEvent('open_workflow_hub', payload)
        return { success: true, message: '已打开工作流仓库' }

      case 'close_workflow_hub':
        emitAssistantUiEvent('close_workflow_hub', payload)
        return { success: true, message: '已关闭工作流仓库' }

      case 'open_auto_browser':
        emitAssistantUiEvent('open_auto_browser', payload)
        return { success: true, message: '已打开自动化浏览器对话框' }

      case 'close_auto_browser':
        emitAssistantUiEvent('close_auto_browser', payload)
        return { success: true, message: '已关闭自动化浏览器对话框' }

      case 'open_phone_mirror':
        emitAssistantUiEvent('open_phone_mirror', payload)
        return { success: true, message: '已打开手机投屏' }

      case 'close_phone_mirror':
        emitAssistantUiEvent('close_phone_mirror', payload)
        return { success: true, message: '已关闭手机投屏' }

      case 'open_variable_tracking':
        emitAssistantUiEvent('open_variable_tracking', payload)
        return { success: true, message: '已打开变量追踪面板' }

      case 'close_variable_tracking':
        emitAssistantUiEvent('close_variable_tracking', payload)
        return { success: true, message: '已关闭变量追踪面板' }

      case 'open_export_dialog':
        emitAssistantUiEvent('open_export_dialog', payload)
        return { success: true, message: '已打开导出对话框' }

      case 'open_module_search':
        emitAssistantUiEvent('open_module_search', payload)
        return { success: true, message: '已打开画布模块搜索框' }

      case 'take_screenshot':
        emitAssistantUiEvent('take_screenshot', payload)
        return { success: true, message: '已发起截图' }

      // ============================================================
      // 通知 / 提示
      // ============================================================
      case 'show_toast':
        emitAssistantUiEvent('show_toast', payload)
        return { success: true, message: '已显示提示' }

      case 'add_log': {
        const level = (payload.level as any) || 'info'
        const message = (payload.message as string) || ''
        useWorkflowStore.getState().addLog({ level, message })
        return { success: true, message: '已添加日志' }
      }

      default:
        return { success: false, error: `未知 action：${action}` }
    }
  } catch (err) {
    return {
      success: false,
      error: err instanceof Error ? err.message : String(err),
    }
  }
}

/**
 * 把当前工作流的轻量上下文打包，发给后端给 LLM 看
 */
export function buildWorkflowContext() {
  const s = useWorkflowStore.getState()
  return {
    name: s.name,
    nodes: s.nodes.map((n) => ({
      id: n.id,
      type: n.type,
      position: n.position,
      data: { label: (n.data as any)?.label, moduleType: (n.data as any)?.moduleType },
    })),
    edges: s.edges.map((e) => ({ id: e.id, source: e.source, target: e.target })),
    variables: s.variables,
    currentExecutionWorkflowId: s.currentExecutionWorkflowId,
    executionStatus: s.executionStatus,
    bottomPanelTab: s.bottomPanelTab,
    hasUnsavedChanges: s.hasUnsavedChanges,
  }
}

/**
 * 监听 socket 推送的 ai_assistant 事件并更新 store
 */
let bound = false
export function bindAssistantSocketEvents(handlers: {
  onToolCall?: (data: any) => void
  onToolResult?: (data: any) => void
  onAssistantPartial?: (data: any) => void
}) {
  if (bound) return
  bound = true
  socketService.on('ai_assistant:tool_call', (data) => handlers.onToolCall?.(data))
  socketService.on('ai_assistant:tool_result', (data) => handlers.onToolResult?.(data))
  socketService.on('ai_assistant:assistant_partial', (data) => handlers.onAssistantPartial?.(data))
}
