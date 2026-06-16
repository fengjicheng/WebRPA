import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'
import fs from 'fs'

/**
 * 加载配置文件
 */
function loadConfig() {
  const configPath = path.resolve(__dirname, '../WebRPAConfig.json')
  try {
    if (fs.existsSync(configPath)) {
      const configContent = fs.readFileSync(configPath, 'utf-8')
      const config = JSON.parse(configContent)
      return config.frontend || {}
    } else {
      console.log('[Config] 配置文件不存在，使用默认配置')
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error)
    console.error('[Config] 读取配置文件失败:', errorMessage, '，使用默认配置')
  }
  
  // 返回默认配置
  return {
    host: '0.0.0.0',
    port: 5173
  }
}

// 加载配置
const config = loadConfig()
console.log(`[Config] 前端服务配置: host=${config.host}, port=${config.port}`)

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: config.host || '0.0.0.0', // 允许局域网访问
    port: config.port || 5173,
    strictPort: true, // 端口被占用时报错，而不是自动尝试下一个端口
  },
  // 优化 Monaco Editor 打包
  optimizeDeps: {
    include: ['monaco-editor'],
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return
          if (id.includes('monaco-editor') || id.includes('@monaco-editor')) return 'monaco-editor'
          // reactflow 必须在 react 判断之前（名字含 react）
          if (id.includes('reactflow') || id.includes('@reactflow') || id.includes('@xyflow')) return 'reactflow'
          // React 全家桶必须在同一 chunk：react / react-dom / scheduler / jsx-runtime
          // 否则 react-dom 给 scheduler 设置 unstable_now 时会因跨 chunk 初始化顺序报错
          if (
            id.includes('/react-dom/') || id.includes('/react/') ||
            id.includes('/scheduler/') || id.includes('/react-is/') ||
            id.includes('use-sync-external-store')
          ) return 'react-vendor'
          if (id.includes('elkjs')) return 'elkjs'
          if (id.includes('xlsx') || id.includes('exceljs')) return 'excel-vendor'
          return 'vendor'
        },
      },
    },
  },
})
