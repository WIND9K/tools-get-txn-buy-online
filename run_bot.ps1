# run_bot.ps1
$ErrorActionPreference = "Stop"

$ROOT   = Split-Path -Parent $MyInvocation.MyCommand.Path
$VENVPY = Join-Path $ROOT ".venv\Scripts\python.exe"
$SCRIPT = Join-Path $ROOT "src\bots\listener_main.py"
$LOGDIR = Join-Path $ROOT "logs"

if (!(Test-Path $VENVPY))  { Write-Error "Không tìm thấy Python trong .venv: $VENVPY" }
if (!(Test-Path $SCRIPT))  { Write-Error "Không tìm thấy script: $SCRIPT" }
if (!(Test-Path $LOGDIR))  { New-Item -ItemType Directory -Force -Path $LOGDIR | Out-Null }

$ts  = Get-Date -Format "yyyyMMdd_HHmmss"
$LOG = Join-Path $LOGDIR "bot_$ts.log"
Write-Host "Starting bot... (log: $LOG)"

Push-Location $ROOT

while ($true) {
  $cmd = "`"$VENVPY`" `"$SCRIPT`" >> `"$LOG`" 2>&1"
  & cmd /c $cmd
  $exit = $LASTEXITCODE
  Add-Content -Path $LOG -Value "Bot exited with code $exit. Restarting in 5s..."
  Start-Sleep -Seconds 5
}
