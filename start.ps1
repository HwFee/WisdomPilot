[CmdletBinding()]
param(
    [switch]$ReloadBackend
)

$ErrorActionPreference = "Stop"
$ScriptDir = $PSScriptRoot
if (-not $ScriptDir) { $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
$PythonScript = Join-Path $ScriptDir "start_services.py"

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " 智码领航 启动脚本 (PowerShell)" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[提示] 启动前会自动停止旧窗口并清理端口" -ForegroundColor DarkGray
Write-Host "[提示] 按 Ctrl+C 会关闭所有相关进程" -ForegroundColor DarkGray
Write-Host ""

try {
    $pythonVersion = python --version 2>&1
    Write-Host "[检查] Python: $pythonVersion" -ForegroundColor Gray
} catch {
    Write-Host "[错误] 未找到 Python，请先安装 Python 3.10+" -ForegroundColor Red
    exit 1
}

$arguments = @($PythonScript)
if ($ReloadBackend) {
    $arguments += "--reload-backend"
}

& python @arguments
$exitCode = $LASTEXITCODE

if ($exitCode -ne 0) {
    Write-Host ""
    Write-Host "[错误] 启动失败，退出码 $exitCode" -ForegroundColor Red
}

exit $exitCode
