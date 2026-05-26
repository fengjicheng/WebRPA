/**
 * 前端 Skills 派发器
 *
 * 当后端 AI 助手返回 client_action 工具调用时，由这个文件负责实际操作 WebRPA。
 * 它会从 zustand store 中拿到当前 workflow 状态、并直接调用 store 的 actions。
 *
 * 设计原则：把所有用户能在 UI 上做的事都暴露成 action，
 * 让小助手具有完全的前端操作能力。
 */
import { useWorkflowStore, moduleTypeLabels } from '@/store/workflowStore'
import { useGlobalConfigStore } from '@/store/globalConfigStore'
import { localWorkflowApi, workflowApi, screensaverApi, dataAssetApi, imageAssetApi, scheduledTaskApi } from '@/services/api'
import { socketService } from '@/services/socket'

/**
 * 把 AI 助手生成的节点（type 是 module_type 例如 'open_page'/'note'/'group'）
 * 转换为 React Flow 内部需要的节点结构（type 是 'moduleNode'/'noteNode'/'groupNode'）
 */
function convertAiNodeToReactFlow(n: any): any {
  const businessType = (n.type ?? n.data?.moduleType) as string
  let frontendType: string

  // 已经是前端格式直接保留
  if (
    businessType === 'moduleNode' ||
    businessType === 'noteNode' ||
    businessType === 'groupNode' ||
    businessType === 'subflowHeaderNode'
  ) {
    frontendType = businessType
  } else if (businessType === 'note') {
    frontendType = 'noteNode'
  } else if (businessType === 'group') {
    frontendType = 'groupNode'
  } else if (businessType === 'subflow_header') {
    frontendType = 'subflowHeaderNode'
  } else {
    frontendType = 'moduleNode'
  }

  // 基础数据：label / moduleType / 其他配置字段都展开到 data
  const moduleType = n.data?.moduleType ?? businessType
  // 模块原名（中文）：永远用 moduleTypeLabels 查表，不接受 AI 改 label
  let officialLabel = ''
  if (frontendType === 'moduleNode' && moduleType) {
    officialLabel = (moduleTypeLabels as Record<string, string>)[moduleType] || moduleType
  }
  // AI 传的 label 实际是它想给节点起的名字，应当落到 name（节点备注）字段
  // 这样画布显示：「<官方模块名> (<AI 给的名字>)」
  const aiCustomName = n.data?.label && n.data.label !== officialLabel ? n.data.label : undefined
  const baseData: Record<string, any> = {
    label: officialLabel,
    moduleType,
  }
  if (aiCustomName && !n.data?.name && !n.data?.remark) {
    baseData.name = aiCustomName
  }
  // 把 data 里其它字段（remark/comment/content/config 等）合并展开
  if (n.data && typeof n.data === 'object') {
    for (const [k, v] of Object.entries(n.data)) {
      if (k === 'config' && v && typeof v === 'object') {
        // 兼容旧风格：把 config 内字段展平到 data 顶层
        Object.assign(baseData, v)
      } else if (k !== 'label' && k !== 'moduleType') {
        baseData[k] = v
      }
    }
  }
  // 双保险：合并完后强制还原模块原名，绝不接受 AI 改 label
  // （即便 config 子对象里也写了 label，也会被这一步覆盖回来）
  if (frontendType === 'moduleNode' && officialLabel) {
    baseData.label = officialLabel
  }

  // 便签 / 分组节点的样式（默认尺寸，AI 没传时给个合理默认）
  let style: Record<string, any> | undefined = n.style
  if (frontendType === 'noteNode') {
    // 根据内容长度自动算合适的便签尺寸（避免 AI 不调整尺寸导致文本溢出）
    const content = String(baseData.content ?? n.data?.content ?? '')
    const fontSize = Number(baseData.fontSize ?? n.data?.fontSize ?? 13)
    // 计算每行近似字符数：宽度 / 字号 ≈ 字符数（中文每字符 ~1 字号宽，英文 ~0.55 字号宽）
    // 用 280 当默认宽度做基准
    const targetWidth = 280
    const charsPerLine = Math.floor(targetWidth / (fontSize * 0.95))
    // 把显式换行符 + 自动换行都计入行数
    const explicitLines = content.split(/\r?\n/)
    const totalLines = explicitLines.reduce((sum, line) => {
      // 中文字符按 1 算，英文/数字按 0.55 算（粗略）
      let visualWidth = 0
      for (const ch of line) {
        visualWidth += /[\u4e00-\u9fa5\u3000-\u303f\uff00-\uffef]/.test(ch) ? 1 : 0.55
      }
      return sum + Math.max(1, Math.ceil(visualWidth / charsPerLine))
    }, 0)
    // 行高 ≈ 字号 * 1.5；外边距上下各 16px
    const calcHeight = Math.max(70, totalLines * fontSize * 1.5 + 32)
    style = {
      width: targetWidth,
      height: Math.min(800, calcHeight),
      ...(n.style || {}),
    }
    // 便签默认黄色
    if (!baseData.color) baseData.color = '#fef08a'
  } else if (frontendType === 'groupNode') {
    style = { width: 360, height: 240, ...(n.style || {}) }
    if (!baseData.color) baseData.color = '#3b82f6'
  }

  return {
    id: n.id,
    type: frontendType,
    position: n.position || { x: 200, y: 200 },
    data: baseData,
    ...(style ? { style } : {}),
    // 便签 / 分组放在底层
    ...(frontendType === 'noteNode' || frontendType === 'groupNode' ? { zIndex: -1 } : {}),
  }
}

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
        const xyNodes = nodes.map(convertAiNodeToReactFlow)
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
        const xyNodes = nodes.map(convertAiNodeToReactFlow)
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
        // 保护：label 是模块原名，AI 不允许通过 update_node_config 修改它
        // 如果 AI 想改"显示名"，应该改 name（节点备注）字段
        if ('label' in config) {
          const labelVal = config.label
          delete config.label
          // 如果当前没有 name/remark，把 AI 传的 label 当作备注落到 name
          if (labelVal && !('name' in config) && !('remark' in config)) {
            config.name = labelVal
          }
        }
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

      case 'move_node': {
        const nodeId = payload.node_id as string
        const x = Number(payload.x)
        const y = Number(payload.y)
        if (!nodeId) return { success: false, error: '缺少 node_id' }
        if (!Number.isFinite(x) || !Number.isFinite(y)) return { success: false, error: '坐标必须为数字' }
        const s = useWorkflowStore.getState()
        const exists = s.nodes.some((n: any) => n.id === nodeId)
        if (!exists) return { success: false, error: `节点 ${nodeId} 不存在` }
        useWorkflowStore.setState({
          nodes: s.nodes.map((n: any) => (n.id === nodeId ? { ...n, position: { x, y } } : n)),
        } as any)
        return { success: true, message: `已将节点 ${nodeId} 移到 (${x}, ${y})` }
      }

      case 'rename_node': {
        const nodeId = payload.node_id as string
        // 兼容 AI 可能传 label / name / remark 任一字段：实际都写到 name（节点备注）
        const newName = (payload.name as string) ?? (payload.remark as string) ?? (payload.label as string)
        if (!nodeId) return { success: false, error: '缺少 node_id' }
        if (!newName) return { success: false, error: '缺少 name（节点备注）' }
        // 关键：不能动 label（label 是模块原名），只改 name 这个备注字段
        useWorkflowStore.getState().updateNodeData(nodeId, { name: newName } as any)
        return { success: true, message: `已重命名节点 ${nodeId} → ${newName}（备注）` }
      }

      case 'find_nodes_by_type': {
        const type = payload.type as string
        if (!type) return { success: false, error: '缺少 type' }
        const matches = useWorkflowStore.getState().nodes.filter((n: any) => n.type === type)
        return {
          success: true,
          data: matches.map((n: any) => ({ id: n.id, type: n.type, label: n.data?.label, position: n.position })),
        }
      }

      case 'connect_nodes': {
        const source = payload.source as string
        const target = payload.target as string
        if (!source || !target) return { success: false, error: '缺少 source / target' }
        const s = useWorkflowStore.getState()
        const sourceExists = s.nodes.some((n: any) => n.id === source)
        const targetExists = s.nodes.some((n: any) => n.id === target)
        if (!sourceExists || !targetExists) return { success: false, error: '节点不存在' }
        const newEdge = {
          id: `e-${source}-${target}-${Date.now().toString(36)}`,
          source,
          target,
          sourceHandle: payload.source_handle || undefined,
          targetHandle: payload.target_handle || undefined,
        }
        useWorkflowStore.setState({ edges: [...s.edges, newEdge] } as any)
        return { success: true, message: `已连接 ${source} → ${target}`, data: newEdge }
      }

      case 'disconnect_edge': {
        const edgeId = payload.edge_id as string
        if (!edgeId) return { success: false, error: '缺少 edge_id' }
        const s = useWorkflowStore.getState()
        const remaining = s.edges.filter((e: any) => e.id !== edgeId)
        if (remaining.length === s.edges.length) return { success: false, error: '该连线不存在' }
        useWorkflowStore.setState({ edges: remaining } as any)
        return { success: true, message: `已删除连线 ${edgeId}` }
      }

      case 'select_all_nodes': {
        const s = useWorkflowStore.getState()
        useWorkflowStore.setState({
          nodes: s.nodes.map((n: any) => ({ ...n, selected: true })),
        } as any)
        return { success: true, message: `已选中 ${s.nodes.length} 个节点` }
      }

      case 'clear_selection': {
        const s = useWorkflowStore.getState()
        useWorkflowStore.setState({
          nodes: s.nodes.map((n: any) => ({ ...n, selected: false })),
          selectedNodeId: null,
        } as any)
        return { success: true, message: '已取消选中' }
      }

      case 'fit_view': {
        emitAssistantUiEvent('fit_view', payload)
        return { success: true, message: '已请求适配视图' }
      }

      case 'run_single_node': {
        const nodeId = payload.node_id as string
        if (!nodeId) return { success: false, error: '缺少 node_id' }
        emitAssistantUiEvent('run_single_node', { node_id: nodeId })
        return { success: true, message: `已请求单节点运行：${nodeId}` }
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
      // 数据表格底栏 - 行/列/单元格细粒度操作
      // ============================================================
      case 'add_data_row': {
        // 添加一行：payload.row 是 {col1: val1, col2: val2, ...} 字典；不传则添加空行
        const row = (payload.row as Record<string, unknown>) || {}
        const s = useWorkflowStore.getState()
        // 没传完整列时，用现有数据的列名补齐空字符串
        if (s.collectedData.length > 0) {
          const cols = Object.keys(s.collectedData[0])
          for (const c of cols) if (!(c in row)) row[c] = ''
        }
        s.addDataRow(row as any)
        return { success: true, message: '已添加一行', data: { rowCount: s.collectedData.length + 1 } }
      }

      case 'add_data_column': {
        // 添加一列：payload.column='列名', payload.default=默认值（可选，默认空字符串）
        const column = payload.column as string
        const defaultValue = payload.default ?? ''
        if (!column) return { success: false, error: '缺少 column' }
        const s = useWorkflowStore.getState()
        const newData = s.collectedData.map((r) => ({ ...r, [column]: (r as any)[column] ?? defaultValue }))
        s.setCollectedData(newData as any)
        return { success: true, message: `已添加列「${column}」` }
      }

      case 'delete_data_row': {
        const index = Number(payload.index)
        if (!Number.isFinite(index) || index < 0) return { success: false, error: 'index 必须是非负整数' }
        useWorkflowStore.getState().deleteDataRow(index)
        return { success: true, message: `已删除第 ${index + 1} 行` }
      }

      case 'delete_data_column': {
        const column = payload.column as string
        if (!column) return { success: false, error: '缺少 column' }
        const s = useWorkflowStore.getState()
        const newData = s.collectedData.map((r) => {
          const copy = { ...r }
          delete (copy as any)[column]
          return copy
        })
        s.setCollectedData(newData as any)
        return { success: true, message: `已删除列「${column}」` }
      }

      case 'set_data_cell': {
        // payload.row_index, payload.column, payload.value
        const rowIndex = Number(payload.row_index)
        const column = payload.column as string
        if (!Number.isFinite(rowIndex) || !column) return { success: false, error: '缺少 row_index 或 column' }
        const s = useWorkflowStore.getState()
        if (rowIndex < 0 || rowIndex >= s.collectedData.length) {
          return { success: false, error: `row_index 越界（0..${s.collectedData.length - 1}）` }
        }
        const newRow = { ...s.collectedData[rowIndex], [column]: payload.value }
        s.updateDataRow(rowIndex, newRow as any)
        return { success: true, message: `已更新单元格 [${rowIndex}][${column}]` }
      }

      // ============================================================
      // Excel 资源底栏（数据资产）
      // ============================================================
      case 'list_data_assets': {
        try {
          const res = await dataAssetApi.list()
          return { success: true, data: res?.data ?? res }
        } catch (e: any) {
          return { success: false, error: e?.message || String(e) }
        }
      }

      case 'delete_data_asset': {
        const id = payload.id as string
        if (!id) return { success: false, error: '缺少 id' }
        try {
          await dataAssetApi.delete(id)
          // 同步前端 store
          useWorkflowStore.getState().deleteDataAsset(id)
          return { success: true, message: `已删除 Excel 资源 ${id}` }
        } catch (e: any) {
          return { success: false, error: e?.message || String(e) }
        }
      }

      case 'rename_data_asset': {
        const id = payload.id as string
        const newName = payload.new_name as string
        if (!id || !newName) return { success: false, error: '缺少 id 或 new_name' }
        try {
          await dataAssetApi.rename(id, newName)
          return { success: true, message: `已重命名 Excel 资源 ${id} → ${newName}` }
        } catch (e: any) {
          return { success: false, error: e?.message || String(e) }
        }
      }

      case 'preview_data_asset': {
        // payload.id, payload.sheet?, payload.max_rows?, payload.max_cols?
        const id = payload.id as string
        if (!id) return { success: false, error: '缺少 id' }
        try {
          const sheet = payload.sheet as string | undefined
          const res = await dataAssetApi.preview(
            id,
            sheet,
            Number(payload.max_rows) || undefined,
            Number(payload.max_cols) || undefined
          )
          return { success: true, data: res?.data ?? res }
        } catch (e: any) {
          return { success: false, error: e?.message || String(e) }
        }
      }

      case 'get_data_asset_sheets': {
        const id = payload.id as string
        if (!id) return { success: false, error: '缺少 id' }
        try {
          const res = await dataAssetApi.getSheets(id)
          return { success: true, data: res?.data ?? res }
        } catch (e: any) {
          return { success: false, error: e?.message || String(e) }
        }
      }

      // ============================================================
      // 图像资源底栏
      // ============================================================
      case 'list_image_assets': {
        try {
          const res = await imageAssetApi.list()
          return { success: true, data: res?.data ?? res }
        } catch (e: any) {
          return { success: false, error: e?.message || String(e) }
        }
      }

      case 'delete_image_asset': {
        const id = payload.id as string
        if (!id) return { success: false, error: '缺少 id' }
        try {
          await imageAssetApi.delete(id)
          useWorkflowStore.getState().deleteImageAsset(id)
          return { success: true, message: `已删除图像资源 ${id}` }
        } catch (e: any) {
          return { success: false, error: e?.message || String(e) }
        }
      }

      case 'rename_image_asset': {
        const id = payload.id as string
        const newName = payload.new_name as string
        if (!id || !newName) return { success: false, error: '缺少 id 或 new_name' }
        try {
          await imageAssetApi.rename(id, newName)
          return { success: true, message: `已重命名图像资源 ${id} → ${newName}` }
        } catch (e: any) {
          return { success: false, error: e?.message || String(e) }
        }
      }

      // ============================================================
      // 全局变量底栏 - 批量/汇总操作
      // ============================================================
      case 'clear_variables': {
        const s = useWorkflowStore.getState()
        const names = s.variables.map((v) => v.name)
        for (const n of names) s.deleteVariable(n)
        return { success: true, message: `已清空 ${names.length} 个变量` }
      }

      case 'get_variable': {
        const name = payload.name as string
        if (!name) return { success: false, error: '缺少 name' }
        const v = useWorkflowStore.getState().variables.find((x) => x.name === name)
        if (!v) return { success: false, error: `变量 ${name} 不存在` }
        return { success: true, data: v }
      }

      case 'change_variable_type': {
        // payload.name, payload.type='string'|'number'|'boolean'|'array'|'object', payload.value?
        const name = payload.name as string
        const newType = payload.type as string
        if (!name || !newType) return { success: false, error: '缺少 name 或 type' }
        const s = useWorkflowStore.getState()
        const v = s.variables.find((x) => x.name === name)
        if (!v) return { success: false, error: `变量 ${name} 不存在` }
        // 删除旧的，加入新的（同名）
        s.deleteVariable(name)
        s.addVariable({
          name,
          value: payload.value ?? v.value,
          type: newType as any,
          scope: v.scope,
        })
        return { success: true, message: `已修改变量 ${name} 的类型为 ${newType}` }
      }

      // ============================================================
      // 本地工作流（指定路径打开/保存/删除/列出）
      // ============================================================
      case 'list_local_workflows': {
        try {
          const folder = payload.folder as string | undefined
          const res: any = await localWorkflowApi.list(folder)
          return { success: true, data: res?.data ?? res }
        } catch (e: any) {
          return { success: false, error: e?.message || String(e) }
        }
      }

      case 'get_local_workflow_content': {
        const filename = payload.filename as string
        if (!filename) return { success: false, error: '缺少 filename' }
        try {
          const fileWithExt = filename.endsWith('.json') ? filename : `${filename}.json`
          const res: any = await localWorkflowApi.get(fileWithExt)
          return { success: true, data: res?.data ?? res }
        } catch (e: any) {
          return { success: false, error: e?.message || String(e) }
        }
      }

      case 'delete_local_workflow': {
        const filename = payload.filename as string
        if (!filename) return { success: false, error: '缺少 filename' }
        try {
          const fileWithExt = filename.endsWith('.json') ? filename : `${filename}.json`
          await localWorkflowApi.delete(fileWithExt)
          return { success: true, message: `已删除本地工作流 ${filename}` }
        } catch (e: any) {
          return { success: false, error: e?.message || String(e) }
        }
      }

      case 'save_workflow_to_folder': {
        // 把当前画布工作流保存到指定文件名（不弹对话框）
        const filename = (payload.filename as string) || ''
        if (!filename) return { success: false, error: '缺少 filename' }
        try {
          const s = useWorkflowStore.getState()
          const data = {
            filename: filename.endsWith('.json') ? filename : `${filename}.json`,
            content: {
              name: s.name || filename,
              nodes: s.nodes,
              edges: s.edges,
              variables: s.variables,
            },
          }
          await localWorkflowApi.save(data)
          return { success: true, message: `已保存到 ${data.filename}` }
        } catch (e: any) {
          return { success: false, error: e?.message || String(e) }
        }
      }

      case 'get_local_workflow_default_folder': {
        try {
          const res: any = await localWorkflowApi.getDefaultFolder()
          return { success: true, data: res?.data ?? res }
        } catch (e: any) {
          return { success: false, error: e?.message || String(e) }
        }
      }

      // ============================================================
      // 工作流仓库（远程 Hub）
      // ============================================================
      case 'hub_list_workflows': {
        // payload.keyword?, payload.category?, payload.page?(1), payload.limit?(20), payload.sort_by?(latest|popular|hot)
        try {
          const hubUrl = (typeof window !== 'undefined' && (window.localStorage?.getItem('workflow_hub_url') || '')) || 'https://hub.pmhs.top'
          const params = new URLSearchParams()
          if (payload.keyword) params.set('keyword', String(payload.keyword))
          if (payload.category) params.set('category', String(payload.category))
          if (payload.page) params.set('page', String(payload.page))
          if (payload.limit) params.set('limit', String(payload.limit))
          if (payload.sort_by) params.set('sort_by', String(payload.sort_by))
          const resp = await fetch(`${hubUrl}/api/workflows?${params}`)
          if (!resp.ok) return { success: false, error: `Hub 返回 ${resp.status}` }
          const data = await resp.json()
          return { success: true, data }
        } catch (e: any) {
          return { success: false, error: e?.message || String(e) }
        }
      }

      case 'hub_get_categories': {
        try {
          const hubUrl = (typeof window !== 'undefined' && (window.localStorage?.getItem('workflow_hub_url') || '')) || 'https://hub.pmhs.top'
          const resp = await fetch(`${hubUrl}/api/workflows/categories`)
          if (!resp.ok) return { success: false, error: `Hub 返回 ${resp.status}` }
          const data = await resp.json()
          return { success: true, data }
        } catch (e: any) {
          return { success: false, error: e?.message || String(e) }
        }
      }

      case 'hub_download_workflow': {
        // 下载 hub 上的一个工作流并直接装入画布
        const workflowId = payload.workflow_id as string
        if (!workflowId) return { success: false, error: '缺少 workflow_id' }
        try {
          const hubUrl = (typeof window !== 'undefined' && (window.localStorage?.getItem('workflow_hub_url') || '')) || 'https://hub.pmhs.top'
          const resp = await fetch(`${hubUrl}/api/workflows/${workflowId}/download`, { method: 'POST' })
          if (!resp.ok) return { success: false, error: `Hub 返回 ${resp.status}` }
          const data = await resp.json()
          const wf = data?.workflow || data
          if (!wf?.nodes) return { success: false, error: 'Hub 返回格式异常' }
          if (payload.load_into_canvas !== false) {
            useWorkflowStore.getState().loadWorkflow({
              nodes: wf.nodes || [],
              edges: wf.edges || [],
              name: wf.name || workflowId,
            })
          }
          return { success: true, message: `已下载并装入：${wf.name || workflowId}`, data: wf }
        } catch (e: any) {
          return { success: false, error: e?.message || String(e) }
        }
      }

      case 'hub_publish_workflow': {
        // 把当前画布发布到 hub。payload: name?, description?, category?, tags?, author?
        try {
          const hubUrl = (typeof window !== 'undefined' && (window.localStorage?.getItem('workflow_hub_url') || '')) || 'https://hub.pmhs.top'
          const s = useWorkflowStore.getState()
          const body = {
            name: (payload.name as string) || s.name || '未命名工作流',
            description: payload.description || '',
            category: payload.category || '其他',
            tags: payload.tags || [],
            author: payload.author || '匿名',
            workflow: {
              nodes: s.nodes,
              edges: s.edges,
              variables: s.variables,
            },
            clientId: (typeof window !== 'undefined' && (window.localStorage?.getItem('webrpa.clientId') || '')) || '',
          }
          const resp = await fetch(`${hubUrl}/api/workflows`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
          })
          if (!resp.ok) return { success: false, error: `Hub 返回 ${resp.status}` }
          const data = await resp.json()
          return { success: true, message: `已发布到工作流仓库：${body.name}`, data }
        } catch (e: any) {
          return { success: false, error: e?.message || String(e) }
        }
      }

      case 'hub_get_my_workflows': {
        try {
          const hubUrl = (typeof window !== 'undefined' && (window.localStorage?.getItem('workflow_hub_url') || '')) || 'https://hub.pmhs.top'
          const clientId = (typeof window !== 'undefined' && (window.localStorage?.getItem('webrpa.clientId') || '')) || ''
          const resp = await fetch(`${hubUrl}/api/workflows/my-workflows`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ clientId }),
          })
          if (!resp.ok) return { success: false, error: `Hub 返回 ${resp.status}` }
          const data = await resp.json()
          return { success: true, data }
        } catch (e: any) {
          return { success: false, error: e?.message || String(e) }
        }
      }

      case 'hub_delete_my_workflow': {
        const workflowId = payload.workflow_id as string
        if (!workflowId) return { success: false, error: '缺少 workflow_id' }
        try {
          const hubUrl = (typeof window !== 'undefined' && (window.localStorage?.getItem('workflow_hub_url') || '')) || 'https://hub.pmhs.top'
          const clientId = (typeof window !== 'undefined' && (window.localStorage?.getItem('webrpa.clientId') || '')) || ''
          const resp = await fetch(`${hubUrl}/api/workflows/${workflowId}`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ clientId }),
          })
          if (!resp.ok) return { success: false, error: `Hub 返回 ${resp.status}` }
          return { success: true, message: `已从 hub 删除工作流 ${workflowId}` }
        } catch (e: any) {
          return { success: false, error: e?.message || String(e) }
        }
      }

      // ============================================================
      // 计划任务（完整 CRUD + 启停 + 日志）
      // ============================================================
      case 'list_scheduled_tasks_full': {
        try {
          const res: any = await scheduledTaskApi.list()
          return { success: true, data: res?.data ?? res }
        } catch (e: any) {
          return { success: false, error: e?.message || String(e) }
        }
      }

      case 'get_scheduled_task_detail': {
        const id = payload.id as string
        if (!id) return { success: false, error: '缺少 id' }
        try {
          const res: any = await scheduledTaskApi.get(id)
          return { success: true, data: res?.data ?? res }
        } catch (e: any) {
          return { success: false, error: e?.message || String(e) }
        }
      }

      case 'create_scheduled_task': {
        // payload 直接传后端要的 task 对象
        try {
          const res: any = await scheduledTaskApi.create(payload || {})
          return { success: true, message: '已创建计划任务', data: res?.data ?? res }
        } catch (e: any) {
          return { success: false, error: e?.message || String(e) }
        }
      }

      case 'update_scheduled_task': {
        const id = payload.id as string
        if (!id) return { success: false, error: '缺少 id' }
        try {
          const data = { ...payload }
          delete (data as any).id
          const res: any = await scheduledTaskApi.update(id, data)
          return { success: true, message: `已更新计划任务 ${id}`, data: res?.data ?? res }
        } catch (e: any) {
          return { success: false, error: e?.message || String(e) }
        }
      }

      case 'delete_scheduled_task': {
        const id = payload.id as string
        if (!id) return { success: false, error: '缺少 id' }
        try {
          await scheduledTaskApi.delete(id)
          return { success: true, message: `已删除计划任务 ${id}` }
        } catch (e: any) {
          return { success: false, error: e?.message || String(e) }
        }
      }

      case 'toggle_scheduled_task': {
        const id = payload.id as string
        if (!id) return { success: false, error: '缺少 id' }
        const enabled = !!payload.enabled
        try {
          await scheduledTaskApi.toggle(id, enabled)
          return { success: true, message: `计划任务 ${id} 已${enabled ? '启用' : '禁用'}` }
        } catch (e: any) {
          return { success: false, error: e?.message || String(e) }
        }
      }

      case 'execute_scheduled_task': {
        const id = payload.id as string
        if (!id) return { success: false, error: '缺少 id' }
        try {
          await scheduledTaskApi.execute(id)
          return { success: true, message: `已立即执行计划任务 ${id}` }
        } catch (e: any) {
          return { success: false, error: e?.message || String(e) }
        }
      }

      case 'stop_scheduled_task': {
        const id = payload.id as string
        if (!id) return { success: false, error: '缺少 id' }
        try {
          await scheduledTaskApi.stop(id)
          return { success: true, message: `已停止计划任务 ${id}` }
        } catch (e: any) {
          return { success: false, error: e?.message || String(e) }
        }
      }

      case 'get_scheduled_task_logs': {
        const id = payload.id as string
        const limit = Number(payload.limit) || 100
        try {
          const res: any = id
            ? await scheduledTaskApi.getTaskLogs(id, limit)
            : await scheduledTaskApi.getAllLogs(limit)
          return { success: true, data: res?.data ?? res }
        } catch (e: any) {
          return { success: false, error: e?.message || String(e) }
        }
      }

      case 'clear_scheduled_task_logs': {
        const id = payload.id as string
        try {
          if (id) await scheduledTaskApi.clearTaskLogs(id)
          else await scheduledTaskApi.clearAllLogs()
          return { success: true, message: id ? `已清空任务 ${id} 的日志` : '已清空所有计划任务日志' }
        } catch (e: any) {
          return { success: false, error: e?.message || String(e) }
        }
      }

      case 'get_scheduled_task_statistics': {
        try {
          const res: any = await scheduledTaskApi.getStatistics()
          return { success: true, data: res?.data ?? res }
        } catch (e: any) {
          return { success: false, error: e?.message || String(e) }
        }
      }

      // ============================================================
      // 全局配置（读 + 写）
      // ============================================================
      case 'get_global_config': {
        const cfg = useGlobalConfigStore.getState().config
        // 屏蔽敏感字段，避免 AI 不慎把密钥写回去或外泄到对话历史
        const SENSITIVE_KEYS = new Set([
          'apiKey', 'authCode', 'password', 'accessToken', 'appSecret',
          'azureApiKey',
        ])
        const masked = JSON.parse(JSON.stringify(cfg))
        const walk = (obj: any) => {
          if (!obj || typeof obj !== 'object') return
          for (const k of Object.keys(obj)) {
            if (SENSITIVE_KEYS.has(k)) {
              const v = obj[k]
              obj[k] = v ? `[已配置 长度=${String(v).length}]` : '[未配置]'
            } else if (typeof obj[k] === 'object') {
              walk(obj[k])
            }
          }
        }
        walk(masked)
        return {
          success: true,
          data: masked,
          message: '已读取全局配置（敏感字段已脱敏）',
        }
      }

      case 'reset_global_config': {
        const cfgStore = useGlobalConfigStore.getState() as any
        if (typeof cfgStore.resetConfig === 'function') {
          cfgStore.resetConfig()
          emitAssistantUiEvent('show_toast', {
            message: '全局配置已重置为默认值',
            type: 'warning',
          })
          try {
            useWorkflowStore.getState().addLog({
              level: 'warning',
              message: '[小助手] 已重置全局配置为默认值',
            })
          } catch {}
          return { success: true, message: '已重置全局配置为默认值' }
        }
        return { success: false, error: 'resetConfig 方法不存在' }
      }

      case 'update_global_config': {
        const section = payload.section as string
        const values = (payload.values as Record<string, any>) || {}
        if (!section) return { success: false, error: '缺少 section' }
        if (!values || Object.keys(values).length === 0) {
          return { success: false, error: 'values 不能为空' }
        }
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
          return {
            success: false,
            error: `未知配置段：${section}。可选值：${Object.keys(updateMap).join(', ')}`,
          }
        }
        // 调用 store 更新方法（zustand persist 会自动写入 localStorage）
        try {
          cfgStore[fnName](values)
        } catch (err) {
          return {
            success: false,
            error: `更新配置失败：${err instanceof Error ? err.message : String(err)}`,
          }
        }
        // 在工作流日志面板加一条记录，让用户能看到 AI 改了什么
        try {
          const changedKeys = Object.keys(values)
          const summary = changedKeys
            .map((k) => {
              const v = values[k]
              const SENSITIVE = new Set(['apiKey', 'authCode', 'password', 'accessToken', 'appSecret', 'azureApiKey'])
              if (SENSITIVE.has(k)) return `${k}=***`
              if (typeof v === 'object') return `${k}=(对象)`
              return `${k}=${String(v).slice(0, 60)}`
            })
            .join(', ')
          useWorkflowStore.getState().addLog({
            level: 'info',
            message: `[小助手] 已更新全局配置 ${section}: ${summary}`,
          })
        } catch {}
        // 给用户一个明显的 toast 提示
        emitAssistantUiEvent('show_toast', {
          message: `小助手已更新「${section}」配置`,
          type: 'success',
        })
        return {
          success: true,
          message: `已更新配置 ${section}（共 ${Object.keys(values).length} 个字段，已自动持久化到本地）`,
          data: { section, fields: Object.keys(values) },
        }
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

      // ============================================================
      // 屏保弹幕：UI 控制 + 真生效启动/停止
      // ============================================================
      case 'open_screensaver':
        emitAssistantUiEvent('open_screensaver', payload)
        return { success: true, message: '已打开屏保弹幕配置面板' }

      case 'close_screensaver':
        emitAssistantUiEvent('close_screensaver', payload)
        return { success: true, message: '已关闭屏保弹幕配置面板' }

      case 'start_screensaver': {
        // 直接调后端 API 真启动子进程（无需打开 UI）；payload 即为完整 config
        const cfg = (payload && typeof payload === 'object') ? payload as Record<string, unknown> : {}
        const res = await screensaverApi.start(cfg)
        if (res.success) {
          return { success: true, message: '屏保已启动', data: res.data }
        }
        return { success: false, error: res.error || '启动屏保失败' }
      }

      case 'stop_screensaver': {
        const res = await screensaverApi.stop()
        if (res.success) {
          return { success: true, message: '屏保已停止', data: res.data }
        }
        return { success: false, error: res.error || '停止屏保失败' }
      }

      case 'get_screensaver_status': {
        const res = await screensaverApi.status()
        if (res.success) return { success: true, data: res.data }
        return { success: false, error: res.error || '获取屏保状态失败' }
      }

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
  onReasoningPartial?: (data: any) => void
  onContentPartial?: (data: any) => void
}) {
  if (bound) return
  bound = true
  socketService.on('ai_assistant:tool_call', (data) => handlers.onToolCall?.(data))
  socketService.on('ai_assistant:tool_result', (data) => handlers.onToolResult?.(data))
  socketService.on('ai_assistant:assistant_partial', (data) => handlers.onAssistantPartial?.(data))
  socketService.on('ai_assistant:reasoning_partial', (data) => handlers.onReasoningPartial?.(data))
  socketService.on('ai_assistant:content_partial', (data) => handlers.onContentPartial?.(data))

  // 关键：后端发出 client_action 工具调用后会通过 socket 发请求让前端立即执行，
  // 前端必须把真实执行结果通过 ack 事件回传，否则后端会等 30s 超时
  socketService.on('ai_assistant:client_action_request', async (data: any) => {
    const toolCallId = data?.tool_call_id
    const action = data?.action
    const payload = data?.payload || {}
    if (!toolCallId || !action) return
    try {
      const result = await executeClientAction(action, payload)
      socketService.emit('ai_client_action_ack', { tool_call_id: toolCallId, result })
    } catch (err: any) {
      socketService.emit('ai_client_action_ack', {
        tool_call_id: toolCallId,
        result: { success: false, error: err?.message || String(err) || '前端执行 client_action 异常' },
      })
    }
  })
}
