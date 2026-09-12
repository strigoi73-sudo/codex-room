@echo off
setlocal

set "CODEX_ROOM_ROOT=%~dp0"
set "CODEX_ROOM_KILL_DRY_RUN="
if /I "%~1"=="--dry-run" set "CODEX_ROOM_KILL_DRY_RUN=1"

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference = 'Stop';" ^
  "$roomRoot = [IO.Path]::GetFullPath($env:CODEX_ROOM_ROOT).TrimEnd([IO.Path]::DirectorySeparatorChar);" ^
  "$pythonLauncher = Join-Path $roomRoot '.venv\Scripts\python.exe';" ^
  "$startScript = Join-Path $roomRoot 'Start-Codex-Room.cmd';" ^
  "$consoleTitle = 'Codex Room Server';" ^
  "$all = @(Get-CimInstance Win32_Process);" ^
  "$serverRoots = @($all | Where-Object { $_.Name -ieq 'python.exe' -and $_.CommandLine -match '(?i)(?:^|\s)-m\s+codex_room(?:\s|$)' -and $_.CommandLine.IndexOf($pythonLauncher, [StringComparison]::OrdinalIgnoreCase) -ge 0 });" ^
  "$launcherShells = @($all | Where-Object { if ($_.Name -ine 'cmd.exe') { return $false }; if ($_.CommandLine -and $_.CommandLine.IndexOf($startScript, [StringComparison]::OrdinalIgnoreCase) -ge 0) { return $true }; $live = Get-Process -Id $_.ProcessId -ErrorAction SilentlyContinue; return $null -ne $live -and $live.MainWindowTitle -eq $consoleTitle });" ^
  "$seeds = @($serverRoots + $launcherShells | Sort-Object ProcessId -Unique);" ^
  "if (-not $seeds) { Write-Host 'Codex Room is not running and no launcher console remains.'; exit 0 };" ^
  "$targets = @{};" ^
  "$frontier = @($seeds.ProcessId);" ^
  "while ($frontier.Count -gt 0) { $next = @(); foreach ($processId in $frontier) { if ($targets.ContainsKey($processId)) { continue }; $process = $all | Where-Object ProcessId -eq $processId | Select-Object -First 1; if ($null -eq $process) { continue }; $targets[$processId] = $process; $next += @($all | Where-Object ParentProcessId -eq $processId | ForEach-Object ProcessId) }; $frontier = $next };" ^
  "$ordered = @($targets.Values | Sort-Object CreationDate -Descending);" ^
  "if ($env:CODEX_ROOM_KILL_DRY_RUN) { Write-Host 'Dry run - would stop:'; $ordered | Select-Object ProcessId, ParentProcessId, Name, CommandLine | Format-Table -AutoSize -Wrap; exit 0 };" ^
  "foreach ($process in $ordered) { Stop-Process -Id $process.ProcessId -Force -ErrorAction SilentlyContinue };" ^
  "Start-Sleep -Milliseconds 150;" ^
  "$remaining = @(Get-Process -Id @($ordered.ProcessId) -ErrorAction SilentlyContinue);" ^
  "if ($remaining) { throw ('Codex Room shutdown left process ID(s): ' + (($remaining.Id | Sort-Object) -join ', ')) };" ^
  "Write-Host ('Codex Room stopped cleanly. Terminated {0} process(es), including any dedicated launcher console.' -f $ordered.Count)"

if errorlevel 1 (
  echo Failed to stop Codex Room cleanly.
  pause
  exit /b 1
)

exit /b 0
