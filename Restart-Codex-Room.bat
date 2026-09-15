@echo off
setlocal
cd /d "%~dp0"

echo Closing the Codex Room browser window if it is currently visible...
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -Command ^
  "$browserNames = @('msedge','chrome','firefox','brave','opera','vivaldi','chromium');" ^
  "$windows = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -like '*Codex Room*' -and $browserNames -contains $_.ProcessName.ToLowerInvariant() });" ^
  "foreach ($window in $windows) { try { [void]$window.CloseMainWindow() } catch {} };" ^
  "if ($windows.Count -gt 0) { Start-Sleep -Milliseconds 500; Write-Host ('Requested close for {0} Codex Room browser window(s).' -f $windows.Count) } else { Write-Host 'No visible Codex Room browser window was found.' }"

call "%~dp0Kill-Codex-Room.bat"
if errorlevel 1 (
  echo Restart aborted because Codex Room did not shut down cleanly.
  pause
  exit /b 1
)

echo Waiting 5 seconds before restart...
timeout /t 5 /nobreak >nul

echo Starting Codex Room...
start "" "%~dp0Start-Codex-Room.cmd"
exit /b 0
