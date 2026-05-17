import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { phoneApi } from '@/services/api'
import { Smartphone, RefreshCw, Monitor, AlertCircle, CheckCircle, Loader2, X, Crop } from 'lucide-react'
import { PhoneScreenshotCropper } from './PhoneScreenshotCropper'

interface PhoneMirrorDialogProps {
  open: boolean
  onClose: () => void
}

interface Device {
  id: string
  model: string
  status: string
}

export function PhoneMirrorDialog({ open, onClose }: PhoneMirrorDialogProps) {
  const [devices, setDevices] = useState<Device[]>([])
  const [error, setError] = useState<string | null>(null)
  const [mirrorStatus, setMirrorStatus] = useState<{
    devices?: Record<string, { running: boolean; recording: boolean }>
    running: boolean
    device_id: string | null
  }>({ running: false, device_id: null })
  const [refreshing, setRefreshing] = useState(false)
  const [showCropper, setShowCropper] = useState(false)
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>('')
  
  // 每个设备独立的加载状态
  const [deviceLoadingStates, setDeviceLoadingStates] = useState<Record<string, boolean>>({})
  
  // 从localStorage读取指针位置设置，默认为true
  const [enablePointerLocation, setEnablePointerLocation] = useState(() => {
    const saved = localStorage.getItem('phone_mirror_enable_pointer_location')
    return saved !== null ? saved === 'true' : true
  })

  // 当enablePointerLocation改变时，保存到localStorage
  useEffect(() => {
    localStorage.setItem('phone_mirror_enable_pointer_location', String(enablePointerLocation))
  }, [enablePointerLocation])

  // 加载设备列表
  const loadDevices = async () => {
    setRefreshing(true)
    setError(null)
    try {
      const result = await phoneApi.getDevices()
      if (result.error) {
        setError(result.error)
        setDevices([])
      } else {
        setDevices(result.data?.devices || [])
      }
    } catch (err) {
      setError('获取设备列表失败')
      setDevices([])
    } finally {
      setRefreshing(false)
    }
  }

  // 加载镜像状态
  const loadMirrorStatus = async () => {
    try {
      const result = await phoneApi.getMirrorStatus()
      console.log('[PhoneMirror] 镜像状态:', JSON.stringify(result.data?.status, null, 2))
      if (result.data?.status) {
        setMirrorStatus(result.data.status)
      }
    } catch (err) {
      console.error('获取镜像状态失败:', err)
    }
  }

  // 启动镜像
  const startMirror = async (deviceId: string) => {
    console.log('[PhoneMirror] 启动镜像:', deviceId, 'enablePointerLocation:', enablePointerLocation)
    // 设置该设备的加载状态
    setDeviceLoadingStates(prev => ({ ...prev, [deviceId]: true }))
    setError(null)
    try {
      const result = await phoneApi.startMirror(deviceId, 1920, '8M', enablePointerLocation)
      console.log('[PhoneMirror] 启动镜像结果:', JSON.stringify(result, null, 2))
      if (result.error) {
        // 显示详细的错误信息
        console.error('[PhoneMirror] 启动失败:', result.error)
        setError(result.error)
      } else {
        console.log('[PhoneMirror] 启动成功，刷新状态...')
        // 启动成功，更新状态
        await loadMirrorStatus()
      }
    } catch (err) {
      console.error('[PhoneMirror] 启动镜像异常:', err)
      setError('启动镜像失败')
    } finally {
      // 清除该设备的加载状态
      setDeviceLoadingStates(prev => ({ ...prev, [deviceId]: false }))
    }
  }

  // 停止镜像
  const stopMirror = async (deviceId: string) => {
    // 设置该设备的加载状态
    setDeviceLoadingStates(prev => ({ ...prev, [deviceId]: true }))
    setError(null)
    try {
      const result = await phoneApi.stopMirror(deviceId)
      if (result.error) {
        setError(result.error)
      } else {
        await loadMirrorStatus()
      }
    } catch (err) {
      setError('停止镜像失败')
    } finally {
      // 清除该设备的加载状态
      setDeviceLoadingStates(prev => ({ ...prev, [deviceId]: false }))
    }
  }
  
  // 检查设备是否正在运行镜像
  const isDeviceRunning = (deviceId: string): boolean => {
    return mirrorStatus.devices?.[deviceId]?.running || false
  }

  // 对话框打开时加载数据
  useEffect(() => {
    if (open) {
      loadDevices()
      loadMirrorStatus()
    }
  }, [open])

  if (!open) return null

  return (
    <>
      <div 
        className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4 animate-fade-in"
        onClick={onClose}
      >
      <div 
        className="bg-white text-black border border-gray-200 rounded-xl shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden animate-scale-in"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 标题栏 */}
        <div className="bg-[hsl(var(--card))] flex items-center justify-between px-6 py-4 border-b">
          <div className="flex items-center gap-2">
            <Smartphone className="w-6 h-6 text-emerald-600" />
            <h2 className="text-xl font-semibold text-gray-900">手机屏幕镜像</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* 内容区域 */}
        <div className="p-6 overflow-y-auto max-h-[calc(80vh-80px)]">
          <div className="space-y-6">
          {/* 说明 */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex gap-3">
              <Monitor className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h3 className="font-semibold text-blue-900 mb-2">功能说明</h3>
                <div className="space-y-2 text-sm text-blue-700">
                  <p>
                    启动手机屏幕镜像后，您可以在电脑上查看和操作手机屏幕。
                    镜像窗口会自动置顶显示，方便您同时使用电脑和手机。
                  </p>
                  
                  <div className="mt-3 pt-3 border-t border-blue-200">
                    <p className="font-semibold text-blue-900 mb-1.5">指针位置辅助功能</p>
                    <p className="mb-2">
                      启用后，手机屏幕上会自动显示"指针位置"信息，帮助您精准定位坐标：
                    </p>
                    <ul className="space-y-1.5 ml-4 list-disc">
                      <li>
                        <span className="font-medium">长按屏幕不松手</span>，将指针拖拽到需要操作的位置
                      </li>
                      <li>
                        查看屏幕<span className="font-medium">左上角的 X 和 Y 坐标值</span>，即为当前触摸点的精确坐标
                      </li>
                      <li className="text-orange-700 font-medium">
                        注意：必须保持长按状态，一旦松手，左上角显示的就会变成 dX 和 dY（滑动距离），而不是坐标位置
                      </li>
                    </ul>
                    <p className="mt-2 text-xs text-blue-600">
                      提示：关闭镜像窗口后，指针位置显示会自动关闭
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* 指针位置设置 */}
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <div className="flex-1">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={enablePointerLocation}
                    onChange={(e) => setEnablePointerLocation(e.target.checked)}
                    className="w-4 h-4 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500"
                  />
                  <span className="font-medium text-amber-900">启动镜像时自动开启"指针位置"</span>
                </label>
                <p className="text-sm text-amber-700 mt-1.5 ml-6">
                  开启后，镜像启动时会自动在手机屏幕顶部显示触摸坐标信息。如果您不需要查看坐标，可以取消勾选此选项。
                </p>
              </div>
            </div>
          </div>

          {/* 错误信息 */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex gap-3">
                <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <h3 className="font-semibold text-red-900 mb-2">操作失败</h3>
                  <pre className="text-sm text-red-700 whitespace-pre-wrap font-mono bg-red-100 p-3 rounded">
                    {error}
                  </pre>
                </div>
              </div>
            </div>
          )}

          {/* 设备列表 */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-gray-900">已连接的设备</h3>
              <Button
                variant="outline"
                size="sm"
                onClick={loadDevices}
                disabled={refreshing}
              >
                <RefreshCw className={`w-4 h-4 mr-1 ${refreshing ? 'animate-spin' : ''}`} />
                刷新
              </Button>
            </div>

            {devices.length === 0 ? (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
                <Smartphone className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-600 mb-2">未检测到设备</p>
                <p className="text-sm text-gray-500">
                  请确保手机已通过 USB 连接并开启了 USB 调试
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                {devices.map((device) => {
                  const isRunning = isDeviceRunning(device.id)
                  const isLoading = deviceLoadingStates[device.id] || false
                  
                  return (
                    <div
                      key={device.id}
                      className={`bg-white border rounded-lg p-4 transition-all ${
                        isRunning 
                          ? 'border-green-300 bg-green-50' 
                          : 'border-gray-200 hover:border-emerald-300'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                            isRunning ? 'bg-green-200' : 'bg-emerald-100'
                          }`}>
                            <Smartphone className={`w-5 h-5 ${
                              isRunning ? 'text-green-700' : 'text-emerald-600'
                            }`} />
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <h4 className="font-medium text-gray-900">{device.model || device.id}</h4>
                              {isRunning && (
                                <span className="px-2 py-0.5 bg-green-200 text-green-800 text-xs font-medium rounded-full flex items-center gap-1">
                                  <CheckCircle className="w-3 h-3" />
                                  镜像中
                                </span>
                              )}
                            </div>
                            <p className="text-sm text-gray-500">
                              {device.id} • {device.status}
                            </p>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            onClick={() => {
                              setSelectedDeviceId(device.id)
                              setShowCropper(true)
                            }}
                            disabled={isLoading}
                            className="border-orange-300 text-orange-700 hover:bg-orange-50"
                          >
                            <Crop className="w-4 h-4 mr-1" />
                            截图裁剪
                          </Button>
                          {isRunning ? (
                            <Button
                              variant="outline"
                              onClick={() => stopMirror(device.id)}
                              disabled={isLoading}
                              className="border-red-300 text-red-700 hover:bg-red-50"
                            >
                              {isLoading ? (
                                <>
                                  <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                                  停止中...
                                </>
                              ) : (
                                <>
                                  <X className="w-4 h-4 mr-1" />
                                  停止镜像
                                </>
                              )}
                            </Button>
                          ) : (
                            <Button
                              onClick={() => startMirror(device.id)}
                              disabled={isLoading}
                              className="bg-[hsl(var(--card))]"
                            >
                              {isLoading ? (
                                <>
                                  <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                                  启动中...
                                </>
                              ) : (
                                <>
                                  <Monitor className="w-4 h-4 mr-1" />
                                  启动镜像
                                </>
                              )}
                            </Button>
                          )}
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
          </div>
        </div>
      </div>
      </div>

      {/* 截图裁剪对话框 */}
      <PhoneScreenshotCropper
        open={showCropper}
        onClose={() => setShowCropper(false)}
        deviceId={selectedDeviceId}
      />
    </>
  )
}
