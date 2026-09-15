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
exit /b 0
