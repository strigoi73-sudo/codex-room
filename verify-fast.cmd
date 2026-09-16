@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0verify-local.ps1" -Mode Fast %*
exit /b %ERRORLEVEL%
