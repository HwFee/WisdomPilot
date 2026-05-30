[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$ScriptDir = $PSScriptRoot
if (-not $ScriptDir) { $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
$PythonScript = Join-Path $ScriptDir "stop_services.py"

Write-Host ""
Write-Host "==================================================" -ForegroundColor Yellow
Write-Host " 智码领航 停止脚本 (PowerShell)" -ForegroundColor Yellow
Write-Host "==================================================" -ForegroundColor Yellow
Write-Host ""

try {
    $pythonVersion = python --version 2>&1
    Write-Host "[检查] Python: $pythonVersion" -ForegroundColor Gray
} catch {
    Write-Host "[错误] 未找到 Python，请先安装 Python 3.10+" -ForegroundColor Red
    exit 1
}

& python $PythonScript
$exitCode = $LASTEXITCODE

if ($exitCode -ne 0) {
    Write-Host ""
    Write-Host "[警告] 停止脚本返回退出码 $exitCode" -ForegroundColor Yellow
}

exit $exitCode
