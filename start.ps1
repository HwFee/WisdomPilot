# AIcodiingTeach 启动脚本 (PowerShell 7)
# 用法: .\start.ps1
# 内部调用 start_services.py 工作

$ErrorActionPreference = "Stop"
$ScriptDir = $PSScriptRoot
if (-not $ScriptDir) { $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
$PythonScript = Join-Path $ScriptDir "start_services.py"

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " AIcodiingTeach 启动脚本" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[检查] Python: $pythonVersion" -ForegroundColor Gray
} catch {
    Write-Host "[错误] 未找到 Python，请先安装 Python 3.8+" -ForegroundColor Red
    exit 1
}

# 运行 Python 启动器（前台运行，Ctrl+C 关闭）
python $PythonScript
