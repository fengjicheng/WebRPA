# Git commit script for offline deployment changes

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "  Committing Offline Changes" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Add modified files
Write-Host "Adding modified files..." -ForegroundColor Yellow

git add frontend/src/components/workflow/PythonEditorDialog.tsx
git add frontend/src/components/workflow/JsEditorDialog.tsx
git add frontend/src/components/workflow/InjectJsEditorDialog.tsx
git add frontend/vite.config.ts

# Add new documentation and tools
Write-Host "Adding documentation and tools..." -ForegroundColor Yellow

git add OFFLINE_VERIFICATION.md
git add README_OFFLINE.md
git add "离线部署完成说明.md"
git add verify-offline.js
git add quick-test.ps1
git add test-monaco-offline.html

# Show status
Write-Host ""
Write-Host "Files to be committed:" -ForegroundColor Green
git status --short

Write-Host ""
Write-Host "Creating commit..." -ForegroundColor Yellow

# Create commit
git commit -m "feat: 完全离线化Monaco Editor配置

修改内容：
- 配置Monaco Editor使用本地包而不是CDN
- 优化Vite构建配置
- 添加离线部署验证工具
- 添加详细的离线部署文档

修改文件：
- frontend/src/components/workflow/PythonEditorDialog.tsx
- frontend/src/components/workflow/JsEditorDialog.tsx
- frontend/src/components/workflow/InjectJsEditorDialog.tsx
- frontend/vite.config.ts

新增文件：
- OFFLINE_VERIFICATION.md - 技术文档
- README_OFFLINE.md - 快速指南
- 离线部署完成说明.md - 中文说明
- verify-offline.js - 自动化验证脚本
- quick-test.ps1 - 快速测试脚本
- test-monaco-offline.html - 浏览器测试页面

验证结果：
✅ 无外部CDN引用
✅ Monaco Editor配置正确
✅ 可在纯内网环境运行"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "================================" -ForegroundColor Green
    Write-Host "  Commit successful!" -ForegroundColor Green
    Write-Host "================================" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "Commit failed!" -ForegroundColor Red
    Write-Host ""
    exit 1
}
