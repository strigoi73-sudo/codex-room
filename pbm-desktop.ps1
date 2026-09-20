[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$TaskId,

    [ValidateSet('Prepare', 'Complete')]
    [string]$Phase = 'Prepare',

    [string]$RunId,

    [string]$ThreadId
)

$ErrorActionPreference = 'Stop'

$Root = $PSScriptRoot
$Python = Join-Path $Root '.venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Codex Room virtual environment not found: $Python"
}

Set-Location $Root

if (-not $RunId) {
    if ($Phase -ne 'Prepare') {
        throw 'RunId is required for Desktop completion.'
    }

    $runJson = & $Python -m codex_room.pbm new-run --json
    $runExit = $LASTEXITCODE
    if ($runExit -ne 0) {
        throw "PBM new-run failed with exit code $runExit."
    }

    $run = ($runJson -join [Environment]::NewLine) | ConvertFrom-Json
    $RunId = [string]$run.run_id
}

$ArmDir = Join-Path $Root ("output\pbm\runs\{0}\{1}\desktop" -f $RunId, $TaskId)
$Workspace = Join-Path $ArmDir 'workspace'

if ($Phase -eq 'Prepare') {
    New-Item -ItemType Directory -Force -Path $ArmDir | Out-Null

    & $Python -m codex_room.pbm prepare --run-id $RunId --task-id $TaskId --arm desktop --workspace $Workspace --evidence-dir $ArmDir
    $prepareExit = $LASTEXITCODE
    if ($prepareExit -ne 0) {
        throw "PBM Desktop preparation failed with exit code $prepareExit."
    }

    $promptPath = Join-Path $ArmDir 'prompt.txt'
    $prompt = Get-Content -LiteralPath $promptPath -Raw
    Set-Clipboard -Value $prompt

    Write-Host ''
    Write-Host '=== PBM DESKTOP ARM PREPARED ===' -ForegroundColor Cyan
    Write-Host "Run ID:    $RunId"
    Write-Host "Task:      $TaskId"
    Write-Host "Workspace: $Workspace"
    Write-Host ''
    Write-Host 'In Codex Desktop:' -ForegroundColor Yellow
    Write-Host '1. Open a NEW Codex local chat.'
    Write-Host '2. Open the exact workspace folder shown above.'
    Write-Host '3. Leave Codex Desktop on its normal/default naturalistic configuration.'
    Write-Host '4. Paste the benchmark prompt from the clipboard and run it once.'
    Write-Host '5. Do not provide substantive follow-up guidance.'
    Write-Host ''
    Write-Host 'After Desktop finishes, run:' -ForegroundColor Yellow
    Write-Host ('.\pbm-desktop.ps1 -Phase Complete -TaskId "{0}" -RunId "{1}"' -f $TaskId, $RunId)
}

if ($Phase -eq 'Complete') {
    $arguments = @(
        '-m', 'codex_room.pbm', 'desktop-complete',
        '--run-id', $RunId,
        '--task-id', $TaskId
    )

    if ($ThreadId) {
        $arguments += @('--thread-id', $ThreadId)
    }

    & $Python @arguments
    $completeExit = $LASTEXITCODE
    if ($completeExit -ne 0) {
        throw "PBM Desktop completion failed with exit code $completeExit."
    }

    & $Python -m codex_room.pbm report --run-id $RunId | Out-Null
    $reportExit = $LASTEXITCODE
    if ($reportExit -ne 0) {
        throw "PBM report refresh failed with exit code $reportExit."
    }

    Write-Host ''
    Write-Host '=== PBM DESKTOP ARM CAPTURED ===' -ForegroundColor Green
    Write-Host "Run ID: $RunId"
    Write-Host "Task:   $TaskId"
    Write-Host "Result: $(Join-Path $ArmDir 'result.json')"
    Write-Host "Report: $(Join-Path $Root ("output\pbm\runs\{0}\pbm-report.md" -f $RunId))"
}
