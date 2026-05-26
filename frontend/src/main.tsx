import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { installGlobalTooltip } from './lib/globalTooltip'

// 安装全局 tooltip 拦截：把所有 title 属性自动转成 WebRPA 主题浮窗
installGlobalTooltip()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
