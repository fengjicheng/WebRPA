# WebRPA Offline Deployment Quick Test

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "  WebRPA Offline Test" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/3] Running offline verification..." -ForegroundColor Yellow
node verify-offline.js

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Verification failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Verification passed!" -ForegroundColor Green
Write-Host ""

Write-Host "[2/3] Checking Monaco Editor config..." -ForegroundColor Yellow

$files = @(
    "frontend/src/components/workflow/PythonEditorDialog.tsx",
    "frontend/src/components/workflow/JsEditorDialog.tsx",
    "frontend/src/components/workflow/InjectJsEditorDialog.tsx"
)

$allConfigured = $true
foreach ($file in $files) {
    if (Test-Path $file) {
        $content = Get-Content $file -Raw
        if ($content -match "loader\.config\(\{\s*monaco\s*\}\)") {
            Write-Host "  OK: $file" -ForegroundColor Green
        } else {
            Write-Host "  FAIL: $file" -ForegroundColor Red
            $allConfigured = $false
        }
    }
}

if (-not $allConfigured) {
    Write-Host ""
    Write-Host "Monaco Editor config incomplete!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Monaco Editor config OK!" -ForegroundColor Green
Write-Host ""

Write-Host "[3/3] Checking Vite config..." -ForegroundColor Yellow

$viteConfig = "frontend/vite.config.ts"
if (Test-Path $viteConfig) {
    $content = Get-Content $viteConfig -Raw
    if ($content -match "monaco-editor") {
        Write-Host "  OK: Vite config includes Monaco Editor" -ForegroundColor Green
    } else {
        Write-Host "  WARN: Vite config may be missing Monaco Editor" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "  All tests passed!" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Next steps:" -ForegroundColor Blue
Write-Host "  1. Rebuild frontend: cd frontend && npm run build"
Write-Host "  2. Start the project and test"
Write-Host "  3. Open browser DevTools (F12) -> Network tab"
Write-Host "  4. Test code editors, confirm no CDN requests"
Write-Host ""
