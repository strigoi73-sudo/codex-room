@echo off
setlocal
set "ROOT=%~dp0"
set "PYTHON=%ROOT%.venv\Scripts\python.exe"
if not exist "%PYTHON%" (
  echo Codex Room virtual environment not found: "%PYTHON%" 1>&2
  echo Run this from the normal Codex Room checkout after creating/installing .venv. 1>&2
  exit /b 2
)
"%PYTHON%" "%ROOT%codex_room\codex_usage.py" %*
exit /b %ERRORLEVEL%
