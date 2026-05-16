import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { X, Image as ImageIcon, AlertCircle, Loader2, RotateCcw } from 'lucide-react'

interface ScreenshotNameDialogProps {
  defaultName: string
  onConfirm: (name: string) => void
  onCancel: () => void
  onRetry?: () => void
}

export function ScreenshotNameDialog({
  defaultName,
  onConfirm,
  onCancel,
  onRetry
}: ScreenshotNameDialogProps) {
  const [name, setName] = useState(defaultName.replace('.png', ''))

  const handleConfirm = () => {
    if (name.trim()) {
      onConfirm(name.trim())
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleConfirm()
    } else if (e.key === 'Escape') {
      onCancel()
    }
  }

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-white rounded-xl shadow-2xl w-[500px] max-w-[90vw] overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* 标题栏 */}
        <div className="bg-gradient-to-r from-green-500 to-emerald-600 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
              <ImageIcon className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">截图成功</h2>
              <p className="text-sm text-white/80">请为截图命名</p>
            </div>
          </div>
          <button
            onClick={onCancel}
            className="w-8 h-8 rounded-lg hover:bg-white/20 flex items-center justify-center transition-colors"
          >
            <X className="w-5 h-5 text-white" />
          </button>
        </div>

        {/* 内容区 */}
        <div className="p-6 space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700">
              截图名称（不含扩展名）
            </label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="请输入截图名称"
              className="text-base"
              autoFocus
            />
            <p className="text-xs text-gray-500">
              保存为: {name.trim() || '未命名'}.png
            </p>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <p className="text-sm text-blue-800">
              💡 提示：截图已保存到图像资源，您可以在底部面板的"图像资源"标签中查看
            </p>
          </div>
        </div>

        {/* 按钮栏 */}
        <div className="bg-gray-50 px-6 py-4 flex items-center justify-end gap-3">
          <Button
            variant="outline"
            onClick={onCancel}
            className="min-w-[100px]"
          >
            取消
          </Button>
          <Button
            onClick={handleConfirm}
            className="min-w-[100px] bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700"
          >
            确定
          </Button>
        </div>
      </div>
    </div>
  )
}

interface ScreenshotErrorDialogProps {
  error: string
  cancelled?: boolean
  onRetry: () => void
  onCancel: () => void
}

export function ScreenshotErrorDialog({
  error,
  cancelled,
  onRetry,
  onCancel
}: ScreenshotErrorDialogProps) {
  const [retrying, setRetrying] = useState(false)

  const handleRetry = async () => {
    setRetrying(true)
    try {
      await new Promise(resolve => setTimeout(resolve, 500))
      onRetry()
    } finally {
      setRetrying(false)
    }
  }

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-white rounded-xl shadow-2xl w-[500px] max-w-[90vw] overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* 标题栏 */}
        <div className="bg-gradient-to-r from-red-500 to-rose-600 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
              <AlertCircle className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">截图失败</h2>
              <p className="text-sm text-white/80">
                {cancelled ? '您取消了截图' : '截图过程中出现问题'}
              </p>
            </div>
          </div>
          <button
            onClick={onCancel}
            className="w-8 h-8 rounded-lg hover:bg-white/20 flex items-center justify-center transition-colors"
          >
            <X className="w-5 h-5 text-white" />
          </button>
        </div>

        {/* 内容区 */}
        <div className="p-6 space-y-4">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-sm text-red-800 font-medium mb-2">错误信息：</p>
            <p className="text-sm text-red-700 font-mono break-words">
              {error === 'timeout'
                ? '等待超时（90秒）- 您可能没有完成截图，或截图工具未正确启动'
                : error}
            </p>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <p className="text-sm text-blue-800">
              💡 <strong>故障排查：</strong>
            </p>
            <ul className="text-sm text-blue-700 mt-2 space-y-1 ml-4 list-disc">
              <li>确保 Windows 截图工具已启用</li>
              <li>尝试手动按 Win+Shift+S 测试</li>
              <li>如果仍然失败，请重试</li>
            </ul>
          </div>
        </div>

        {/* 按钮栏 */}
        <div className="bg-gray-50 px-6 py-4 flex items-center justify-end gap-3">
          <Button
            variant="outline"
            onClick={onCancel}
            className="min-w-[100px]"
          >
            关闭
          </Button>
          <Button
            onClick={handleRetry}
            disabled={retrying}
            className="min-w-[120px] bg-gradient-to-r from-blue-500 to-cyan-600 hover:from-blue-600 hover:to-cyan-700"
          >
            {retrying ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                重试中...
              </>
            ) : (
              <>
                <RotateCcw className="w-4 h-4 mr-2" />
                重试截图
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  )
}
