@echo off
setlocal
set "ROOT=%~dp0"
set "PYTHON=%ROOT%.venv\Scripts\python.exe"
if not exist "%PYTHON%" (
  echo Codex Room virtual environment not found: "%PYTHON%" 1>&2
  exit /b 2
)
"%PYTHON%" -m codex_room.maintenance %*
exit /b %ERRORLEVEL%
