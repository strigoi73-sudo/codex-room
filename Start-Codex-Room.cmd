@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Codex Room environment is missing. Re-run the project setup.
  pause
  exit /b 1
)
if not defined CODEX_ROOM_CODEX_BIN set "CODEX_ROOM_CODEX_BIN=%LOCALAPPDATA%\OpenAI\Codex\bin\8e5b6932251c2c1c\codex.exe"
if not exist "%CODEX_ROOM_CODEX_BIN%" (
  echo Configured Codex runtime is missing: %CODEX_ROOM_CODEX_BIN%
  echo Set CODEX_ROOM_CODEX_BIN to a current codex.exe and try again.
  pause
  exit /b 1
)
echo Using Codex runtime: %CODEX_ROOM_CODEX_BIN%
echo Codex Room agents: gpt-5.6-terra with high reasoning
".venv\Scripts\python.exe" -m codex_room
