import { useState, useEffect } from 'react'
import { Loader2, Play } from 'lucide-react'
import { VariableInput } from './variable-input'
import { Button } from './button'
import { cn } from '@/lib/utils'
import { phoneApi } from '@/services/api'

interface PhoneCoordinateInputProps {
  xValue: string
  yValue: string
  onXChange: (value: string) => void
  onYChange: (value: string) => void
  deviceId?: string  // 指定的设备ID
  xPlaceholder?: string
  yPlaceholder?: string
  className?: string
}

export function PhoneCoordinateInput({
  xValue,
  yValue,
  onXChange,
  onYChange,
  deviceId: propDeviceId,  // 从props接收的设备ID
  xPlaceholder = '手机屏幕X坐标',
  yPlaceholder = '手机屏幕Y坐标',
  className,
}: PhoneCoordinateInputProps) {
  const [isTesting, setIsTesting] = useState(false)
  const [statusText, setStatusText] = useState('')
  const [defaultDeviceId, setDefaultDeviceId] = useState<string | null>(null)

  // 获取默认设备（仅在没有指定deviceId时使用）
  const checkDevice = async () => {
    try {
      const result = await phoneApi.getDevices()
      if (result.data?.devices && result.data.devices.length > 0) {
        setDefaultDeviceId(result.data.devices[0].id)
        return result.data.devices[0].id
      }
      return null
    } catch {
      return null
    }
  }

  useEffect(() => {
    // 只有在没有指定deviceId时才获取默认设备
    if (!propDeviceId) {
      checkDevice()
    }
  }, [propDeviceId])

  const handleTest = async () => {
    const x = parseInt(xValue)
    const y = parseInt(yValue)
    
    if (isNaN(x) || isNaN(y)) {
      setStatusText('❌ 请先输入有效的坐标')
      setTimeout(() => setStatusText(''), 2000)
      return
    }
    
    // 使用指定的deviceId，如果没有则使用默认设备
    const targetDeviceId = propDeviceId || defaultDeviceId
    
    if (!targetDeviceId) {
      setStatusText('❌ 未检测到设备')
      setTimeout(() => setStatusText(''), 2000)
      return
    }
    
    setIsTesting(true)
    setStatusText(`正在测试坐标 (${x}, ${y})...`)
    
    try {
      const result = await phoneApi.testCoordinate(x, y, targetDeviceId)
      
      if (result.data?.success) {
        setStatusText(`✅ 已在设备 ${targetDeviceId} 上点击坐标 (${x}, ${y})`)
      } else {
        setStatusText(`❌ 测试失败: ${result.data?.error || result.error || '未知错误'}`)
      }
      setTimeout(() => setStatusText(''), 3000)
    } catch (error) {
      console.error('Failed to test:', error)
      setStatusText('❌ 测试失败')
      setTimeout(() => setStatusText(''), 2000)
    } finally {
      setIsTesting(false)
    }
  }

  return (
    <div className={cn('space-y-2', className)}>
      <div className="flex items-center gap-2">
        <div className="flex-1 space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground w-6">X:</span>
            <VariableInput
              value={xValue}
              onChange={onXChange}
              placeholder={xPlaceholder}
            />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground w-6">Y:</span>
            <VariableInput
              value={yValue}
              onChange={onYChange}
              placeholder={yPlaceholder}
            />
          </div>
        </div>
        <div className="flex flex-col gap-1">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleTest}
            disabled={isTesting || !xValue || !yValue || !(propDeviceId || defaultDeviceId)}
            className="h-16 px-3 flex items-center justify-center gap-1"
            title="在手机上测试当前坐标"
          >
            {isTesting ? (
              <>
                <Loader2 className="h-3 w-3 animate-spin" />
                <span className="text-xs whitespace-nowrap">测试中</span>
              </>
            ) : (
              <>
                <Play className="h-3 w-3" />
                <span className="text-xs whitespace-nowrap">测试</span>
              </>
            )}
          </Button>
        </div>
      </div>
      {statusText ? (
        <p className={cn(
          'text-xs',
          statusText.includes('✅') ? 'text-green-600' : 
          statusText.includes('❌') ? 'text-red-600' : 
          'text-blue-600'
        )}>
          {statusText}
        </p>
      ) : (
        <p className="text-xs text-muted-foreground">
          请先到「手机镜像」中启动设备，然后通过查看「指针位置」来手动填写上方的坐标输入框。点击「测试」可验证坐标是否正确。
        </p>
      )}
    </div>
  )
}
