# WebRPA 工作流仓库服务

这是 WebRPA 的工作流仓库后端服务，用于存储和分享用户创建的工作流。

## 功能特性

- 📤 发布工作流到公共仓库
- 📥 下载其他用户分享的工作流
- 🔍 搜索和浏览工作流
- 🏷️ 分类和标签系统
- 🛡️ 完善的安全措施

## 安全措施

- 速率限制：防止恶意请求
- 输入验证：所有输入都经过严格验证
- XSS 防护：过滤恶意脚本
- 敏感信息过滤：自动隐藏 API Key、密码等
- 内容哈希：防止重复发布
- IP 记录：追踪异常行为

## Linux 服务器部署

### 1. 安装依赖

```bash
cd FrameworkHub
npm install
```

### 2. 直接运行

```bash
npm start
```

### 3. 使用 PM2 守护进程（推荐）

```bash
# 安装 PM2
npm install -g pm2

# 启动服务
npm run pm2

# 查看日志
npm run pm2:logs

# 重启服务
npm run pm2:restart

# 停止服务
npm run pm2:stop

# 设置开机自启
pm2 startup
pm2 save
```

### 4. 使用 systemd（可选）

创建服务文件 `/etc/systemd/system/framework-hub.service`：

```ini
[Unit]
Description=WebRPA Framework Hub
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/FrameworkHub
ExecStart=/usr/bin/node src/index.js
Restart=on-failure
RestartSec=10
Environment=NODE_ENV=production
Environment=PORT=3000

[Install]
WantedBy=multi-user.target
```

然后启用服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable framework-hub
sudo systemctl start framework-hub
```

### 5. Nginx 反向代理配置

```nginx
server {
    listen 80;
    server_name hub.pmhs.top;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| PORT | 服务端口 | 3000 |
| NODE_ENV | 运行环境 | development |

## API 接口

### 获取工作流列表
```
GET /api/workflows
参数：
  - page: 页码（默认1）
  - limit: 每页数量（默认20，最大50）
  - category: 分类筛选
  - search: 搜索关键词
  - sort: 排序方式（newest/popular/downloads）
```

### 获取分类列表
```
GET /api/workflows/categories
```

### 获取工作流详情
```
GET /api/workflows/:id
```

### 下载工作流
```
POST /api/workflows/:id/download
```

### 发布工作流
```
POST /api/workflows
Body: {
  name: string,        // 必填，2-50字符
  description: string, // 可选，最多500字符
  author: string,      // 可选，最多30字符
  category: string,    // 可选，预设分类
  tags: string[],      // 可选，最多5个标签
  content: object      // 必填，工作流内容
}
```

### 检查工作流是否存在
```
POST /api/workflows/check
Body: { content: object }
```

### 举报工作流
```
POST /api/workflows/:id/report
Body: {
  reason: string,      // 举报原因
  description: string  // 详细描述
}
```

## 数据存储

数据存储在 `data/workflows.db`（SQLite 数据库），包含：
- workflows: 工作流表
- download_logs: 下载记录表
- reports: 举报记录表
