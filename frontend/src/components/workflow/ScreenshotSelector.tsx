import { useState, useRef, useEffect } from 'react'
import { X } from 'lucide-react'

interface ScreenshotSelectorProps {
  screenshot: string
  width: number
  height: number
  onConfirm: (croppedImage: string) => void
  onCancel: () => void
}

export function ScreenshotSelector({
  screenshot,
  width,
  height,
  onConfirm,
  onCancel
}: ScreenshotSelectorProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [isSelecting, setIsSelecting] = useState(false)
  const [startPos, setStartPos] = useState({ x: 0, y: 0 })
  const [endPos, setEndPos] = useState({ x: 0, y: 0 })
  const [img, setImg] = useState<HTMLImageElement | null>(null)

  // 加载图片
  useEffect(() => {
    const image = new Image()
    image.src = screenshot
    image.onload = () => {
      setImg(image)
      drawCanvas(image)
    }
  }, [screenshot])

  // 绘制画布
  const drawCanvas = (image: HTMLImageElement, selection?: { x1: number; y1: number; x2: number; y2: number }) => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // 清空画布
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    // 绘制截图
    ctx.drawImage(image, 0, 0, width, height)

    // 绘制半透明遮罩
    ctx.fillStyle = 'rgba(0, 0, 0, 0.5)'
    ctx.fillRect(0, 0, width, height)

    // 如果有选择区域，清除遮罩并绘制边框
    if (selection) {
      const { x1, y1, x2, y2 } = selection
      const selWidth = Math.abs(x2 - x1)
      const selHeight = Math.abs(y2 - y1)
      const selX = Math.min(x1, x2)
      const selY = Math.min(y1, y2)

      // 清除选择区域的遮罩
      ctx.clearRect(selX, selY, selWidth, selHeight)
      ctx.drawImage(image, selX, selY, selWidth, selHeight, selX, selY, selWidth, selHeight)

      // 绘制选择框
      ctx.strokeStyle = '#3b82f6'
      ctx.lineWidth = 2
      ctx.strokeRect(selX, selY, selWidth, selHeight)

      // 绘制尺寸信息
      ctx.fillStyle = '#3b82f6'
      ctx.font = '14px Arial'
      const sizeText = `${selWidth} × ${selHeight}`
      const textWidth = ctx.measureText(sizeText).width
      ctx.fillRect(selX, selY - 25, textWidth + 10, 20)
      ctx.fillStyle = 'white'
      ctx.fillText(sizeText, selX + 5, selY - 10)
    }
  }

  // 鼠标按下
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current
    if (!canvas) return

    const rect = canvas.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top

    setIsSelecting(true)
    setStartPos({ x, y })
    setEndPos({ x, y })
  }

  // 鼠标移动
  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isSelecting || !img) return

    const canvas = canvasRef.current
    if (!canvas) return

    const rect = canvas.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top

    setEndPos({ x, y })
    drawCanvas(img, { x1: startPos.x, y1: startPos.y, x2: x, y2: y })
  }

  // 鼠标释放
  const handleMouseUp = () => {
    setIsSelecting(false)
  }

  // 确认选择
  const handleConfirm = () => {
    if (!img) return

    const x1 = Math.min(startPos.x, endPos.x)
    const y1 = Math.min(startPos.y, endPos.y)
    const x2 = Math.max(startPos.x, endPos.x)
    const y2 = Math.max(startPos.y, endPos.y)
    const selWidth = x2 - x1
    const selHeight = y2 - y1

    // 检查选择区域是否有效
    if (selWidth < 10 || selHeight < 10) {
      alert('选择区域太小，请重新选择')
      return
    }

    // 创建临时画布裁剪图片
    const tempCanvas = document.createElement('canvas')
    tempCanvas.width = selWidth
    tempCanvas.height = selHeight
    const tempCtx = tempCanvas.getContext('2d')
    if (!tempCtx) return

    // 裁剪图片
    tempCtx.drawImage(img, x1, y1, selWidth, selHeight, 0, 0, selWidth, selHeight)

    // 转换为base64
    const croppedImage = tempCanvas.toDataURL('image/png')
    onConfirm(croppedImage)
  }

  // 键盘事件
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onCancel()
      } else if (e.key === 'Enter') {
        handleConfirm()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [startPos, endPos, img])

  return (
    <div className="fixed inset-0 z-[9999] bg-black/80 flex items-center justify-center">
      <div className="relative w-full h-full flex flex-col">
        {/* 顶部提示栏 */}
        <div className="absolute top-0 left-0 right-0 bg-blue-600 text-white py-3 px-6 flex items-center justify-between z-10">
          <div className="flex items-center gap-4">
            <span className="text-lg font-semibold">WebRPA 截图工具</span>
            <span className="text-sm opacity-90">拖动鼠标选择区域，按 Enter 确认，按 ESC 取消</span>
          </div>
          <button
            onClick={onCancel}
            className="p-2 hover:bg-white/20 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* 画布区域 */}
        <div className="flex-1 flex items-center justify-center pt-16">
          <canvas
            ref={canvasRef}
            width={width}
            height={height}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            className="cursor-crosshair"
            style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }}
          />
        </div>

        {/* 底部按钮栏 */}
        <div className="absolute bottom-0 left-0 right-0 bg-gray-900/90 py-4 px-6 flex items-center justify-center gap-4 z-10">
          <button
            onClick={onCancel}
            className="px-6 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
          >
            取消 (ESC)
          </button>
          <button
            onClick={handleConfirm}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            确认 (Enter)
          </button>
        </div>
      </div>
    </div>
  )
}
