import { useEffect, useState, useCallback } from 'react'
import { Plus, Trash2, RefreshCw, CheckCircle2, XCircle, Server, AlertCircle, Loader2, ChevronRight, ChevronDown, ExternalLink } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { getBackendBaseUrl } from '@/services/config'

/**
 * MCP（Model Context Protocol）配置面板
 *
 * 功能：
 * - 列出已配置的 MCP server，显示连接状态和工具数量
 * - 添加 / 编辑 / 删除 server（支持 stdio / sse / http 三种 transport）
 * - 一键重新连接
 * - 查看每个 server 暴露的工具列表
 */

interface MCPServerConfig {
  transport?: 'stdio' | 'sse' | 'http'
  command?: string
  args?: string[]
  env?: Record<string, string>
  cwd?: string
  url?: string
  headers?: Record<string, string>
  disabled?: boolean
  autoApprove?: string[]
}

interface MCPServerStatus {
  name: string
  transport: string
  disabled: boolean
  connected: boolean
  tool_count: number
  tools: { name: string; description: string }[]
  last_error: string | null
  connected_at: string | null
  auto_approve: string[]
}

interface MCPStatus {
  servers: MCPServerStatus[]
  total_tools_injected: number
}

const DEFAULT_NEW_SERVER: MCPServerConfig = {
  transport: 'stdio',
  command: '',
  args: [],
  env: {},
  disabled: false,
  autoApprove: [],
}

export function MCPConfigPanel() {
  const [config, setConfig] = useState<{ mcpServers: Record<string, MCPServerConfig> }>({ mcpServers: {} })
  const [status, setStatus] = useState<MCPStatus | null>(null)
  const [loading, setLoading] = useState(false)
  const [reloading, setReloading] = useState(false)
  const [editingName, setEditingName] = useState<string | null>(null)
  const [expandedServers, setExpandedServers] = useState<Set<string>>(new Set())
  const [error, setError] = useState<string | null>(null)
  const [savedFlash, setSavedFlash] = useState(false)

  // 拉取当前配置 + 状态
  const refresh = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const base = getBackendBaseUrl()
      const [cfgRes, stRes] = await Promise.all([
        fetch(`${base}/api/ai-assistant/mcp/config`),
        fetch(`${base}/api/ai-assistant/mcp/status`),
      ])
      const cfg = await cfgRes.json()
      const st = await stRes.json()
      setConfig({ mcpServers: cfg?.mcpServers || {} })
      setStatus(st)
    } catch (e: any) {
      setError(e?.message || '加载失败')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  // 保存配置
  const saveConfig = async (next: { mcpServers: Record<string, MCPServerConfig> }) => {
    try {
      const base = getBackendBaseUrl()
      const res = await fetch(`${base}/api/ai-assistant/mcp/config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ config: next }),
      })
      if (!res.ok) throw new Error(await res.text())
      setSavedFlash(true)
      setTimeout(() => setSavedFlash(false), 1500)
      setError(null)
      return true
    } catch (e: any) {
      setError(`保存失败：${e?.message || e}`)
      return false
    }
  }

  // 重新连接所有 server
  const reload = async () => {
    setReloading(true)
    setError(null)
    try {
      const base = getBackendBaseUrl()
      const res = await fetch(`${base}/api/ai-assistant/mcp/reload`, { method: 'POST' })
      if (!res.ok) throw new Error(await res.text())
      await refresh()
    } catch (e: any) {
      setError(`重连失败：${e?.message || e}`)
    } finally {
      setReloading(false)
    }
  }

  // 添加 / 编辑 server
  const upsertServer = async (name: string, server: MCPServerConfig, oldName?: string) => {
    if (!name.trim()) {
      setError('服务器名称不能为空')
      return
    }
    const next = { ...config }
    if (oldName && oldName !== name) {
      delete next.mcpServers[oldName]
    }
    next.mcpServers[name] = server
    setConfig(next)
    if (await saveConfig(next)) {
      setEditingName(null)
    }
  }

  const deleteServer = async (name: string) => {
    if (!confirm(`确认删除 MCP 服务器 "${name}"？`)) return
    const next = { ...config }
    delete next.mcpServers[name]
    setConfig(next)
    await saveConfig(next)
    await reload()
  }

  const toggleDisabled = async (name: string) => {
    const next = { ...config }
    next.mcpServers[name] = {
      ...next.mcpServers[name],
      disabled: !next.mcpServers[name].disabled,
    }
    setConfig(next)
    await saveConfig(next)
  }

  const toggleExpanded = (name: string) => {
    const next = new Set(expandedServers)
    if (next.has(name)) next.delete(name)
    else next.add(name)
    setExpandedServers(next)
  }

  const serverNames = Object.keys(config.mcpServers)

  return (
    <div className="space-y-4">
      {/* 顶部说明 */}
      <div className="p-3 rounded-md bg-violet-50 border border-violet-200/50 text-xs text-violet-800 leading-relaxed">
        <div className="flex items-start gap-2">
          <Server className="w-4 h-4 mt-0.5 flex-shrink-0" />
          <div>
            <strong>MCP（Model Context Protocol）</strong> 让你接入第三方工具到 WebRPA 小助手。
            支持 <code className="px-1 bg-violet-100 rounded">stdio</code>（本地命令）、
            <code className="px-1 bg-violet-100 rounded mx-0.5">sse</code> 和
            <code className="px-1 bg-violet-100 rounded ml-0.5">http</code>（远程服务）。
            配置格式与 Claude Desktop / Kiro 兼容。
            <a
              className="ml-2 text-violet-700 underline inline-flex items-center gap-0.5"
              href="https://github.com/modelcontextprotocol/servers"
              target="_blank"
              rel="noreferrer"
              onClick={(e) => {
                e.preventDefault()
                window.open('https://github.com/modelcontextprotocol/servers', '_blank')
              }}
            >
              官方 server 列表 <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>
      </div>

      {/* 统计 + 操作 */}
      <div className="flex items-center justify-between gap-2">
        <div className="text-xs text-gray-600">
          {loading ? '加载中…' : (
            <>
              共 <strong>{serverNames.length}</strong> 个服务器
              {status && (
                <>
                  {' · '}已连接 <strong className="text-green-600">{status.servers.filter(s => s.connected).length}</strong>
                  {' · '}注入 <strong className="text-violet-600">{status.total_tools_injected}</strong> 个工具
                </>
              )}
              {savedFlash && <span className="ml-2 text-green-600 inline-flex items-center gap-0.5"><CheckCircle2 className="w-3 h-3" /> 已保存</span>}
            </>
          )}
        </div>
        <div className="flex gap-2">
          <Button size="sm" variant="outline" onClick={reload} disabled={reloading || loading}>
            {reloading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
            <span className="ml-1">重新连接</span>
          </Button>
          <Button size="sm" onClick={() => setEditingName('__new__')} disabled={loading}>
            <Plus className="w-3.5 h-3.5" />
            <span className="ml-1">添加</span>
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-2.5 rounded-md bg-red-50 border border-red-200 text-xs text-red-700 flex items-start gap-1.5">
          <AlertCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* 服务器列表 */}
      <div className="space-y-2">
        {serverNames.length === 0 && !loading && (
          <div className="text-center py-8 text-sm text-gray-500">
            还没有配置 MCP 服务器，点上方"添加"开始
          </div>
        )}
        {serverNames.map((name) => {
          const server = config.mcpServers[name]
          const st = status?.servers.find((s) => s.name === name)
          const isExpanded = expandedServers.has(name)
          return (
            <div
              key={name}
              className={`border rounded-md ${server.disabled ? 'border-gray-200 bg-gray-50/50' : (st?.connected ? 'border-green-200 bg-green-50/30' : 'border-amber-200 bg-amber-50/30')}`}
            >
              <div className="px-3 py-2.5 flex items-center gap-2">
                <button
                  onClick={() => toggleExpanded(name)}
                  className="text-gray-500 hover:text-gray-800 p-0.5"
                >
                  {isExpanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                </button>
                {server.disabled ? (
                  <XCircle className="w-4 h-4 text-gray-400" />
                ) : st?.connected ? (
                  <CheckCircle2 className="w-4 h-4 text-green-600" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-amber-600" />
                )}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-sm text-gray-900 truncate">{name}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-600 uppercase">
                      {server.transport || 'stdio'}
                    </span>
                  </div>
                  <div className="text-xs text-gray-500 truncate mt-0.5">
                    {server.disabled
                      ? '已禁用'
                      : st?.connected
                        ? `已连接 · ${st.tool_count} 个工具`
                        : st?.last_error
                          ? `连接失败：${st.last_error.slice(0, 60)}`
                          : '未连接'}
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => toggleDisabled(name)}
                    className="text-xs px-2 py-1 rounded border border-gray-200 hover:bg-gray-100 text-gray-700"
                  >
                    {server.disabled ? '启用' : '禁用'}
                  </button>
                  <button
                    onClick={() => setEditingName(name)}
                    className="text-xs px-2 py-1 rounded border border-blue-200 text-blue-700 hover:bg-blue-50"
                  >
                    编辑
                  </button>
                  <button
                    onClick={() => deleteServer(name)}
                    className="text-xs p-1 rounded border border-red-200 text-red-600 hover:bg-red-50"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              </div>
              {isExpanded && st && (
                <div className="px-3 pb-3 pt-1 border-t border-gray-100/80 text-xs space-y-2">
                  {st.tools.length > 0 ? (
                    <div>
                      <div className="text-gray-600 mb-1">暴露的工具（{st.tools.length}）：</div>
                      <div className="space-y-1 max-h-48 overflow-y-auto">
                        {st.tools.map((t) => (
                          <div key={t.name} className="flex items-baseline gap-2">
                            <code className="text-violet-700 font-mono text-[11px]">{t.name}</code>
                            <span className="text-gray-500 text-[11px]">{t.description}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="text-gray-500">{st.connected ? '此服务器没有暴露工具' : '未连接'}</div>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* 编辑/新增表单 */}
      {editingName !== null && (
        <ServerEditModal
          name={editingName === '__new__' ? '' : editingName}
          server={editingName === '__new__' ? DEFAULT_NEW_SERVER : config.mcpServers[editingName]}
          existingNames={serverNames}
          onClose={() => setEditingName(null)}
          onSave={(name, server) => upsertServer(name, server, editingName === '__new__' ? undefined : editingName)}
        />
      )}
    </div>
  )
}

// =============================================================================
// 编辑/新增 Server 表单
// =============================================================================

interface ServerEditModalProps {
  name: string
  server: MCPServerConfig
  existingNames: string[]
  onClose: () => void
  onSave: (name: string, server: MCPServerConfig) => void | Promise<void>
}

function ServerEditModal({ name: initialName, server: initialServer, existingNames, onClose, onSave }: ServerEditModalProps) {
  const [name, setName] = useState(initialName)
  const [transport, setTransport] = useState<'stdio' | 'sse' | 'http'>(initialServer.transport || 'stdio')
  const [command, setCommand] = useState(initialServer.command || '')
  const [args, setArgs] = useState((initialServer.args || []).join('\n'))
  const [envText, setEnvText] = useState(
    Object.entries(initialServer.env || {}).map(([k, v]) => `${k}=${v}`).join('\n')
  )
  const [cwd, setCwd] = useState(initialServer.cwd || '')
  const [url, setUrl] = useState(initialServer.url || '')
  const [headersText, setHeadersText] = useState(
    Object.entries(initialServer.headers || {}).map(([k, v]) => `${k}: ${v}`).join('\n')
  )
  const [autoApproveText, setAutoApproveText] = useState(
    (initialServer.autoApprove || []).join('\n')
  )

  const isNew = initialName === ''
  const nameConflict = isNew && existingNames.includes(name)

  const handleSave = () => {
    if (!name.trim()) return
    if (nameConflict) return

    const envLines = envText.split('\n').map(l => l.trim()).filter(Boolean)
    const env: Record<string, string> = {}
    for (const line of envLines) {
      const idx = line.indexOf('=')
      if (idx > 0) env[line.slice(0, idx).trim()] = line.slice(idx + 1).trim()
    }

    const headersLines = headersText.split('\n').map(l => l.trim()).filter(Boolean)
    const headers: Record<string, string> = {}
    for (const line of headersLines) {
      const idx = line.indexOf(':')
      if (idx > 0) headers[line.slice(0, idx).trim()] = line.slice(idx + 1).trim()
    }

    const autoApprove = autoApproveText.split('\n').map(l => l.trim()).filter(Boolean)
    const argsList = args.split('\n').map(l => l.trim()).filter(Boolean)

    const server: MCPServerConfig = {
      transport,
      ...(transport === 'stdio' ? {
        command: command.trim(),
        args: argsList,
        env,
        ...(cwd.trim() ? { cwd: cwd.trim() } : {}),
      } : {
        url: url.trim(),
        ...(Object.keys(headers).length > 0 ? { headers } : {}),
      }),
      disabled: initialServer.disabled || false,
      ...(autoApprove.length > 0 ? { autoApprove } : {}),
    }
    onSave(name.trim(), server)
  }

  return (
    <div
      className="fixed inset-0 z-[10001] bg-black/40 backdrop-blur-sm flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[88vh] flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header（固定不滚动） */}
        <div className="px-5 py-3 border-b border-gray-200 flex items-center justify-between flex-shrink-0">
          <h3 className="font-semibold text-gray-800">
            {isNew ? '添加 MCP 服务器' : `编辑：${initialName}`}
          </h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-800 text-lg leading-none">×</button>
        </div>

        {/* Body（中间区域滚动） */}
        <div className="px-5 py-4 space-y-3 overflow-y-auto flex-1">
          <div>
            <Label className="text-gray-700 text-xs">服务器名称（唯一标识，不能含空格）</Label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value.replace(/\s/g, '-'))}
              placeholder="例如 filesystem / weather / github"
              disabled={!isNew}
              className="bg-white text-black border-gray-300 mt-1 h-8 text-sm"
            />
            {nameConflict && <p className="text-xs text-red-600 mt-1">名称已存在</p>}
          </div>
          <div>
            <Label className="text-gray-700 text-xs">传输方式</Label>
            <div className="flex gap-2 mt-1">
              {(['stdio', 'sse', 'http'] as const).map((t) => (
                <button
                  key={t}
                  onClick={() => setTransport(t)}
                  className={`px-3 py-1 text-xs rounded-md border ${transport === t ? 'border-violet-500 bg-violet-50 text-violet-700 font-medium' : 'border-gray-300 text-gray-600 hover:bg-gray-50'}`}
                >
                  {t}
                </button>
              ))}
            </div>
            <p className="text-[11px] text-gray-500 mt-1">
              {transport === 'stdio' && '本地子进程（npx / node / python 等启动 MCP server）'}
              {transport === 'sse' && '远程 SSE 流（Server-Sent Events）'}
              {transport === 'http' && '远程 HTTP（Streamable HTTP）'}
            </p>
          </div>

          {transport === 'stdio' ? (
            <>
              <div>
                <Label className="text-gray-700 text-xs">启动命令 *</Label>
                <Input
                  value={command}
                  onChange={(e) => setCommand(e.target.value)}
                  placeholder="例如 npx / node / python"
                  className="bg-white text-black border-gray-300 mt-1 h-8 font-mono text-sm"
                />
              </div>
              <div>
                <Label className="text-gray-700 text-xs">命令参数（每行一个）</Label>
                <textarea
                  value={args}
                  onChange={(e) => setArgs(e.target.value)}
                  placeholder={'-y\n@modelcontextprotocol/server-filesystem\nD:\\Documents'}
                  rows={3}
                  className="w-full px-3 py-1.5 text-xs rounded-md border border-gray-300 bg-white text-black mt-1 font-mono"
                />
              </div>
              <div>
                <Label className="text-gray-700 text-xs">环境变量（KEY=VALUE，每行一个）</Label>
                <textarea
                  value={envText}
                  onChange={(e) => setEnvText(e.target.value)}
                  placeholder={'API_KEY=xxx\nDEBUG=1'}
                  rows={2}
                  className="w-full px-3 py-1.5 text-xs rounded-md border border-gray-300 bg-white text-black mt-1 font-mono"
                />
              </div>
              <div>
                <Label className="text-gray-700 text-xs">工作目录（可选）</Label>
                <Input
                  value={cwd}
                  onChange={(e) => setCwd(e.target.value)}
                  placeholder="留空使用 backend 当前目录"
                  className="bg-white text-black border-gray-300 mt-1 h-8 text-sm"
                />
              </div>
            </>
          ) : (
            <>
              <div>
                <Label className="text-gray-700 text-xs">服务器 URL *</Label>
                <Input
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder={transport === 'sse' ? 'https://example.com/sse' : 'https://example.com/mcp'}
                  className="bg-white text-black border-gray-300 mt-1 h-8 font-mono text-sm"
                />
              </div>
              <div>
                <Label className="text-gray-700 text-xs">请求头（Key: Value，每行一个）</Label>
                <textarea
                  value={headersText}
                  onChange={(e) => setHeadersText(e.target.value)}
                  placeholder={'Authorization: Bearer xxx\nX-API-Key: yyy'}
                  rows={2}
                  className="w-full px-3 py-1.5 text-xs rounded-md border border-gray-300 bg-white text-black mt-1 font-mono"
                />
              </div>
            </>
          )}

          <div>
            <Label className="text-gray-700 text-xs">自动批准的工具（可选，每行一个工具名）</Label>
            <textarea
              value={autoApproveText}
              onChange={(e) => setAutoApproveText(e.target.value)}
              placeholder={'read_file\nlist_directory'}
              rows={2}
              className="w-full px-3 py-1.5 text-xs rounded-md border border-gray-300 bg-white text-black mt-1 font-mono"
            />
            <p className="text-[11px] text-gray-500 mt-1">
              这些工具调用时不会要求确认。其他工具默认需要确认。
            </p>
          </div>
        </div>

        {/* Footer（固定不滚动） */}
        <div className="px-5 py-3 border-t border-gray-200 flex justify-end gap-2 flex-shrink-0 bg-white">
          <Button variant="outline" onClick={onClose}>取消</Button>
          <Button onClick={handleSave} disabled={!name.trim() || nameConflict || (transport === 'stdio' ? !command.trim() : !url.trim())}>
            保存
          </Button>
        </div>
      </div>
    </div>
  )
}
