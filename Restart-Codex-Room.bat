@echo off
setlocal
cd /d "%~dp0"

call "%~dp0Kill-Codex-Room.bat"
if errorlevel 1 (
  echo Restart aborted because Codex Room did not shut down cleanly.
  pause
  exit /b 1
)

echo Waiting 5 seconds before restart...
timeout /t 5 /nobreak >nul

echo Starting Codex Room without opening a new browser tab...
start "" "%~dp0Start-Codex-Room.cmd" --no-browser

echo Waiting for Codex Room API readiness...
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference = 'SilentlyContinue';" ^
  "$deadline = [DateTime]::UtcNow.AddSeconds(30);" ^
  "while ([DateTime]::UtcNow -lt $deadline) {" ^
  "  try {" ^
  "    $health = Invoke-RestMethod -Method Get -Uri 'http://127.0.0.1:8765/api/health' -TimeoutSec 2;" ^
  "    if ($null -ne $health -and $health.ok -eq $true) {" ^
  "      Write-Host 'Codex Room API is ready.';" ^
  "      exit 0" ^
  "    }" ^
  "  } catch {};" ^
  "  Start-Sleep -Milliseconds 500" ^
  "};" ^
  "Write-Host 'Codex Room API did not become ready within 30 seconds.';" ^
  "exit 1"

if errorlevel 1 (
  echo Restart failed because Codex Room API readiness was not confirmed.
  call "%~dp0Kill-Codex-Room.bat"
  exit /b 1
)

exit /b 0
