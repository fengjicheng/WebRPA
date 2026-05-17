/**
 * 前端 Skills 派发器
 *
 * 当后端 AI 助手返回 client_action 工具调用时，由这个文件负责实际操作 WebRPA。
 * 它会从 zustand store 中拿到当前 workflow 状态、并直接调用 store 的 actions。
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
 * 跨组件通信：让外部 UI 组件（GlobalConfigDialog、Toolbar 等）订阅事件来响应小助手的指令
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
      // === 画布操作 ===
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
        const existingNodes = store.nodes
        const existingEdges = store.edges
        // 把后端给的简单节点结构转成画布节点（带 data.label/moduleType）
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
          nodes: [...existingNodes, ...xyNodes] as any,
          edges: [...existingEdges, ...xyEdges] as any,
          name: store.name,
        })
        return { success: true, message: `已添加 ${xyNodes.length} 个节点` }
      }

      case 'load_workflow_from_data': {
        // 直接载入完整的 nodes/edges/name（小助手生成完整工作流时使用）
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
        // 触发 UI 上的保存动作（让用户看到保存进度）
        emitAssistantUiEvent('save_workflow', { filename: payload.filename })
        return { success: true, message: '已发起保存' }
      }

      case 'run_workflow': {
        emitAssistantUiEvent('run_workflow', {})
        return { success: true, message: '已发起运行' }
      }

      case 'stop_workflow': {
        const id = useWorkflowStore.getState().currentExecutionWorkflowId
        if (id) {
          await workflowApi.stop(id)
        }
        emitAssistantUiEvent('stop_workflow', {})
        return { success: true, message: '已发起停止' }
      }

      case 'delete_node': {
        const nodeId = payload.node_id as string
        if (!nodeId) return { success: false, error: '缺少 node_id' }
        useWorkflowStore.getState().deleteNode(nodeId)
        return { success: true, message: `已删除节点 ${nodeId}` }
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

      // === 全局配置 ===
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

      case 'open_global_config':
        emitAssistantUiEvent('open_global_config', payload)
        return { success: true, message: '已打开全局配置' }

      case 'open_local_workflow_dialog':
        emitAssistantUiEvent('open_local_workflow', payload)
        return { success: true, message: '已打开本地工作流对话框' }

      case 'open_scheduled_tasks':
        emitAssistantUiEvent('open_scheduled_tasks', payload)
        return { success: true, message: '已打开计划任务面板' }

      case 'open_documentation':
        emitAssistantUiEvent('open_documentation', payload)
        return { success: true, message: '已打开使用文档' }

      case 'show_toast':
        emitAssistantUiEvent('show_toast', payload)
        return { success: true, message: '已显示提示' }

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
