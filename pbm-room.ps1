[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$TaskId,

    [ValidateSet('Prepare', 'Run', 'Complete')]
    [string]$Phase = 'Prepare',

    [string]$RunId,

    [string]$Base = 'http://127.0.0.1:8765'
)

$ErrorActionPreference = 'Stop'

$Root = $PSScriptRoot
$Python = Join-Path $Root '.venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Codex Room virtual environment not found: $Python"
}

Set-Location $Root

function Save-Json {
    param(
        [Parameter(Mandatory = $true)]$Value,
        [Parameter(Mandatory = $true)][string]$Path
    )

    $Value | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Get-PBMRoom {
    param([Parameter(Mandatory = $true)][string]$RoomId)

    Invoke-RestMethod -Method Get -Uri "$Base/api/rooms/$RoomId"
}

function Wait-PBMRoomTerminal {
    param(
        [Parameter(Mandatory = $true)][string]$RoomId,
        [int]$TimeoutSeconds = 3600
    )

    $terminal = @('finished', 'error', 'stopped', 'paused')
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)

    do {
        $room = Get-PBMRoom -RoomId $RoomId
        if ($terminal -contains [string]$room.status) {
            return $room
        }

        Start-Sleep -Seconds 1
    } while ((Get-Date) -lt $deadline)

    throw "PBM Room $RoomId did not reach a terminal state within $TimeoutSeconds seconds."
}

if (-not $RunId) {
    if ($Phase -ne 'Prepare') {
        throw 'RunId is required for Room Run/Complete.'
    }

    $runJson = & $Python -m codex_room.pbm new-run --json
    $runExit = $LASTEXITCODE
    if ($runExit -ne 0) {
        throw "PBM new-run failed with exit code $runExit."
    }

    $run = ($runJson -join [Environment]::NewLine) | ConvertFrom-Json
    $RunId = [string]$run.run_id
}

$ArmDir = Join-Path $Root ("output\pbm\runs\{0}\{1}\room" -f $RunId, $TaskId)
$SetupPath = Join-Path $ArmDir 'room-setup.json'

if ($Phase -eq 'Prepare') {
    $health = Invoke-RestMethod -Method Get -Uri "$Base/api/health"
    if (-not $health.ok) {
        throw 'Codex Room health endpoint did not report ok=true.'
    }

    $taskJson = & $Python -m codex_room.pbm task --task-id $TaskId --json
    $taskExit = $LASTEXITCODE
    if ($taskExit -ne 0) {
        throw "PBM task lookup failed with exit code $taskExit."
    }

    $task = ($taskJson -join [Environment]::NewLine) | ConvertFrom-Json
    New-Item -ItemType Directory -Force -Path $ArmDir | Out-Null

    $body = @{
        title = "PBM $($task.version) — $TaskId"
        topic = [string]$task.prompt
        auto_start = $false
        max_turns = [int]$task.room_max_turns
        max_consecutive_passes = 3
        inactivity_seconds = 900
        starting_agent = 'agent_c'
        completion_policy = 'auto_settle'
        required_contributors = @()
    } | ConvertTo-Json -Depth 20

    $created = Invoke-RestMethod -Method Post -Uri "$Base/api/rooms" -ContentType 'application/json' -Body $body

    $roomId = [string]$created.id
    $roundId = [string]$created.active_round_id
    $workspace = Join-Path $Root ("data\rooms\{0}\shared" -f $roomId)

    & $Python -m codex_room.pbm prepare --run-id $RunId --task-id $TaskId --arm room --workspace $workspace --evidence-dir $ArmDir --allow-existing
    $prepareExit = $LASTEXITCODE
    if ($prepareExit -ne 0) {
        throw "PBM Room fixture preparation failed with exit code $prepareExit."
    }

    $setup = [ordered]@{
        run_id = $RunId
        task_id = $TaskId
        room_id = $roomId
        round_id = $roundId
        workspace = $workspace
        prepared_at = (Get-Date).ToUniversalTime().ToString('o')
    }
    Save-Json $setup $SetupPath
    Save-Json $created (Join-Path $ArmDir 'room-created.json')
    Save-Json $health (Join-Path $ArmDir 'health-before.json')

    Write-Host ''
    Write-Host '=== PBM ROOM ARM PREPARED ===' -ForegroundColor Cyan
    Write-Host "Run ID:    $RunId"
    Write-Host "Task:      $TaskId"
    Write-Host "Room:      $roomId"
    Write-Host "Round:     $roundId"
    Write-Host "Workspace: $workspace"
    Write-Host ''
    Write-Host 'No benchmark model turn has been started.' -ForegroundColor Green
    Write-Host 'To execute this Room arm, run:' -ForegroundColor Yellow
    Write-Host ('.\pbm-room.ps1 -Phase Run -TaskId "{0}" -RunId "{1}"' -f $TaskId, $RunId)
}

if (($Phase -eq 'Run') -or ($Phase -eq 'Complete')) {
    if (-not (Test-Path -LiteralPath $SetupPath)) {
        throw "PBM Room setup not found: $SetupPath"
    }

    $setup = Get-Content -LiteralPath $SetupPath -Raw | ConvertFrom-Json
    $roomId = [string]$setup.room_id
    $roundId = [string]$setup.round_id

    if ($Phase -eq 'Run') {
        Invoke-RestMethod -Method Post -Uri "$Base/api/rooms/$roomId/rounds/$roundId/start" | Out-Null
    }

    $final = Wait-PBMRoomTerminal -RoomId $roomId
    Save-Json $final (Join-Path $ArmDir 'room-final.json')

    $exportPath = Join-Path $ArmDir 'room-export.json'
    Invoke-WebRequest -UseBasicParsing -Method Get -Uri "$Base/api/rooms/$roomId/export?format=json" -OutFile $exportPath

    & $Python -m codex_room.pbm room-complete --run-id $RunId --task-id $TaskId --room-id $roomId --round-id $roundId --export $exportPath
    $completeExit = $LASTEXITCODE
    if ($completeExit -ne 0) {
        throw "PBM Room completion failed with exit code $completeExit."
    }

    & $Python -m codex_room.pbm report --run-id $RunId | Out-Null
    $reportExit = $LASTEXITCODE
    if ($reportExit -ne 0) {
        throw "PBM report refresh failed with exit code $reportExit."
    }

    Write-Host ''
    Write-Host '=== PBM ROOM ARM CAPTURED ===' -ForegroundColor Green
    Write-Host "Run ID: $RunId"
    Write-Host "Task:   $TaskId"
    Write-Host "Room:   $roomId"
    Write-Host "Status: $($final.status)"
    Write-Host "Result: $(Join-Path $ArmDir 'result.json')"
    Write-Host "Report: $(Join-Path $Root ("output\pbm\runs\{0}\pbm-report.md" -f $RunId))"
}
