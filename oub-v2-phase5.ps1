[CmdletBinding()]
param(
    [ValidateSet("o2-1", "o2-2", "o2-3")]
    [string[]]$TaskIds = @("o2-1", "o2-2", "o2-3"),

    [ValidatePattern("^[0-9a-fA-F]{40}$")]
    [string]$ExpectedHead,

    [ValidateRange(10, 300)]
    [int]$HeartbeatSeconds = 30
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $false

$RepoRoot = $PSScriptRoot
$RoomBase = "http://127.0.0.1:8765"
$TerminalRoomStatuses = @("finished", "stopped", "error", "archived")
$TaskResults = @()
$ActiveRunId = $null

function Assert-Phase5 {
    param(
        [bool]$Condition,
        [string]$Message
    )

    if (-not $Condition) {
        throw "PHASE 5 FAIL: $Message"
    }
}

function Invoke-OubV2Json {
    param(
        [Parameter(Mandatory)]
        [string[]]$Arguments
    )

    $rawLines = & .\.venv\Scripts\python.exe -m codex_room.oub_v2 @Arguments 2>&1
    $oubExit = $LASTEXITCODE
    $raw = ($rawLines | Out-String).Trim()

    if ($oubExit -ne 0) {
        throw "OUB v2 command failed: $($Arguments -join ' ')\n$raw"
    }

    try {
        return ($raw | ConvertFrom-Json -Depth 100)
    }
    catch {
        throw "OUB v2 returned non-JSON output: $($Arguments -join ' ')\n$raw"
    }
}

function Invoke-OubV2GradeWithHeartbeat {
    param(
        [Parameter(Mandatory)]
        [string]$TaskId,

        [Parameter(Mandatory)]
        [string]$Workspace
    )

    $python = Join-Path $RepoRoot ".venv\Scripts\python.exe"

    $psi = [System.Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = $python
    $psi.WorkingDirectory = $RepoRoot
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true

    foreach ($argument in @(
        "-m",
        "codex_room.oub_v2",
        "grade",
        "--task-id",
        $TaskId,
        "--workspace",
        $Workspace
    )) {
        [void]$psi.ArgumentList.Add($argument)
    }

    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $psi

    Write-Host "Starting isolated WSL grader..."
    [void]$process.Start()

    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()
    $heartbeat = 0

    try {
        while (-not $process.HasExited) {
            Start-Sleep -Seconds $HeartbeatSeconds

            if (-not $process.HasExited) {
                $heartbeat++
                Write-Host ""
                Write-Host ("[grade heartbeat {0}] {1} still running - {2}" -f $heartbeat, $TaskId, (Get-Date -Format "HH:mm:ss"))

                $activity = & wsl.exe -e sh -lc @'
ps -eo pid,ppid,etime,stat,pcpu,pmem,args |
grep -E 'grade_workspace_native|uv (venv|pip)|pytest|cargo|rustc|git clone|python.*pytest' |
grep -v grep
'@ 2>&1
                $activityExit = $LASTEXITCODE
                $activityText = ($activity | Out-String).Trim()

                if ($activityText -match "Failed to start the systemd user session") {
                    throw "WSL reported a failed systemd user session during grading. Run .\Repair-WSL-Codex-Room.ps1 before retrying."
                }

                if ($activityExit -eq 0 -and -not [string]::IsNullOrWhiteSpace($activityText)) {
                    Write-Host $activityText
                }
                else {
                    Write-Host "No matching grader child process visible at this instant."
                }
            }
        }

        $process.WaitForExit()
    }
    catch {
        if (-not $process.HasExited) {
            $process.Kill($true)
            $process.WaitForExit()
        }

        throw
    }

    $stdout = $stdoutTask.GetAwaiter().GetResult().Trim()
    $stderr = $stderrTask.GetAwaiter().GetResult().Trim()
    $gradeExit = $process.ExitCode

    if ($gradeExit -ne 0) {
        throw "OUB v2 grade command exited with code $gradeExit.\nSTDOUT:\n$stdout\n\nSTDERR:\n$stderr"
    }

    try {
        return ($stdout | ConvertFrom-Json -Depth 100)
    }
    catch {
        throw "OUB v2 grade command returned non-JSON output.\nSTDOUT:\n$stdout\n\nSTDERR:\n$stderr"
    }
}

function Get-GitText {
    param(
        [Parameter(Mandatory)]
        [string]$Workspace,

        [Parameter(Mandatory)]
        [string[]]$Arguments
    )

    $lines = & git -C $Workspace @Arguments 2>&1
    $gitExit = $LASTEXITCODE
    $text = ($lines | Out-String).Trim()

    if ($gitExit -ne 0) {
        throw "Git failed in ${Workspace}: git $($Arguments -join ' ')\n$text"
    }

    return $text
}

function Test-RoomHealth {
    try {
        $health = Invoke-RestMethod -Method Get -Uri "$RoomBase/api/health" -TimeoutSec 2
        return ($null -ne $health -and $health.ok -eq $true)
    }
    catch {
        return $false
    }
}

function Assert-WslHealthy {
    $probe = & wsl.exe -e sh -c 'printf ok' 2>&1
    $probeExit = $LASTEXITCODE
    $probeText = ($probe | Out-String).Trim()

    Assert-Phase5 -Condition ($probeExit -eq 0) -Message "WSL probe failed with exit code $probeExit."

    if ($probeText -match "Failed to start the systemd user session") {
        throw "PHASE 5 FAIL: WSL reports a failed systemd user session. Run .\Repair-WSL-Codex-Room.ps1 before retrying."
    }

    Assert-Phase5 -Condition ($probeText -eq "ok") -Message "WSL probe returned unexpected output: $probeText"
}

Push-Location $RepoRoot
try {
    Write-Host "=== I-028 OUB V2 PHASE 5 MECHANICAL TASK RUNNER ==="
    Write-Host "Tasks: $($TaskIds -join ', ')"
    Write-Host "No Desktop benchmark worker will be started."
    Write-Host "No Room Round will be started."
    Write-Host ""

    Write-Host "=== PRECHECK ==="

    $headLines = & git rev-parse HEAD 2>&1
    $headExit = $LASTEXITCODE
    $head = ($headLines | Out-String).Trim()

    Assert-Phase5 -Condition ($headExit -eq 0) -Message "Could not resolve repository HEAD."

    if ($ExpectedHead) {
        Assert-Phase5 -Condition ($head -eq $ExpectedHead) -Message "Expected HEAD $ExpectedHead; found $head."
    }

    $trackedStatus = @(& git status --porcelain --untracked-files=no)
    $statusExit = $LASTEXITCODE
    Assert-Phase5 -Condition ($statusExit -eq 0) -Message "Could not inspect tracked repository status."
    Assert-Phase5 -Condition ($trackedStatus.Count -eq 0) -Message "Tracked repository changes are present."

    Assert-WslHealthy

    Write-Host "HEAD: $head"
    Write-Host "Tracked tree: clean"
    Write-Host "WSL probe: PASS"

    Write-Host ""
    Write-Host "=== CODEX ROOM RUNTIME ==="

    if (-not (Test-RoomHealth)) {
        $startScript = Join-Path $RepoRoot "Start-Codex-Room.cmd"
        $quotedStartScript = '"' + $startScript + '"'
        $server = Start-Process -FilePath "cmd.exe" -ArgumentList @("/c", $quotedStartScript) -WorkingDirectory $RepoRoot -PassThru

        $healthy = $false
        for ($i = 0; $i -lt 120; $i++) {
            if (Test-RoomHealth) {
                $healthy = $true
                break
            }

            if ($server.HasExited) {
                break
            }

            Start-Sleep -Milliseconds 250
        }

        Assert-Phase5 -Condition $healthy -Message "Codex Room failed to become healthy."
    }

    Write-Host "Codex Room health: PASS"

    Write-Host ""
    Write-Host "=== OUB V2 AUDIT ==="

    $audit = Invoke-OubV2Json -Arguments @("audit")
    Assert-Phase5 -Condition ($audit.ok -eq $true) -Message "OUB v2 audit failed."
    Assert-Phase5 -Condition ($audit.current_pointer -eq "v1") -Message "OUB v2 CURRENT is not v1 during Phase 5."

    Write-Host "Audit: PASS"
    Write-Host "Fingerprint: $($audit.benchmark_fingerprint)"
    Write-Host "CURRENT: $($audit.current_pointer)"

    $manifest = Get-Content -LiteralPath (Join-Path $RepoRoot "benchmarks\oub\v2\manifest.json") -Raw | ConvertFrom-Json -Depth 100

    Add-Type -AssemblyName System.IO.Compression.FileSystem

    foreach ($taskId in $TaskIds) {
        Write-Host ""
        Write-Host "============================================================"
        Write-Host "PHASE 5 TASK: $taskId"
        Write-Host "============================================================"

        $prepared = Invoke-OubV2Json -Arguments @("prepare", "--task-id", $taskId, "--no-start")
        $ActiveRunId = [string]$prepared.run_id

        Assert-Phase5 -Condition ($prepared.action -eq "prepared_mechanical_only") -Message "$taskId did not use mechanical-only preparation."

        $runRoot = Join-Path $RepoRoot "output\oub\v2-runs\$ActiveRunId"
        $statePath = Join-Path $runRoot "state.json"
        Assert-Phase5 -Condition (Test-Path -LiteralPath $statePath) -Message "$taskId state.json is missing."

        $state = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json -Depth 100
        Assert-Phase5 -Condition ($state.mechanical_only -eq $true) -Message "$taskId is not marked mechanical-only."
        Assert-Phase5 -Condition ($state.workers_started -eq $false) -Message "$taskId spawned benchmark workers."
        Assert-Phase5 -Condition ($null -eq $state.desktop.worker_pid) -Message "$taskId spawned a Desktop worker."
        Assert-Phase5 -Condition ($null -eq $state.room.worker_pid) -Message "$taskId spawned a Room worker."

        $desktopWorkspace = [string]$state.desktop.workspace
        $roomWorkspace = [string]$state.room.workspace
        $roomId = [string]$state.room.room_id
        $roundId = [string]$state.room.round_id

        $task = $manifest.tasks | Where-Object { $_.id -eq $taskId } | Select-Object -First 1
        Assert-Phase5 -Condition ($null -ne $task) -Message "$taskId is missing from the manifest."
        $baseCommit = [string]$task.base_commit

        Write-Host "Run: $ActiveRunId"
        Write-Host "Frozen base: $baseCommit"

        Write-Host ""
        Write-Host "--- Equivalent starting state ---"

        $desktopHead = Get-GitText -Workspace $desktopWorkspace -Arguments @("rev-parse", "HEAD")
        $roomHead = Get-GitText -Workspace $roomWorkspace -Arguments @("rev-parse", "HEAD")
        $desktopTree = Get-GitText -Workspace $desktopWorkspace -Arguments @("rev-parse", "HEAD^{tree}")
        $roomTree = Get-GitText -Workspace $roomWorkspace -Arguments @("rev-parse", "HEAD^{tree}")
        $desktopStatus = Get-GitText -Workspace $desktopWorkspace -Arguments @("status", "--porcelain", "--untracked-files=all")
        $roomStatus = Get-GitText -Workspace $roomWorkspace -Arguments @("status", "--porcelain", "--untracked-files=all")

        Assert-Phase5 -Condition ($desktopHead -eq $baseCommit) -Message "$taskId Desktop HEAD differs from frozen base."
        Assert-Phase5 -Condition ($roomHead -eq $baseCommit) -Message "$taskId Room HEAD differs from frozen base."
        Assert-Phase5 -Condition ($desktopTree -eq $roomTree) -Message "$taskId starting trees differ."
        Assert-Phase5 -Condition ([string]::IsNullOrWhiteSpace($desktopStatus)) -Message "$taskId Desktop workspace starts dirty."
        Assert-Phase5 -Condition ([string]::IsNullOrWhiteSpace($roomStatus)) -Message "$taskId Room workspace starts dirty."

        $desktopMission = Join-Path $desktopWorkspace "BENCHMARK.md"
        $roomMission = Join-Path $roomWorkspace "BENCHMARK.md"
        $desktopMissionHash = (Get-FileHash -LiteralPath $desktopMission -Algorithm SHA256).Hash.ToLowerInvariant()
        $roomMissionHash = (Get-FileHash -LiteralPath $roomMission -Algorithm SHA256).Hash.ToLowerInvariant()

        Assert-Phase5 -Condition ($desktopMissionHash -eq $roomMissionHash) -Message "$taskId mission hashes differ."

        Write-Host "HEAD identity: PASS"
        Write-Host "Tree identity: PASS"
        Write-Host "Mission identity: PASS"
        Write-Host "Clean starting source: PASS"

        Write-Host ""
        Write-Host "--- Repository-local cross-host Git contract ---"

        $winAutocrlfLines = & git -C $desktopWorkspace config --get core.autocrlf 2>&1
        $winAutocrlfExit = $LASTEXITCODE
        $winAutocrlf = ($winAutocrlfLines | Out-String).Trim()

        Assert-Phase5 -Condition ($winAutocrlfExit -eq 0) -Message "$taskId Windows Git could not read core.autocrlf."
        Assert-Phase5 -Condition ($winAutocrlf -eq "false") -Message "$taskId Windows Git sees core.autocrlf=$winAutocrlf."

        $wslPathLines = & wsl.exe wslpath -a -u $desktopWorkspace 2>&1
        $wslPathExit = $LASTEXITCODE
        $wslWorkspace = ($wslPathLines | Out-String).Trim()

        Assert-Phase5 -Condition ($wslPathExit -eq 0) -Message "$taskId wslpath failed."
        Assert-Phase5 -Condition ($wslWorkspace -notmatch "Failed to start the systemd user session") -Message "$taskId wslpath reported the systemd user-session failure."
        Assert-Phase5 -Condition ($wslWorkspace.StartsWith("/")) -Message "$taskId wslpath returned unexpected output: $wslWorkspace"

        $wslAutocrlfLines = & wsl.exe -e git -C $wslWorkspace config --get core.autocrlf 2>&1
        $wslAutocrlfExit = $LASTEXITCODE
        $wslAutocrlf = ($wslAutocrlfLines | Out-String).Trim()

        Assert-Phase5 -Condition ($wslAutocrlfExit -eq 0) -Message "$taskId WSL Git could not read core.autocrlf."
        Assert-Phase5 -Condition ($wslAutocrlf -eq "false") -Message "$taskId WSL Git sees core.autocrlf=$wslAutocrlf."

        Write-Host "Windows Git core.autocrlf: $winAutocrlf"
        Write-Host "WSL Git core.autocrlf:     $wslAutocrlf"
        Write-Host "Cross-host Git contract: PASS"

        Write-Host ""
        Write-Host "--- Hidden-test isolation ---"

        foreach ($feature in @($task.features)) {
            $hiddenRelative = ([string]$feature.tests_file).Replace("/", [IO.Path]::DirectorySeparatorChar)

            Assert-Phase5 -Condition (-not (Test-Path -LiteralPath (Join-Path $desktopWorkspace $hiddenRelative))) -Message "$taskId hidden test leaked into Desktop workspace."
            Assert-Phase5 -Condition (-not (Test-Path -LiteralPath (Join-Path $roomWorkspace $hiddenRelative))) -Message "$taskId hidden test leaked into Room workspace."
        }

        Write-Host "Hidden-test isolation: PASS"

        Write-Host ""
        Write-Host "--- Prepared Room has not started ---"

        $roomSnapshot = Invoke-RestMethod -Method Get -Uri "$RoomBase/api/rooms/$roomId" -TimeoutSec 10
        Assert-Phase5 -Condition ($roomSnapshot.active_round_id -eq $roundId) -Message "$taskId active Round identity changed."
        Assert-Phase5 -Condition ($roomSnapshot.status -eq "preparing") -Message "$taskId Room started unexpectedly."
        Assert-Phase5 -Condition ($roomSnapshot.active_round.status -eq "preparing") -Message "$taskId Round started unexpectedly."

        Write-Host "Room:  preparing"
        Write-Host "Round: preparing"
        Write-Host "No cognition started: PASS"

        Write-Host ""
        Write-Host "--- Mechanical candidate replay sentinel ---"

        $readme = Get-ChildItem -LiteralPath $desktopWorkspace -File |
            Where-Object { $_.Name -match '^README(?:\.md)?$' } |
            Select-Object -First 1

        Assert-Phase5 -Condition ($null -ne $readme) -Message "$taskId has no root README for replay sentinel."

        $newline = [Environment]::NewLine

        [IO.File]::AppendAllText(
            $readme.FullName,
            $newline + "<!-- OUB Phase 5 replay sentinel: $taskId -->" + $newline,
            [Text.UTF8Encoding]::new($false)
        )

        $untrackedName = "PHASE5_CANDIDATE_REPLAY_SENTINEL.txt"
        $untrackedPath = Join-Path $desktopWorkspace $untrackedName

        [IO.File]::WriteAllText(
            $untrackedPath,
            "OUB Phase 5 replay sentinel for $taskId" + $newline,
            [Text.UTF8Encoding]::new($false)
        )

        Write-Host ""
        Write-Host "--- Cross-host candidate view before grading ---"

        $windowsCandidateStatus = Get-GitText -Workspace $desktopWorkspace -Arguments @("status", "--short", "--untracked-files=all")

        $wslCandidateLines = & wsl.exe -e git -C $wslWorkspace status --short --untracked-files=all 2>&1
        $wslCandidateExit = $LASTEXITCODE
        $wslCandidateStatus = ($wslCandidateLines | Out-String).Trim()

        Assert-Phase5 -Condition ($wslCandidateExit -eq 0) -Message "$taskId WSL Git status failed."
        Assert-Phase5 -Condition ($wslCandidateStatus -notmatch "Failed to start the systemd user session") -Message "$taskId WSL Git reported the systemd user-session failure."

        $windowsCandidateLines = @($windowsCandidateStatus -split '\r?\n' | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
        $wslCandidateStatusLines = @($wslCandidateStatus -split '\r?\n' | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })

        Assert-Phase5 -Condition ($windowsCandidateLines.Count -eq 2) -Message "$taskId Windows Git sees unexpected candidate paths:\n$windowsCandidateStatus"
        Assert-Phase5 -Condition ($wslCandidateStatusLines.Count -eq 2) -Message "$taskId WSL Git sees unexpected candidate paths:\n$wslCandidateStatus"

        Write-Host "Windows candidate view:"
        Write-Host $windowsCandidateStatus
        Write-Host ""
        Write-Host "WSL candidate view:"
        Write-Host $wslCandidateStatus
        Write-Host ""
        Write-Host "Cross-host candidate view: PASS"

        Write-Host ""
        Write-Host "--- Isolated WSL grading/replay ---"
        Write-Host "A heartbeat will print every $HeartbeatSeconds seconds."

        $grade = Invoke-OubV2GradeWithHeartbeat -TaskId $taskId -Workspace $desktopWorkspace

        Assert-Phase5 -Condition ($grade.schema -eq "oub-v2-grade-v1") -Message "$taskId grader returned wrong schema."
        Assert-Phase5 -Condition ($grade.base_commit -eq $baseCommit) -Message "$taskId grader used the wrong base."
        Assert-Phase5 -Condition ($grade.total_features -eq 2) -Message "$taskId grader did not exercise both features."
        Assert-Phase5 -Condition ($grade.passed_features -eq 0) -Message "$taskId untouched source unexpectedly passed feature grading."
        Assert-Phase5 -Condition ($grade.pass -eq $false) -Message "$taskId untouched source unexpectedly passed overall."
        Assert-Phase5 -Condition (@($grade.changed_paths) -contains $readme.Name) -Message "$taskId tracked replay sentinel was not captured."
        Assert-Phase5 -Condition (@($grade.changed_paths) -contains $untrackedName) -Message "$taskId untracked replay sentinel was not captured."

        foreach ($featureResult in @($grade.features)) {
            Assert-Phase5 -Condition ($null -ne $featureResult.returncode) -Message "$taskId feature $($featureResult.feature) never reached its official test command."
            Assert-Phase5 -Condition ($featureResult.failure_kind -eq "official_tests_failed") -Message "$taskId feature $($featureResult.feature) failed in infrastructure rather than its official test."
        }

        Write-Host "Candidate replay: PASS"
        Write-Host "Official tests reached: 2/2"
        Write-Host "Frozen untouched source rejected as expected: PASS"

        $grade | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath (Join-Path $runRoot "phase5-grade.json") -Encoding utf8

        $taskCheck = [ordered]@{
            schema = "oub-v2-phase5-task-check-v3"
            task_id = $taskId
            run_id = $ActiveRunId
            canonical_head = $head
            benchmark_fingerprint = [string]$audit.benchmark_fingerprint
            frozen_base = $baseCommit
            desktop_head = $desktopHead
            room_head = $roomHead
            desktop_tree = $desktopTree
            room_tree = $roomTree
            mission_sha256 = $desktopMissionHash
            windows_core_autocrlf = $winAutocrlf
            wsl_core_autocrlf = $wslAutocrlf
            windows_candidate_status = $windowsCandidateStatus
            wsl_candidate_status = $wslCandidateStatus
            hidden_tests_absent = $true
            mechanical_only = $true
            workers_started = $false
            room_status_before_abort = [string]$roomSnapshot.status
            round_status_before_abort = [string]$roomSnapshot.active_round.status
            grade = $grade
        }

        $taskCheck | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath (Join-Path $runRoot "phase5-check.json") -Encoding utf8

        Write-Host ""
        Write-Host "--- Abort / cleanup / serialization ---"

        $abort = Invoke-OubV2Json -Arguments @("abort", "--run-id", $ActiveRunId)
        Assert-Phase5 -Condition ($abort.aborted -eq $true) -Message "$taskId abort failed."

        $roomAfterAbort = Invoke-RestMethod -Method Get -Uri "$RoomBase/api/rooms/$roomId" -TimeoutSec 10
        Assert-Phase5 -Condition ($TerminalRoomStatuses -contains [string]$roomAfterAbort.status) -Message "$taskId Room remained active after abort."

        $statusAfterAbort = Invoke-OubV2Json -Arguments @("status", "--run-id", $ActiveRunId)
        Assert-Phase5 -Condition ($statusAfterAbort.active -eq $false) -Message "$taskId remained active after abort."
        Assert-Phase5 -Condition ($statusAfterAbort.aborted -eq $true) -Message "$taskId did not serialize aborted=true."

        $bundlePath = [string]$abort.bundle.bundle_path
        Assert-Phase5 -Condition (Test-Path -LiteralPath $bundlePath) -Message "$taskId evidence bundle is missing."

        $zip = [IO.Compression.ZipFile]::OpenRead($bundlePath)
        try {
            $entries = @($zip.Entries | ForEach-Object { $_.FullName })
        }
        finally {
            $zip.Dispose()
        }

        Assert-Phase5 -Condition ($entries -contains "state.json") -Message "$taskId bundle lacks state.json."
        Assert-Phase5 -Condition ($entries -contains "phase5-grade.json") -Message "$taskId bundle lacks phase5-grade.json."
        Assert-Phase5 -Condition ($entries -contains "phase5-check.json") -Message "$taskId bundle lacks phase5-check.json."
        Assert-Phase5 -Condition (@($entries | Where-Object { $_ -like "desktop-workspace/*" }).Count -eq 0) -Message "$taskId bundle copied the external repository."

        Write-Host "Abort: PASS"
        Write-Host "Room cleanup: $($roomAfterAbort.status)"
        Write-Host "Serialization: PASS"
        Write-Host "Bundle: PASS"
        Write-Host $bundlePath

        $TaskResults += [pscustomobject]@{
            task_id = $taskId
            run_id = $ActiveRunId
            frozen_base = $baseCommit
            room_after_abort = [string]$roomAfterAbort.status
            bundle = $bundlePath
            result = "PASS"
        }

        $ActiveRunId = $null
    }

    Write-Host ""
    Write-Host "=== FINAL TASK-SET CHECKS ==="

    $finalAudit = Invoke-OubV2Json -Arguments @("audit")
    $finalStatus = Invoke-OubV2Json -Arguments @("status")
    $currentPointer = (Get-Content -LiteralPath (Join-Path $RepoRoot "benchmarks\oub\CURRENT") -Raw).Trim()

    Assert-Phase5 -Condition ($finalAudit.ok -eq $true) -Message "Final OUB v2 audit failed."
    Assert-Phase5 -Condition ($finalStatus.active -eq $false) -Message "An OUB v2 run remains active."
    Assert-Phase5 -Condition ($currentPointer -eq "v1") -Message "OUB CURRENT changed during Phase 5."
    Assert-Phase5 -Condition ($TaskResults.Count -eq $TaskIds.Count) -Message "Not all requested tasks passed."

    $allFrozenTasksCovered = @($TaskIds | Sort-Object -Unique).Count -eq 3

    $summary = [ordered]@{
        schema = "oub-v2-phase5-taskset-summary-v1"
        phase = 5
        canonical_head = $head
        benchmark_fingerprint = [string]$finalAudit.benchmark_fingerprint
        current_pointer = $currentPointer
        paid_benchmark_cognition_started = $false
        requested_tasks = $TaskIds
        task_count = $TaskResults.Count
        all_frozen_tasks_covered_by_this_run = $allFrozenTasksCovered
        tasks = $TaskResults
        result = "PASS"
    }

    $stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
    $summaryPath = Join-Path $RepoRoot "output\oub\oub-v2-phase5-taskset-$stamp.json"
    $summary | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $summaryPath -Encoding utf8

    Write-Host ""
    Write-Host "============================================================"
    Write-Host "I-028 PHASE 5 REQUESTED TASK SET: PASS"
    Write-Host "============================================================"
    Write-Host "Canonical HEAD: $head"
    Write-Host "Fingerprint: $($finalAudit.benchmark_fingerprint)"
    Write-Host "OUB CURRENT: $currentPointer"
    Write-Host "Paid benchmark cognition: NONE"
    Write-Host "Active OUB runs: NONE"
    Write-Host "Summary: $summaryPath"
    Write-Host ""

    $TaskResults |
        Select-Object task_id, run_id, result, room_after_abort, bundle |
        Format-Table -AutoSize
}
catch {
    Write-Host ""
    Write-Host "============================================================"
    Write-Host "I-028 PHASE 5 REQUESTED TASK SET: FAIL"
    Write-Host "============================================================"
    Write-Host $_.Exception.Message

    if (-not [string]::IsNullOrWhiteSpace($ActiveRunId)) {
        Write-Host ""
        Write-Host "Attempting fail-safe abort of $ActiveRunId ..."

        try {
            [void](Invoke-OubV2Json -Arguments @("abort", "--run-id", $ActiveRunId))
            Write-Host "Fail-safe abort: completed"
        }
        catch {
            Write-Host "WARNING: fail-safe abort failed: $($_.Exception.Message)"
        }
    }

    throw
}
finally {
    Pop-Location
}
