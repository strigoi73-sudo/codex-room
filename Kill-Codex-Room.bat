@echo off
setlocal

set "CODEX_ROOM_ROOT=%~dp0"
set "CODEX_ROOM_KILL_DRY_RUN="
if /I "%~1"=="--dry-run" set "CODEX_ROOM_KILL_DRY_RUN=1"

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference = 'Stop';" ^
  "$roomRoot = [IO.Path]::GetFullPath($env:CODEX_ROOM_ROOT).TrimEnd([IO.Path]::DirectorySeparatorChar);" ^
  "$launcher = Join-Path $roomRoot '.venv\Scripts\python.exe';" ^
  "$all = @(Get-CimInstance Win32_Process);" ^
  "$roots = @($all | Where-Object { $_.Name -ieq 'python.exe' -and $_.CommandLine -match '(?i)(?:^|\s)-m\s+codex_room(?:\s|$)' -and $_.CommandLine.IndexOf($launcher, [StringComparison]::OrdinalIgnoreCase) -ge 0 });" ^
  "if (-not $roots) { Write-Host 'Codex Room server is not running.'; exit 0 };" ^
  "$targets = @{};" ^
  "$frontier = @($roots.ProcessId);" ^
  "while ($frontier.Count -gt 0) { $next = @(); foreach ($processId in $frontier) { if ($targets.ContainsKey($processId)) { continue }; $process = $all | Where-Object ProcessId -eq $processId | Select-Object -First 1; if ($null -eq $process) { continue }; $targets[$processId] = $process; $next += @($all | Where-Object ParentProcessId -eq $processId | ForEach-Object ProcessId) }; $frontier = $next };" ^
  "$ordered = @($targets.Values | Sort-Object CreationDate -Descending);" ^
  "if ($env:CODEX_ROOM_KILL_DRY_RUN) { Write-Host 'Dry run - would stop:'; $ordered | Select-Object ProcessId, ParentProcessId, Name, CommandLine | Format-Table -AutoSize -Wrap; exit 0 };" ^
  "foreach ($process in $ordered) { Stop-Process -Id $process.ProcessId -Force -ErrorAction SilentlyContinue };" ^
  "Write-Host ('Codex Room stopped. Terminated {0} process(es).' -f $ordered.Count)"

if errorlevel 1 (
  echo Failed to stop Codex Room.
  pause
  exit /b 1
)

if /I not "%~1"=="--dry-run" pause
exit /b 0
