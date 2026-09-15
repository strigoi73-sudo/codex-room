@echo off
setlocal
cd /d "%~dp0"
title Codex Room Server
if not exist ".venv\Scripts\python.exe" (
  echo Codex Room environment is missing. Re-run the project setup.
  pause
  exit /b 1
)
if defined CODEX_ROOM_CODEX_BIN (
  if not exist "%CODEX_ROOM_CODEX_BIN%" (
    echo Configured Codex runtime override is missing: %CODEX_ROOM_CODEX_BIN%
    echo Clear CODEX_ROOM_CODEX_BIN or point it to a compatible codex.exe and try again.
    pause
    exit /b 1
  )
  echo Using Codex runtime override: %CODEX_ROOM_CODEX_BIN%
) else (
  echo Using SDK-pinned Codex runtime.
)
echo Codex Room agents: gpt-5.6-terra with high reasoning
set "PATH=%CD%;%PATH%"
".venv\Scripts\python.exe" -m codex_room %*
