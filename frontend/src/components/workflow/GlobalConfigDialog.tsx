import { useState, useEffect, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useConfirm } from '@/components/ui/confirm-dialog'
import { useGlobalConfigStore, type BrowserType } from '@/store/globalConfigStore'
import { X, Settings, Brain, Mail, RotateCcw, Folder, Loader2, Database, Monitor, Globe, Zap, MessageCircle, MessageSquare, Plus, Trash2 } from 'lucide-react'
import { systemApi } from '@/services/api'
import { getBackendBaseUrl } from '@/services/config'

interface GlobalConfigDialogProps {
  isOpen: boolean
  onClose: () => void
}

type TabType = 'system' | 'ai' | 'aiScraper' | 'email' | 'workflow' | 'database' | 'display' | 'browser' | 'triggers' | 'qq' | 'feishu'

// 浏览器选项
const browserOptions: { value: BrowserType; label: string; description: string }[] = [
  { value: 'msedge', label: 'Microsoft Edge', description: '启动系统安装的 Edge 浏览器（非系统默认浏览器）' },
  { value: 'chrome', label: 'Google Chrome', description: '启动系统安装的 Chrome 浏览器' },
  { value: 'chromium', label: 'Chromium', description: '启动 Chromium 浏览器（开源版本）' },
  { value: 'firefox', label: 'Firefox', description: '需要安装 Firefox 浏览器' },
]

export function GlobalConfigDialog({ isOpen, onClose }: GlobalConfigDialogProps) {
  const { 
    config, 
    updateSystemConfig,
    updateAIConfig, 
    updateAIScraperConfig, 
    updateEmailConfig, 
    updateEmailTriggerConfig,
    updateApiTriggerConfig,
    updateFileTriggerConfig,
    updateWorkflowConfig, 
    updateDatabaseConfig, 
    updateQQConfig,
    updateFeishuConfig,
    updateDisplayConfig, 
    updateBrowserConfig, 
    resetConfig 
  } = useGlobalConfigStore()
  const [activeTab, setActiveTab] = useState<TabType>('system')
  const [defaultFolder, setDefaultFolder] = useState<string>('')
  const [isSelectingFolder, setIsSelectingFolder] = useState(false)
  const [isSelectingBrowser, setIsSelectingBrowser] = useState(false)
  const [showBrowserConfigTip, setShowBrowserConfigTip] = useState(false)
  const { confirm, ConfirmDialog } = useConfirm()
  const browserConfigTipRef = useRef<HTMLDivElement>(null)

  // 获取默认文件夹路径
  useEffect(() => {
    if (isOpen) {
      const API_BASE = getBackendBaseUrl()
      fetch(`${API_BASE}/api/local-workflows/default-folder`)
        .then(res => res.json())
        .then(data => {
          if (data.folder) {
            setDefaultFolder(data.folder)
          }
        })
        .catch(console.error)
    }
  }, [isOpen])

  // 当提示框显示时，自动滚动到提示框位置
  useEffect(() => {
    if (showBrowserConfigTip && browserConfigTipRef.current) {
      // 使用 setTimeout 确保 DOM 已更新
      setTimeout(() => {
        browserConfigTipRef.current?.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'nearest' 
        })
      }, 100)
    }
  }, [showBrowserConfigTip])

  if (!isOpen) return null

  const handleReset = async () => {
    const confirmed = await confirm('确定要重置所有全局配置吗？', { type: 'warning', title: '重置配置' })
    if (confirmed) {
      resetConfig()
    }
  }

  return (
    <div 
      className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4 animate-fade-in"
      onClick={onClose}
    >
      <div 
        className="bg-white text-black border border-gray-200 rounded-xl shadow-2xl w-full max-w-2xl overflow-hidden animate-scale-in"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 标题栏 */}
        <div className="flex items-center justify-between p-4 border-b bg-gradient-to-r from-blue-50 via-cyan-50/50 to-teal-50">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500">
              <Settings className="w-4 h-4 text-white" />
            </div>
            <h3 className="font-semibold text-gradient">全局默认配置</h3>
          </div>
          <Button variant="ghost" size="icon" className="text-gray-600 hover:text-gray-900 hover:bg-white/50" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>

        {/* 标签页 */}
        <div className="flex border-b bg-gray-50/50 overflow-x-auto scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-transparent hover:scrollbar-thumb-gray-400">
          <button
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-all duration-200 whitespace-nowrap flex-shrink-0 ${
              activeTab === 'system'
                ? 'border-blue-500 text-blue-600 bg-gradient-to-t from-blue-50 to-transparent'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-100/50'
            }`}
            onClick={() => setActiveTab('system')}
          >
            <Settings className="w-4 h-4" />
            系统
          </button>
          <button
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-all duration-200 whitespace-nowrap flex-shrink-0 ${
              activeTab === 'ai'
                ? 'border-blue-500 text-blue-600 bg-gradient-to-t from-blue-50 to-transparent'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-100/50'
            }`}
            onClick={() => setActiveTab('ai')}
          >
            <Brain className="w-4 h-4" />
            AI对话
          </button>
          <button
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-all duration-200 whitespace-nowrap flex-shrink-0 ${
              activeTab === 'aiScraper'
                ? 'border-blue-500 text-blue-600 bg-gradient-to-t from-blue-50 to-transparent'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-100/50'
            }`}
            onClick={() => setActiveTab('aiScraper')}
          >
            <Brain className="w-4 h-4" />
            AI智能
          </button>
          <button
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-all duration-200 whitespace-nowrap flex-shrink-0 ${
              activeTab === 'email'
                ? 'border-blue-500 text-blue-600 bg-gradient-to-t from-blue-50 to-transparent'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-100/50'
            }`}
            onClick={() => setActiveTab('email')}
          >
            <Mail className="w-4 h-4" />
            邮件
          </button>
          <button
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap flex-shrink-0 ${
              activeTab === 'workflow'
                ? 'border-blue-500 text-blue-600 bg-blue-50'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50'
            }`}
            onClick={() => setActiveTab('workflow')}
          >
            <Folder className="w-4 h-4" />
            存储
          </button>
          <button
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap flex-shrink-0 ${
              activeTab === 'database'
                ? 'border-blue-500 text-blue-600 bg-blue-50'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50'
            }`}
            onClick={() => setActiveTab('database')}
          >
            <Database className="w-4 h-4" />
            数据库
          </button>
          <button
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap flex-shrink-0 ${
              activeTab === 'display'
                ? 'border-blue-500 text-blue-600 bg-blue-50'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50'
            }`}
            onClick={() => setActiveTab('display')}
          >
            <Monitor className="w-4 h-4" />
            显示
          </button>
          <button
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap flex-shrink-0 ${
              activeTab === 'browser'
                ? 'border-blue-500 text-blue-600 bg-blue-50'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50'
            }`}
            onClick={() => setActiveTab('browser')}
          >
            <Globe className="w-4 h-4" />
            浏览器
          </button>
          <button
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap flex-shrink-0 ${
              activeTab === 'triggers'
                ? 'border-blue-500 text-blue-600 bg-blue-50'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50'
            }`}
            onClick={() => setActiveTab('triggers')}
          >
            <Zap className="w-4 h-4" />
            触发器
          </button>
          <button
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap flex-shrink-0 ${
              activeTab === 'qq'
                ? 'border-blue-500 text-blue-600 bg-blue-50'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50'
            }`}
            onClick={() => setActiveTab('qq')}
          >
            <MessageCircle className="w-4 h-4" />
            QQ号
          </button>
          <button
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap flex-shrink-0 ${
              activeTab === 'feishu'
                ? 'border-blue-500 text-blue-600 bg-blue-50'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50'
            }`}
            onClick={() => setActiveTab('feishu')}
          >
            <MessageSquare className="w-4 h-4" />
            飞书
          </button>
        </div>

        {/* 内容区 */}
        <div className="p-4 space-y-4 max-h-[60vh] overflow-y-auto">
          {activeTab === 'system' && (
            <>
              <p className="text-xs text-gray-500 mb-4">
                配置系统相关的全局设置
              </p>
              
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200">
                  <div className="flex-1">
                    <Label className="text-sm font-medium text-gray-700">启动时检查更新</Label>
                    <p className="text-xs text-gray-500 mt-1">
                      启动WebRPA时自动检查是否有新版本可用
                    </p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      className="sr-only peer"
                      checked={config.system.checkUpdateOnStartup}
                      onChange={(e) => updateSystemConfig({ checkUpdateOnStartup: e.target.checked })}
                    />
                    <div className="w-11 h-6 bg-gray-300 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>
                
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200">
                  <div className="flex-1">
                    <Label className="text-sm font-medium text-gray-700">自动识别剪贴板截图</Label>
                    <p className="text-xs text-gray-500 mt-1">
                      当剪贴板中有新截图时，自动弹出保存对话框
                    </p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      className="sr-only peer"
                      checked={config.system.autoDetectClipboardScreenshot}
                      onChange={(e) => updateSystemConfig({ autoDetectClipboardScreenshot: e.target.checked })}
                    />
                    <div className="w-11 h-6 bg-gray-300 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>
              </div>
            </>
          )}

          {activeTab === 'ai' && (
            <>
              <p className="text-xs text-gray-500 mb-4">
                配置AI对话模块的默认值，新建模块时将自动填充这些配置
              </p>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label className="text-gray-700">默认API地址</Label>
                  <Input
                    value={config.ai.apiUrl}
                    onChange={(e) => updateAIConfig({ apiUrl: e.target.value })}
                    placeholder="https://api.openai.com/v1/chat/completions"
                    className="bg-white text-black border-gray-300"
                  />
                  <p className="text-xs text-gray-500">
                    智谱: https://open.bigmodel.cn/api/paas/v4/chat/completions<br/>
                    Deepseek: https://api.deepseek.com/chat/completions
                  </p>
                </div>
                <div className="space-y-2">
                  <Label className="text-gray-700">默认API密钥</Label>
                  <Input
                    type="password"
                    value={config.ai.apiKey}
                    onChange={(e) => updateAIConfig({ apiKey: e.target.value })}
                    placeholder="sk-xxx"
                    className="bg-white text-black border-gray-300"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-gray-700">默认模型名称</Label>
                  <Input
                    value={config.ai.model}
                    onChange={(e) => updateAIConfig({ model: e.target.value })}
                    placeholder="gpt-3.5-turbo / glm-4 / deepseek-chat"
                    className="bg-white text-black border-gray-300"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-gray-700">默认温度</Label>
                    <Input
                      type="number"
                      min={0}
                      max={2}
                      step={0.1}
                      value={config.ai.temperature}
                      onChange={(e) => updateAIConfig({ temperature: parseFloat(e.target.value) || 0.7 })}
                      className="bg-white text-black border-gray-300"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-gray-700">默认最大Token</Label>
                    <Input
                      type="number"
                      min={1}
                      value={config.ai.maxTokens}
                      onChange={(e) => updateAIConfig({ maxTokens: parseInt(e.target.value) || 2000 })}
                      className="bg-white text-black border-gray-300"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label className="text-gray-700">默认系统提示词</Label>
                  <textarea
                    value={config.ai.systemPrompt}
                    onChange={(e) => updateAIConfig({ systemPrompt: e.target.value })}
                    placeholder="设定AI的角色和行为..."
                    className="w-full min-h-[80px] px-3 py-2 text-sm rounded-md border border-gray-300 bg-white text-black"
                  />
                </div>
              </div>
            </>
          )}

          {activeTab === 'aiScraper' && (
            <>
              <p className="text-xs text-gray-500 mb-4">
                配置AI智能爬虫和AI元素选择器模块的默认值，新建模块时将自动填充这些配置
              </p>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label className="text-gray-700">默认LLM提供商</Label>
                  <select
                    value={config.aiScraper?.llmProvider || 'ollama'}
                    onChange={(e) => updateAIScraperConfig({ llmProvider: e.target.value })}
                    className="w-full px-3 py-2 text-sm rounded-md border border-gray-300 bg-white text-black"
                  >
                    <option value="ollama">Ollama (本地免费)</option>
                    <option value="openai">OpenAI</option>
                    <option value="groq">Groq</option>
                    <option value="gemini">Google Gemini</option>
                    <option value="azure">Azure OpenAI</option>
                    <option value="zhipu">智谱 AI (GLM)</option>
                    <option value="deepseek">Deepseek</option>
                    <option value="custom">自定义</option>
                  </select>
                  <p className="text-xs text-gray-500">
                    推荐使用 Ollama 本地运行，完全免费
                  </p>
                </div>
                
                {(config.aiScraper?.llmProvider || 'ollama') !== 'ollama' && (
                  <div className="space-y-2">
                    <Label className="text-gray-700">默认API地址</Label>
                    <Input
                      value={config.aiScraper?.apiUrl || ''}
                      onChange={(e) => updateAIScraperConfig({ apiUrl: e.target.value })}
                      placeholder={
                        (config.aiScraper?.llmProvider || 'ollama') === 'openai' ? 'https://api.openai.com/v1' :
                        (config.aiScraper?.llmProvider || 'ollama') === 'zhipu' ? 'https://open.bigmodel.cn/api/paas/v4' :
                        (config.aiScraper?.llmProvider || 'ollama') === 'deepseek' ? 'https://api.deepseek.com' :
                        (config.aiScraper?.llmProvider || 'ollama') === 'groq' ? 'https://api.groq.com/openai/v1' :
                        (config.aiScraper?.llmProvider || 'ollama') === 'gemini' ? 'https://generativelanguage.googleapis.com/v1beta' :
                        '自定义API地址'
                      }
                      className="bg-white text-black border-gray-300"
                    />
                    <div className="text-xs text-gray-600 space-y-1 bg-gray-50 p-3 rounded-lg border border-gray-200">
                      <div className="font-medium text-gray-700 mb-1">常用API地址：</div>
                      <div><strong>OpenAI:</strong> https://api.openai.com/v1</div>
                      <div><strong>智谱AI:</strong> https://open.bigmodel.cn/api/paas/v4</div>
                      <div><strong>Deepseek:</strong> https://api.deepseek.com</div>
                      <div><strong>Groq:</strong> https://api.groq.com/openai/v1</div>
                      <div><strong>Gemini:</strong> https://generativelanguage.googleapis.com/v1beta</div>
                    </div>
                  </div>
                )}
                
                <div className="space-y-2">
                  <Label className="text-gray-700">默认模型名称</Label>
                  <Input
                    value={config.aiScraper?.llmModel || ''}
                    onChange={(e) => updateAIScraperConfig({ llmModel: e.target.value })}
                    placeholder={
                      (config.aiScraper?.llmProvider || 'ollama') === 'ollama' ? 'llama3.2' :
                      (config.aiScraper?.llmProvider || 'ollama') === 'openai' ? 'gpt-4o-mini' :
                      (config.aiScraper?.llmProvider || 'ollama') === 'zhipu' ? 'glm-4-flash' :
                      (config.aiScraper?.llmProvider || 'ollama') === 'deepseek' ? 'deepseek-chat' :
                      (config.aiScraper?.llmProvider || 'ollama') === 'groq' ? 'llama-3.3-70b-versatile' :
                      (config.aiScraper?.llmProvider || 'ollama') === 'gemini' ? 'gemini-2.0-flash-exp' :
                      '模型名称'
                    }
                    className="bg-white text-black border-gray-300"
                  />
                  <div className="text-xs text-gray-600 space-y-1 bg-gray-50 p-3 rounded-lg border border-gray-200">
                    <div className="font-medium text-gray-700 mb-1">推荐模型：</div>
                    {(config.aiScraper?.llmProvider || 'ollama') === 'ollama' && (
                      <>
                        <div><strong>llama3.2</strong> - Meta 开源模型，性能均衡</div>
                        <div><strong>qwen2.5</strong> - 阿里通义千问，中文友好</div>
                      </>
                    )}
                    {(config.aiScraper?.llmProvider || 'ollama') === 'openai' && (
                      <>
                        <div><strong>gpt-4o-mini</strong> - 性价比高，速度快</div>
                        <div><strong>gpt-4o</strong> - 最强性能</div>
                      </>
                    )}
                    {(config.aiScraper?.llmProvider || 'ollama') === 'zhipu' && (
                      <>
                        <div><strong>glm-4-flash</strong> - 免费，速度快</div>
                        <div><strong>glm-4-plus</strong> - 性能更强</div>
                      </>
                    )}
                    {(config.aiScraper?.llmProvider || 'ollama') === 'deepseek' && (
                      <>
                        <div><strong>deepseek-chat</strong> - 性价比极高</div>
                      </>
                    )}
                    {(config.aiScraper?.llmProvider || 'ollama') === 'groq' && (
                      <>
                        <div><strong>llama-3.3-70b-versatile</strong> - 免费，速度极快</div>
                      </>
                    )}
                    {(config.aiScraper?.llmProvider || 'ollama') === 'gemini' && (
                      <>
                        <div><strong>gemini-2.0-flash-exp</strong> - 免费，性能强</div>
                      </>
                    )}
                  </div>
                </div>
                
                {(config.aiScraper?.llmProvider || 'ollama') !== 'ollama' && (
                  <div className="space-y-2">
                    <Label className="text-gray-700">默认API Key</Label>
                    <Input
                      type="password"
                      value={config.aiScraper?.apiKey || ''}
                      onChange={(e) => updateAIScraperConfig({ apiKey: e.target.value })}
                      placeholder="sk-xxx 或其他格式的密钥"
                      className="bg-white text-black border-gray-300"
                    />
                  </div>
                )}
                
                {(config.aiScraper?.llmProvider || 'ollama') === 'azure' && (
                  <div className="space-y-2">
                    <Label className="text-gray-700">Azure Endpoint</Label>
                    <Input
                      value={config.aiScraper?.azureEndpoint || ''}
                      onChange={(e) => updateAIScraperConfig({ azureEndpoint: e.target.value })}
                      placeholder="https://your-resource.openai.azure.com/"
                      className="bg-white text-black border-gray-300"
                    />
                  </div>
                )}
                
                <div className="p-3 bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 rounded-lg">
                  <p className="text-xs text-purple-900">
                    <strong>💡 提示</strong><br/>
                    • <strong>Ollama</strong>: 需要先安装并下载模型，完全免费<br/>
                    • <strong>智谱/Groq/Gemini</strong>: 提供免费额度，适合测试<br/>
                    • <strong>OpenAI/Deepseek</strong>: 按使用量付费<br/>
                    • 这些配置将应用于 AI智能爬虫 和 AI元素选择器 模块
                  </p>
                </div>
              </div>
            </>
          )}

          {activeTab === 'email' && (
            <>
              <p className="text-xs text-gray-500 mb-4">
                配置发送邮件模块的默认值，新建模块时将自动填充这些配置
              </p>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label className="text-gray-700">默认发件人邮箱</Label>
                  <Input
                    value={config.email.senderEmail}
                    onChange={(e) => updateEmailConfig({ senderEmail: e.target.value })}
                    placeholder="your_qq@qq.com"
                    className="bg-white text-black border-gray-300"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-gray-700">默认授权码</Label>
                  <Input
                    type="password"
                    value={config.email.authCode}
                    onChange={(e) => updateEmailConfig({ authCode: e.target.value })}
                    placeholder="QQ邮箱授权码"
                    className="bg-white text-black border-gray-300"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-gray-700">SMTP服务器</Label>
                    <Input
                      value={config.email.smtpServer}
                      onChange={(e) => updateEmailConfig({ smtpServer: e.target.value })}
                      placeholder="smtp.qq.com"
                      className="bg-white text-black border-gray-300"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-gray-700">SMTP端口</Label>
                    <Input
                      type="number"
                      value={config.email.smtpPort}
                      onChange={(e) => updateEmailConfig({ smtpPort: parseInt(e.target.value) || 465 })}
                      className="bg-white text-black border-gray-300"
                    />
                  </div>
                </div>
              </div>
            </>
          )}

          {activeTab === 'workflow' && (
            <>
              <p className="text-xs text-gray-500 mb-4">
                配置本地工作流文件的保存位置和自动保存选项
              </p>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label className="text-gray-700">工作流保存文件夹</Label>
                  <div className="flex gap-1">
                    <Input
                      value={config.workflow?.localFolder || ''}
                      onChange={(e) => updateWorkflowConfig({ localFolder: e.target.value })}
                      placeholder={defaultFolder || '使用默认路径'}
                      className="bg-white text-black border-gray-300 flex-1"
                    />
                    <Button
                      type="button"
                      variant="outline"
                      size="icon"
                      disabled={isSelectingFolder}
                      className="shrink-0 border-gray-300"
                      onClick={async () => {
                        setIsSelectingFolder(true)
                        try {
                          const result = await systemApi.selectFolder('选择工作流保存文件夹')
                          if (result.data?.success && result.data.path) {
                            updateWorkflowConfig({ localFolder: result.data.path })
                          }
                        } catch (error) {
                          console.error('选择文件夹失败:', error)
                        } finally {
                          setIsSelectingFolder(false)
                        }
                      }}
                    >
                      {isSelectingFolder ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Folder className="w-4 h-4" />
                      )}
                    </Button>
                  </div>
                  <p className="text-xs text-gray-500">
                    留空则使用默认路径: {defaultFolder || '加载中...'}
                  </p>
                </div>
                {config.workflow?.localFolder && (
                  <Button
                    variant="outline"
                    size="sm"
                    className="border-gray-300 text-gray-700 hover:bg-gray-100"
                    onClick={() => updateWorkflowConfig({ localFolder: '' })}
                  >
                    恢复默认路径
                  </Button>
                )}
                
                {/* 自动保存开关 */}
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200">
                  <div>
                    <Label className="text-gray-700 font-medium">自动保存工作流</Label>
                    <p className="text-xs text-gray-500 mt-1">
                      开启后，工作流的每次编辑都会自动保存到本地，无需手动保存
                    </p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={config.workflow?.autoSave || false}
                      onChange={(e) => updateWorkflowConfig({ autoSave: e.target.checked })}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>
                
                {/* 覆盖提示开关 */}
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200">
                  <div>
                    <Label className="text-gray-700 font-medium">同名工作流覆盖提示</Label>
                    <p className="text-xs text-gray-500 mt-1">
                      手动保存工作流时，若本地存在同名文件，是否弹出覆盖确认提示
                    </p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={config.workflow?.showOverwriteConfirm !== false}
                      onChange={(e) => updateWorkflowConfig({ showOverwriteConfirm: e.target.checked })}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>
              </div>
            </>
          )}

          {activeTab === 'database' && (
            <>
              <p className="text-xs text-gray-500 mb-4">
                配置数据库模块的默认连接信息，新建模块时将自动填充这些配置
              </p>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-gray-700">主机地址</Label>
                    <Input
                      value={config.database?.host || 'localhost'}
                      onChange={(e) => updateDatabaseConfig({ host: e.target.value })}
                      placeholder="localhost"
                      className="bg-white text-black border-gray-300"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-gray-700">端口</Label>
                    <Input
                      type="number"
                      value={config.database?.port || 3306}
                      onChange={(e) => updateDatabaseConfig({ port: parseInt(e.target.value) || 3306 })}
                      placeholder="3306"
                      className="bg-white text-black border-gray-300"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label className="text-gray-700">用户名</Label>
                  <Input
                    value={config.database?.user || ''}
                    onChange={(e) => updateDatabaseConfig({ user: e.target.value })}
                    placeholder="root"
                    className="bg-white text-black border-gray-300"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-gray-700">密码</Label>
                  <Input
                    type="password"
                    value={config.database?.password || ''}
                    onChange={(e) => updateDatabaseConfig({ password: e.target.value })}
                    placeholder="数据库密码"
                    className="bg-white text-black border-gray-300"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-gray-700">数据库名</Label>
                  <Input
                    value={config.database?.database || ''}
                    onChange={(e) => updateDatabaseConfig({ database: e.target.value })}
                    placeholder="默认数据库名（可选）"
                    className="bg-white text-black border-gray-300"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-gray-700">字符集</Label>
                  <Input
                    value={config.database?.charset || 'utf8mb4'}
                    onChange={(e) => updateDatabaseConfig({ charset: e.target.value })}
                    placeholder="utf8mb4"
                    className="bg-white text-black border-gray-300"
                  />
                </div>
              </div>
            </>
          )}

          {activeTab === 'display' && (
            <>
              <p className="text-xs text-gray-500 mb-4">
                配置界面显示相关的选项
              </p>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200">
                  <div>
                    <Label className="text-gray-700 font-medium">鼠标坐标实时显示</Label>
                    <p className="text-xs text-gray-500 mt-1">
                      开启后会在鼠标旁边显示当前坐标位置
                    </p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={config.display?.showMouseCoordinates || false}
                      onChange={(e) => updateDisplayConfig({ showMouseCoordinates: e.target.checked })}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>
                
                {/* 连接点尺寸滑条 */}
                <div className="space-y-2 p-3 bg-gray-50 rounded-lg border border-gray-200">
                  <div className="flex items-center justify-between">
                    <Label className="text-gray-700 font-medium">节点连接点尺寸</Label>
                    <span className="text-sm font-semibold text-blue-600">{config.display?.handleSize || 12}px</span>
                  </div>
                  <p className="text-xs text-gray-500">
                    调整工作流画布中所有节点连接点的大小（6-24像素）
                  </p>
                  <div className="flex items-center gap-3 mt-3">
                    <span className="text-xs text-gray-500 w-8">小</span>
                    <input
                      type="range"
                      min="6"
                      max="24"
                      step="1"
                      value={config.display?.handleSize || 12}
                      onChange={(e) => updateDisplayConfig({ handleSize: parseInt(e.target.value) })}
                      className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                    />
                    <span className="text-xs text-gray-500 w-8 text-right">大</span>
                  </div>
                  <div className="flex justify-center gap-2 mt-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="text-xs border-gray-300 text-gray-700 hover:bg-gray-100"
                      onClick={() => updateDisplayConfig({ handleSize: 12 })}
                    >
                      恢复默认 (12px)
                    </Button>
                  </div>
                </div>
              </div>
            </>
          )}

          {activeTab === 'browser' && (
            <>
              <p className="text-xs text-gray-500 mb-4">
                配置浏览器自动化使用的浏览器类型，修改后需要重新打开浏览器才能生效
              </p>
              
              {/* 登录状态持久化提示 */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-5 h-5 rounded-full bg-blue-500 flex items-center justify-center mt-0.5">
                    <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-blue-900 mb-2">关于登录状态持久化</p>
                    <div className="text-xs text-blue-800 space-y-1.5">
                      <p>• <strong>使用默认浏览器（推荐）：</strong>登录状态会自动保存，下次运行工作流时无需重新登录</p>
                      <p>• <strong>使用自定义浏览器路径：</strong>由于技术限制，登录状态无法持久化保存，每次运行都需要重新登录</p>
                      <p className="pt-1 text-blue-700">💡 如需保持登录状态，建议使用默认的 Microsoft Edge 浏览器（不指定自定义路径）</p>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-4">
                <p className="text-xs text-amber-800">
                  <strong>重要提示：</strong>浏览器类型选项会启动对应的浏览器程序，而不是系统默认浏览器。
                  例如选择"Microsoft Edge"会启动系统安装的 Edge 浏览器，即使您的系统默认浏览器是 Chrome。
                  如果选择的浏览器未安装或路径不正确，请使用"自定义浏览器路径"手动指定。
                </p>
              </div>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label className="text-gray-700">浏览器类型</Label>
                  <div className="grid grid-cols-1 gap-2">
                    {browserOptions.map((option) => (
                      <label
                        key={option.value}
                        className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all ${
                          (config.browser?.type || 'msedge') === option.value
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                        }`}
                      >
                        <input
                          type="radio"
                          name="browserType"
                          value={option.value}
                          checked={(config.browser?.type || 'msedge') === option.value}
                          onChange={(e) => updateBrowserConfig({ type: e.target.value as BrowserType })}
                          className="w-4 h-4 text-blue-600"
                        />
                        <div className="flex-1">
                          <div className="font-medium text-gray-700">{option.label}</div>
                          <div className="text-xs text-gray-500">{option.description}</div>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>
                <div className="space-y-2">
                  <Label className="text-gray-700">自定义浏览器路径（可选）</Label>
                  <div className="flex gap-1">
                    <Input
                      value={config.browser?.executablePath || ''}
                      onChange={(e) => updateBrowserConfig({ executablePath: e.target.value })}
                      placeholder="留空则使用系统默认路径"
                      className="bg-white text-black border-gray-300 flex-1"
                    />
                    <Button
                      type="button"
                      variant="outline"
                      size="icon"
                      disabled={isSelectingBrowser}
                      className="shrink-0 border-gray-300"
                      onClick={async () => {
                        setIsSelectingBrowser(true)
                        try {
                          // fileTypes 格式: [["描述", "*.扩展名"], ...]
                          const result = await systemApi.selectFile('选择浏览器可执行文件', undefined, [
                            ['可执行文件', '*.exe']
                          ])
                          if (result.data?.success && result.data.path) {
                            updateBrowserConfig({ executablePath: result.data.path })
                          }
                        } catch (error) {
                          console.error('选择文件失败:', error)
                        } finally {
                          setIsSelectingBrowser(false)
                        }
                      }}
                    >
                      {isSelectingBrowser ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Folder className="w-4 h-4" />
                      )}
                    </Button>
                  </div>
                  <p className="text-xs text-gray-500">
                    如果选择的浏览器类型无法启动，可以手动指定浏览器可执行文件的路径
                  </p>
                </div>
                {config.browser?.executablePath && (
                  <Button
                    variant="outline"
                    size="sm"
                    className="border-gray-300 text-gray-700 hover:bg-gray-100"
                    onClick={() => updateBrowserConfig({ executablePath: '' })}
                  >
                    清除自定义路径
                  </Button>
                )}
                <div className="space-y-2">
                  <Label className="text-gray-700">浏览器数据缓存目录（可选）</Label>
                  <div className="flex gap-1">
                    <Input
                      value={config.browser?.userDataDir || ''}
                      onChange={(e) => updateBrowserConfig({ userDataDir: e.target.value })}
                      placeholder="留空则使用默认目录：backend/browser_data"
                      className="bg-white text-black border-gray-300 flex-1"
                    />
                    <Button
                      type="button"
                      variant="outline"
                      size="icon"
                      disabled={isSelectingFolder}
                      className="shrink-0 border-gray-300"
                      onClick={async () => {
                        setIsSelectingFolder(true)
                        try {
                          const result = await systemApi.selectFolder('选择浏览器数据缓存目录')
                          if (result.data?.success && result.data.path) {
                            updateBrowserConfig({ userDataDir: result.data.path })
                          }
                        } catch (error) {
                          console.error('选择文件夹失败:', error)
                        } finally {
                          setIsSelectingFolder(false)
                        }
                      }}
                    >
                      {isSelectingFolder ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Folder className="w-4 h-4" />
                      )}
                    </Button>
                  </div>
                  <p className="text-xs text-gray-500">
                    默认使用 backend/browser_data 目录存储浏览器数据（Cookie、缓存、登录状态等）。如需自定义存储位置或多项目共享数据，可在此指定
                  </p>
                </div>
                {config.browser?.userDataDir && (
                  <Button
                    variant="outline"
                    size="sm"
                    className="border-gray-300 text-gray-700 hover:bg-gray-100"
                    onClick={() => updateBrowserConfig({ userDataDir: '' })}
                  >
                    恢复默认目录
                  </Button>
                )}
                
                {/* 浏览器启动参数配置 */}
                <div className="space-y-2">
                  <Label className="text-gray-700">浏览器启动参数</Label>
                  <textarea
                    value={config.browser?.launchArgs || ''}
                    onChange={(e) => updateBrowserConfig({ launchArgs: e.target.value })}
                    placeholder="每行一个启动参数，例如：&#10;--disable-blink-features=AutomationControlled&#10;--start-maximized"
                    rows={8}
                    className="w-full px-3 py-2 text-sm font-mono border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-black resize-none"
                  />
                  <p className="text-xs text-gray-500">
                    每行一个参数，留空则使用默认参数。常用参数：
                  </p>
                  <div className="text-xs text-gray-600 space-y-1 bg-gray-50 p-3 rounded-lg border border-gray-200">
                    <div><code className="bg-gray-200 px-1 rounded">--disable-blink-features=AutomationControlled</code> - 隐藏自动化特征</div>
                    <div><code className="bg-gray-200 px-1 rounded">--start-maximized</code> - 最大化启动</div>
                    <div><code className="bg-gray-200 px-1 rounded">--ignore-certificate-errors</code> - 忽略证书错误</div>
                    <div><code className="bg-gray-200 px-1 rounded">--disable-web-security</code> - 禁用Web安全策略</div>
                    <div><code className="bg-gray-200 px-1 rounded">--disable-notifications</code> - 禁用通知</div>
                  </div>
                </div>
                {config.browser?.launchArgs && (
                  <Button
                    variant="outline"
                    size="sm"
                    className="border-gray-300 text-gray-700 hover:bg-gray-100"
                    onClick={() => updateBrowserConfig({ 
                      launchArgs: `--disable-blink-features=AutomationControlled
--start-maximized
--ignore-certificate-errors
--ignore-ssl-errors
--disable-web-security
--disable-features=IsolateOrigins,site-per-process
--allow-running-insecure-content
--disable-infobars
--disable-notifications` 
                    })}
                  >
                    恢复默认启动参数
                  </Button>
                )}
                
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200">
                  <div>
                    <Label className="text-gray-700 font-medium">窗口最大化启动</Label>
                    <p className="text-xs text-gray-500 mt-1">
                      开启后浏览器将以最大化窗口启动（占满整个屏幕）
                    </p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={config.browser?.fullscreen ?? false}
                      onChange={(e) => updateBrowserConfig({ fullscreen: e.target.checked })}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200">
                  <div>
                    <Label className="text-gray-700 font-medium">工作流结束后自动关闭浏览器</Label>
                    <p className="text-xs text-gray-500 mt-1">
                      开启后工作流执行完成时将自动关闭浏览器窗口
                    </p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={config.browser?.autoCloseBrowser ?? true}
                      onChange={(e) => {
                        console.log('[GlobalConfig] 切换 autoCloseBrowser:', e.target.checked)
                        updateBrowserConfig({ autoCloseBrowser: e.target.checked })
                        setShowBrowserConfigTip(true)
                        // 立即验证更新
                        setTimeout(() => {
                          const newConfig = useGlobalConfigStore.getState().config
                          console.log('[GlobalConfig] 更新后的配置:', newConfig.browser?.autoCloseBrowser)
                        }, 100)
                      }}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>
                
                {/* 浏览器配置更改提示 */}
                {showBrowserConfigTip && (
                  <div 
                    ref={browserConfigTipRef}
                    className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg animate-fade-in"
                  >
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 w-5 h-5 rounded-full bg-blue-500 flex items-center justify-center mt-0.5">
                        <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </div>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-blue-900 mb-1">配置已保存</p>
                        <p className="text-xs text-blue-700 mb-3">
                          浏览器配置已更新。如果配置未立即生效，请刷新页面后重试。
                        </p>
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            className="h-7 text-xs bg-blue-600 hover:bg-blue-700 text-white"
                            onClick={() => {
                              window.location.reload()
                            }}
                          >
                            立即刷新
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            className="h-7 text-xs border-blue-300 text-blue-700 hover:bg-blue-100"
                            onClick={() => setShowBrowserConfigTip(false)}
                          >
                            我知道了
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </>
          )}

          {activeTab === 'triggers' && (
            <>
              <p className="text-xs text-gray-500 mb-4">
                配置触发器模块的默认值，新建触发器模块时将自动填充这些配置
              </p>
              <div className="space-y-6">
                {/* 邮件触发器配置 */}
                <div className="space-y-4 p-4 bg-blue-50/30 rounded-lg border border-blue-100">
                  <h4 className="font-medium text-gray-800 flex items-center gap-2">
                    <Mail className="w-4 h-4 text-blue-600" />
                    邮件触发器默认配置
                  </h4>
                  <div className="space-y-3">
                    <div className="space-y-2">
                      <Label className="text-gray-700">IMAP服务器</Label>
                      <Input
                        value={config.emailTrigger?.imapServer || ''}
                        onChange={(e) => updateEmailTriggerConfig({ imapServer: e.target.value })}
                        placeholder="imap.qq.com"
                        className="bg-white text-black border-gray-300"
                      />
                      <p className="text-xs text-gray-500">
                        常用：QQ邮箱 imap.qq.com，163邮箱 imap.163.com，Gmail imap.gmail.com
                      </p>
                    </div>
                    <div className="space-y-2">
                      <Label className="text-gray-700">IMAP端口</Label>
                      <Input
                        type="number"
                        value={config.emailTrigger?.imapPort || 993}
                        onChange={(e) => updateEmailTriggerConfig({ imapPort: parseInt(e.target.value) || 993 })}
                        placeholder="993"
                        className="bg-white text-black border-gray-300"
                      />
                      <p className="text-xs text-gray-500">
                        IMAP SSL端口通常为993
                      </p>
                    </div>
                    <div className="space-y-2">
                      <Label className="text-gray-700">邮箱账号</Label>
                      <Input
                        value={config.emailTrigger?.emailAccount || ''}
                        onChange={(e) => updateEmailTriggerConfig({ emailAccount: e.target.value })}
                        placeholder="your@email.com"
                        className="bg-white text-black border-gray-300"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label className="text-gray-700">邮箱密码/授权码</Label>
                      <Input
                        type="password"
                        value={config.emailTrigger?.emailPassword || ''}
                        onChange={(e) => updateEmailTriggerConfig({ emailPassword: e.target.value })}
                        placeholder="邮箱密码或授权码"
                        className="bg-white text-black border-gray-300"
                      />
                      <p className="text-xs text-gray-500">
                        QQ邮箱、163邮箱等需要使用授权码，而非登录密码
                      </p>
                    </div>
                    <div className="space-y-2">
                      <Label className="text-gray-700">默认检查间隔（秒）</Label>
                      <Input
                        type="number"
                        value={config.emailTrigger?.checkInterval || 30}
                        onChange={(e) => updateEmailTriggerConfig({ checkInterval: parseInt(e.target.value) || 30 })}
                        placeholder="30"
                        min="5"
                        className="bg-white text-black border-gray-300"
                      />
                      <p className="text-xs text-gray-500">
                        建议不低于30秒，避免频繁请求被邮件服务器限制
                      </p>
                    </div>
                  </div>
                </div>

                {/* API触发器配置 */}
                <div className="space-y-4 p-4 bg-green-50/30 rounded-lg border border-green-100">
                  <h4 className="font-medium text-gray-800 flex items-center gap-2">
                    <Globe className="w-4 h-4 text-green-600" />
                    API触发器默认配置
                  </h4>
                  <div className="space-y-3">
                    <div className="space-y-2">
                      <Label className="text-gray-700">默认请求头（JSON格式）</Label>
                      <textarea
                        value={config.apiTrigger?.defaultHeaders || '{}'}
                        onChange={(e) => updateApiTriggerConfig({ defaultHeaders: e.target.value })}
                        placeholder='{"Authorization": "Bearer token", "Content-Type": "application/json"}'
                        rows={4}
                        className="w-full px-3 py-2 text-sm font-mono border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-black resize-none"
                      />
                      <p className="text-xs text-gray-500">
                        设置常用的请求头，如认证token等，新建API触发器时会自动填充
                      </p>
                    </div>
                    <div className="space-y-2">
                      <Label className="text-gray-700">默认检查间隔（秒）</Label>
                      <Input
                        type="number"
                        value={config.apiTrigger?.checkInterval || 10}
                        onChange={(e) => updateApiTriggerConfig({ checkInterval: parseInt(e.target.value) || 10 })}
                        placeholder="10"
                        min="1"
                        className="bg-white text-black border-gray-300"
                      />
                      <p className="text-xs text-gray-500">
                        API轮询的默认间隔时间
                      </p>
                    </div>
                  </div>
                </div>

                {/* 文件监控触发器配置 */}
                <div className="space-y-4 p-4 bg-purple-50/30 rounded-lg border border-purple-100">
                  <h4 className="font-medium text-gray-800 flex items-center gap-2">
                    <Folder className="w-4 h-4 text-purple-600" />
                    文件监控触发器默认配置
                  </h4>
                  <div className="space-y-3">
                    <div className="space-y-2">
                      <Label className="text-gray-700">默认监控路径</Label>
                      <div className="flex gap-1">
                        <Input
                          value={config.fileTrigger?.defaultWatchPath || ''}
                          onChange={(e) => updateFileTriggerConfig({ defaultWatchPath: e.target.value })}
                          placeholder="C:\\Users\\Downloads"
                          className="bg-white text-black border-gray-300 flex-1"
                        />
                        <Button
                          type="button"
                          variant="outline"
                          size="icon"
                          className="shrink-0 border-gray-300"
                          onClick={async () => {
                            try {
                              const result = await systemApi.selectFolder('选择默认监控路径')
                              if (result.data?.success && result.data.path) {
                                updateFileTriggerConfig({ defaultWatchPath: result.data.path })
                              }
                            } catch (error) {
                              console.error('选择文件夹失败:', error)
                            }
                          }}
                        >
                          <Folder className="w-4 h-4" />
                        </Button>
                      </div>
                      <p className="text-xs text-gray-500">
                        设置常用的监控路径，如下载文件夹等
                      </p>
                    </div>
                  </div>
                </div>

                <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
                  <p className="text-xs text-amber-800">
                    💡 提示：这些配置会在新建对应触发器模块时自动填充，帮助您快速配置常用的触发器
                  </p>
                </div>
              </div>
            </>
          )}

          {activeTab === 'qq' && (
            <>
              <p className="text-xs text-gray-500 mb-4">
                配置常用的 QQ 号和群号，在使用 QQ 自动化模块时可以快速选择
              </p>
              <div className="space-y-4">
                {/* 联系人列表 */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label className="text-gray-700 font-medium">常用联系人</Label>
                    <Button
                      size="sm"
                      className="h-7 text-xs bg-blue-600 hover:bg-blue-700 text-white"
                      onClick={() => {
                        const newContact = {
                          id: Date.now().toString(),
                          number: '',
                          remark: '',
                          type: 'private' as const
                        }
                        updateQQConfig({
                          contacts: [...(config.qq?.contacts || []), newContact]
                        })
                      }}
                    >
                      <Plus className="w-3 h-3 mr-1" />
                      添加联系人
                    </Button>
                  </div>
                  
                  {(!config.qq?.contacts || config.qq.contacts.length === 0) ? (
                    <div className="text-center py-8 text-gray-400">
                      <MessageCircle className="w-12 h-12 mx-auto mb-2 opacity-50" />
                      <p className="text-sm">暂无常用联系人</p>
                      <p className="text-xs mt-1">点击上方"添加联系人"按钮开始添加</p>
                    </div>
                  ) : (
                    <div className="space-y-2 max-h-[400px] overflow-y-auto">
                      {config.qq.contacts.map((contact, index) => (
                        <div
                          key={contact.id}
                          className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg border border-gray-200 hover:border-gray-300 transition-colors"
                        >
                          {/* 类型选择 */}
                          <select
                            value={contact.type}
                            onChange={(e) => {
                              const newContacts = [...(config.qq?.contacts || [])]
                              newContacts[index] = {
                                ...newContacts[index],
                                type: e.target.value as 'private' | 'group'
                              }
                              updateQQConfig({ contacts: newContacts })
                            }}
                            className="px-2 py-1.5 text-xs border border-gray-300 rounded bg-white text-black w-20"
                          >
                            <option value="private">私聊</option>
                            <option value="group">群聊</option>
                          </select>
                          
                          {/* QQ号/群号 */}
                          <Input
                            value={contact.number}
                            onChange={(e) => {
                              const newContacts = [...(config.qq?.contacts || [])]
                              newContacts[index] = {
                                ...newContacts[index],
                                number: e.target.value
                              }
                              updateQQConfig({ contacts: newContacts })
                            }}
                            placeholder={contact.type === 'group' ? '群号' : 'QQ号'}
                            className="flex-1 h-8 text-sm bg-white text-black border-gray-300"
                          />
                          
                          {/* 备注 */}
                          <Input
                            value={contact.remark}
                            onChange={(e) => {
                              const newContacts = [...(config.qq?.contacts || [])]
                              newContacts[index] = {
                                ...newContacts[index],
                                remark: e.target.value
                              }
                              updateQQConfig({ contacts: newContacts })
                            }}
                            placeholder="备注名称"
                            className="flex-1 h-8 text-sm bg-white text-black border-gray-300"
                          />
                          
                          {/* 删除按钮 */}
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-red-500 hover:text-red-700 hover:bg-red-50"
                            onClick={() => {
                              const newContacts = (config.qq?.contacts || []).filter((_, i) => i !== index)
                              updateQQConfig({ contacts: newContacts })
                            }}
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-xs text-blue-800">
                    💡 提示：添加常用的 QQ 号和群号后，在使用 QQ 自动化模块时可以从下拉列表中快速选择，无需每次手动输入
                  </p>
                </div>
              </div>
            </>
          )}

          {activeTab === 'feishu' && (
            <>
              <p className="text-xs text-gray-500 mb-4">
                配置飞书自动化模块的默认值，新建飞书模块时将自动填充这些配置
              </p>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label className="text-gray-700">默认 App ID</Label>
                  <Input
                    value={config.feishu?.appId || ''}
                    onChange={(e) => updateFeishuConfig({ appId: e.target.value })}
                    placeholder="cli_xxxxxxxxxxxxxxxx"
                    className="bg-white text-black border-gray-300"
                  />
                  <p className="text-xs text-gray-500">
                    飞书应用的唯一标识，可在飞书开放平台的应用详情页面获取
                  </p>
                </div>
                <div className="space-y-2">
                  <Label className="text-gray-700">默认 App Secret</Label>
                  <Input
                    type="password"
                    value={config.feishu?.appSecret || ''}
                    onChange={(e) => updateFeishuConfig({ appSecret: e.target.value })}
                    placeholder="应用密钥"
                    className="bg-white text-black border-gray-300"
                  />
                  <p className="text-xs text-gray-500">
                    飞书应用的密钥，用于获取访问令牌，请妥善保管
                  </p>
                </div>
                
                <div className="p-4 bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-lg space-y-3">
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-5 h-5 rounded-full bg-green-500 flex items-center justify-center mt-0.5">
                      <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-semibold text-green-900 mb-2">如何获取飞书应用凭证</p>
                      <div className="text-xs text-green-800 space-y-1.5">
                        <p><strong>1. 创建飞书应用</strong></p>
                        <p className="pl-3">• 访问 <a href="https://open.feishu.cn/app" target="_blank" rel="noopener noreferrer" className="underline hover:text-green-600">飞书开放平台</a></p>
                        <p className="pl-3">• 点击"创建企业自建应用"</p>
                        <p className="pl-3">• 填写应用名称和描述</p>
                        
                        <p className="pt-2"><strong>2. 获取凭证</strong></p>
                        <p className="pl-3">• 进入应用详情页面</p>
                        <p className="pl-3">• 在"凭证与基础信息"中找到 App ID 和 App Secret</p>
                        
                        <p className="pt-2"><strong>3. 配置权限</strong></p>
                        <p className="pl-3">• 在"权限管理"中添加所需权限</p>
                        <p className="pl-3">• 多维表格：bitable:app</p>
                        <p className="pl-3">• 电子表格：sheets:spreadsheet</p>
                        <p className="pl-3">• 发布应用并等待管理员审核通过</p>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-xs text-blue-800">
                    <strong>💡 使用说明</strong><br/>
                    • 配置后，新建飞书模块时会自动填充 App ID 和 App Secret<br/>
                    • 如果不同的飞书模块需要使用不同的应用，可以在模块中单独修改<br/>
                    • 这些配置仅存储在本地浏览器中，不会上传到服务器
                  </p>
                </div>
              </div>
            </>
          )}
        </div>

        {/* 底部按钮 */}
        <div className="flex items-center justify-between p-4 border-t">
          <Button
            variant="outline"
            size="sm"
            className="border-gray-300 text-gray-700 hover:bg-gray-100"
            onClick={handleReset}
          >
            <RotateCcw className="w-4 h-4 mr-1" />
            重置全部
          </Button>
          <Button
            className="bg-blue-600 text-white hover:bg-blue-700"
            onClick={onClose}
          >
            完成
          </Button>
        </div>
      </div>
      
      {/* 确认对话框 */}
      <ConfirmDialog />
    </div>
  )
}
