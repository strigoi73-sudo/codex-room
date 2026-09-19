# Codex Room — Repeatable Functional Acceptance Test Plan

**Initialized:** 2026-09-18  
**Purpose:** Repeatable functional and operational acceptance testing of Codex Room Personal.  
**Reference baseline when initialized:** canonical `main` at `800beeaa9c102c325e0c645a3416ec427f862500`.  
**Proposed repository location:** `docs/CODEX_ROOM_FUNCTIONAL_ACCEPTANCE_TEST_PLAN.md`.  
**Authority:** Operational test specification. This file is not a canonical Project-source owner and does not replace `docs/project/06_DEVELOPMENT_CONTROL.md`, the Decision Register, Architecture & Current State, or the Evidence Register.

## 1. What this test plan is

This plan freezes a series of functional tests so that the campaign can survive chat changes, context loss, and long pauses. Each test has a stable identifier, a fixed purpose, a complete PowerShell procedure, explicit evidence capture, and pass/inconclusive/fail criteria.

The procedures are **repeatable as test protocols**. Deterministic tests should reproduce the same mechanical result on the same bytes and environment. Live model tests are controlled naturalistic tests: the starting state, prompt, fixture, limits, and evidence collection are repeatable, while the model's exact prose and internal choices can vary. A live rerun should therefore be compared against behavioral invariants, not exact transcript bytes.

These tests are intended to exercise current production behavior. They are not a license to reopen already closed development work when the observed behavior is healthy.

## 2. Test rules

1. Run from the normal Windows workspace `C:\Codex Room`.
2. Use canonical `main`; every script records the exact current Git HEAD.
3. Start live tests with the normal Codex Room server unless the test explicitly stops/restarts it.
4. Each live test creates a fresh Room so prior provider context does not contaminate the result.
5. Production API defaults remain work-model v2 with `provider_context_mode="assignment_thread"`.
6. Evidence is written beneath ignored `output\functional-acceptance\<TEST>-<timestamp>\`.
7. Preserve the entire evidence directory for any FAIL or INCONCLUSIVE result.
8. Do not repair CORE while a test is still being characterized. Record the failure first.
9. A model making a different *valid* cognitive choice can make a behavioral test INCONCLUSIVE without proving a product defect.
10. Stop the campaign on a failure that threatens data integrity, identity/provenance, transaction correctness, or the validity of later tests. Lower-risk behavioral failures may be recorded and the campaign may continue.
11. Do not run deliberately expensive usage-wall or 40–59-turn refresh-threshold stress tests as part of this campaign. Those mechanisms already have stronger targeted evidence and would consume substantial allowance.
12. D-019 daily usage pacing is not tested because it remains decided but unimplemented.
13. Every PowerShell procedure is wrapped in a single invocation block (`& { ... }`) so a terminating error or `throw` stops the entire pasted procedure in an interactive PowerShell session.

## 3. Result vocabulary

- **PASS** — required invariants were observed with sufficient evidence.
- **FAIL** — an expected implemented invariant was contradicted.
- **INCONCLUSIVE** — the run did not exercise the intended branch, or evidence is insufficient.
- **NOT RUN** — no run has been performed under this plan.

A run result applies to the exact recorded repository HEAD and runtime state. Later code changes can make old results historical.

## 4. Campaign order

| Test | Name | Layer | Primary feature |
|---|---|---|---|
| T0 | Baseline health and fast verifier | Deterministic | Repository/runtime health |
| T1 | Fresh Room / C-first smoke | Live | Mandatory triad, C-first, selective cognition |
| T2 | Independent parallel delegation | Live | Differentiated A/B concurrency |
| T3 | Artifact dependency sequencing | Live | Produce → verify → integrate ordering |
| T4 | Direct-result return | Live | Nested delegation and coordinator return |
| T5 | Structured EVIDENCE retrieval | Live | Deterministic source evidence |
| T6 | Explicit worker-context continuation | Live | Assignment context lineage |
| T7 | Bounded HISTORY across rounds | Live | Historical result retrieval |
| T8 | Restart during active work | Live/operational | Recovery, exact execution, reconnect |
| T9 | Deliberate coordinator REFRESH | Live | BCTX-4 checkpoint handoff |
| T10 | Custom deterministic capability lifecycle | Live/tooling | Author → verify → register → invoke |
| T11 | Rollover continuity | Live/operational | Successor lineage and fresh contexts |
| T12 | Export and offline backup/verify | Operational | Complete export and durable maintenance |
| T13 | Explicit model-allocation exercise | Live | Per-assignment execution configuration |
| T14 | Integrated naturalistic mission | Live | End-to-end organization |

## 5. T0 — Baseline health and fast verifier

**Purpose.** Establish that the repository and runtime begin the campaign healthy and that the standard local verification gate passes on the exact tested bytes.

**PASS.** `/api/health` reports `ok=true`; `verify-fast.cmd` exits 0; tracked Git status is unchanged by the verifier.

**PowerShell:**

```powershell
& {
$ErrorActionPreference = 'Stop'

$Root = 'C:\Codex Room'
$Base = 'http://127.0.0.1:8765'
$TestId = 'T0'
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$EvidenceDir = Join-Path $Root ("output\functional-acceptance\{0}-{1}" -f $TestId, $Stamp)

Set-Location $Root
New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null

$head = (git rev-parse HEAD).Trim()
$statusBefore = @(git status --short)
$head | Set-Content -LiteralPath (Join-Path $EvidenceDir 'git-head.txt') -Encoding ASCII
$statusBefore | Set-Content -LiteralPath (Join-Path $EvidenceDir 'git-status-before.txt') -Encoding UTF8

$health = Invoke-RestMethod -Method Get -Uri "$Base/api/health"
$health | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath (Join-Path $EvidenceDir 'health.json') -Encoding UTF8
if (-not $health.ok) {
    throw 'T0 failed: /api/health did not report ok=true.'
}

cmd.exe /d /c verify-fast.cmd 2>&1 | Tee-Object -FilePath (Join-Path $EvidenceDir 'verify-fast.txt')
$verifyExit = $LASTEXITCODE
if ($verifyExit -ne 0) {
    throw "T0 failed: verify-fast.cmd exited $verifyExit."
}

$statusAfter = @(git status --short)
$statusAfter | Set-Content -LiteralPath (Join-Path $EvidenceDir 'git-status-after.txt') -Encoding UTF8

if (($statusBefore -join "`n") -ne ($statusAfter -join "`n")) {
    throw 'T0 failed: tracked/untracked status changed during verification. Inspect the evidence.'
}

Write-Host ""
Write-Host "T0 PASS candidate."
Write-Host "HEAD: $head"
Write-Host "Evidence: $EvidenceDir"
}
```

---

## 6. T1 — Fresh Room / C-first smoke

**Purpose.** Verify fresh production Room creation, mandatory A/B/C presence, C as the ordinary starter, and selective cognition on a task that does not justify peer work.

**Fixed prompt intent.** C should answer the tiny task itself and close the Task without purchasing A/B cognition.

**PASS.** The created Room contains exactly A/B/C; the active Round starts with C; the Room closes normally; A and B are not unnecessarily invoked. A structurally healthy Room that invokes a peer despite the prompt is **INCONCLUSIVE/behavioral concern**, not automatically a CORE failure.

**PowerShell:**

```powershell
& {
$ErrorActionPreference = 'Stop'

$Root = 'C:\Codex Room'
$Base = 'http://127.0.0.1:8765'
$TestId = 'T1'
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$EvidenceDir = Join-Path $Root ("output\functional-acceptance\{0}-{1}" -f $TestId, $Stamp)

Set-Location $Root
New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null

function Save-Json {
    param([Parameter(Mandatory=$true)]$Value, [Parameter(Mandatory=$true)][string]$Path)
    $Value | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Wait-Health {
    param([int]$TimeoutSeconds = 120)
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        try {
            $health = Invoke-RestMethod -Method Get -Uri "$Base/api/health"
            if ($health.ok) { return $health }
        }
        catch {
        }
        Start-Sleep -Seconds 1
    } while ((Get-Date) -lt $deadline)
    throw "Codex Room did not become healthy within $TimeoutSeconds seconds."
}

function Get-Room {
    param([Parameter(Mandatory=$true)][string]$RoomId)
    Invoke-RestMethod -Method Get -Uri "$Base/api/rooms/$RoomId"
}

function Wait-RoomTerminal {
    param(
        [Parameter(Mandatory=$true)][string]$RoomId,
        [int]$TimeoutSeconds = 1800
    )
    $terminal = @('finished', 'error', 'stopped', 'paused')
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        $room = Get-Room -RoomId $RoomId
        if ($terminal -contains [string]$room.status) { return $room }
        Start-Sleep -Seconds 1
    } while ((Get-Date) -lt $deadline)
    throw "Room $RoomId did not reach a terminal/paused state within $TimeoutSeconds seconds."
}

$head = (git rev-parse HEAD).Trim()
$statusBefore = @(git status --short)
$head | Set-Content -LiteralPath (Join-Path $EvidenceDir 'git-head.txt') -Encoding ASCII
$statusBefore | Set-Content -LiteralPath (Join-Path $EvidenceDir 'git-status-before.txt') -Encoding UTF8

$health = Wait-Health
Save-Json $health (Join-Path $EvidenceDir 'health-before.json')

$prompt = @'
This is Functional Acceptance Test T1.

Solve this tiny task yourself. Do not invoke A or B unless a peer is genuinely necessary.
Report the value of 7 * 8 and identify your coordination role in one short sentence, then COMPLETE the bounded Task.
'@

$body = @{
    title = 'T1 — Fresh Room C-first smoke'
    topic = $prompt
    auto_start = $false
    max_turns = 6
    max_consecutive_passes = 3
    inactivity_seconds = 900
    starting_agent = 'agent_c'
    completion_policy = 'auto_settle'
    required_contributors = @()
} | ConvertTo-Json -Depth 20

$created = Invoke-RestMethod -Method Post -Uri "$Base/api/rooms" -ContentType 'application/json' -Body $body
Save-Json $created (Join-Path $EvidenceDir 'room-created.json')

$roomId = [string]$created.id
$roundId = [string]$created.active_round_id
$workspace = Join-Path $Root ("data\rooms\{0}\shared" -f $roomId)
New-Item -ItemType Directory -Force -Path $workspace | Out-Null



Invoke-RestMethod -Method Post -Uri "$Base/api/rooms/$roomId/rounds/$roundId/start" | Out-Null

$final = Wait-RoomTerminal -RoomId $roomId
Save-Json $final (Join-Path $EvidenceDir 'room-final.json')

Invoke-WebRequest -UseBasicParsing -Method Get `
    -Uri "$Base/api/rooms/$roomId/export?format=json" `
    -OutFile (Join-Path $EvidenceDir 'room-export.json')



$statusAfter = @(git status --short)
$statusAfter | Set-Content -LiteralPath (Join-Path $EvidenceDir 'git-status-after.txt') -Encoding UTF8

$summary = [ordered]@{
    test_id = $TestId
    repository_head = $head
    room_id = $roomId
    round_id = $roundId
    room_status = [string]$final.status
    evidence_directory = $EvidenceDir
    tracked_status_before = $statusBefore
    tracked_status_after = $statusAfter
}
Save-Json $summary (Join-Path $EvidenceDir 'run-summary.json')

Write-Host ""
Write-Host "$TestId complete."
Write-Host "Room: $roomId"
Write-Host "Status: $($final.status)"
Write-Host "Evidence: $EvidenceDir"
}
```
## 7. T2 — Independent parallel delegation

**Purpose.** Exercise C's ability to recognize two genuinely independent assignments, differentiate them, and launch them together without unnecessary serialization.

**PASS.** C creates distinct A and B assignments for the two independent problems before either result is needed for the other; both results return through normal transaction state; C integrates once dependencies are satisfied; Room closes normally.

**PowerShell:**

```powershell
& {
$ErrorActionPreference = 'Stop'

$Root = 'C:\Codex Room'
$Base = 'http://127.0.0.1:8765'
$TestId = 'T2'
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$EvidenceDir = Join-Path $Root ("output\functional-acceptance\{0}-{1}" -f $TestId, $Stamp)

Set-Location $Root
New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null

function Save-Json {
    param([Parameter(Mandatory=$true)]$Value, [Parameter(Mandatory=$true)][string]$Path)
    $Value | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Wait-Health {
    param([int]$TimeoutSeconds = 120)
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        try {
            $health = Invoke-RestMethod -Method Get -Uri "$Base/api/health"
            if ($health.ok) { return $health }
        }
        catch {
        }
        Start-Sleep -Seconds 1
    } while ((Get-Date) -lt $deadline)
    throw "Codex Room did not become healthy within $TimeoutSeconds seconds."
}

function Get-Room {
    param([Parameter(Mandatory=$true)][string]$RoomId)
    Invoke-RestMethod -Method Get -Uri "$Base/api/rooms/$RoomId"
}

function Wait-RoomTerminal {
    param(
        [Parameter(Mandatory=$true)][string]$RoomId,
        [int]$TimeoutSeconds = 1800
    )
    $terminal = @('finished', 'error', 'stopped', 'paused')
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        $room = Get-Room -RoomId $RoomId
        if ($terminal -contains [string]$room.status) { return $room }
        Start-Sleep -Seconds 1
    } while ((Get-Date) -lt $deadline)
    throw "Room $RoomId did not reach a terminal/paused state within $TimeoutSeconds seconds."
}

$head = (git rev-parse HEAD).Trim()
$statusBefore = @(git status --short)
$head | Set-Content -LiteralPath (Join-Path $EvidenceDir 'git-head.txt') -Encoding ASCII
$statusBefore | Set-Content -LiteralPath (Join-Path $EvidenceDir 'git-status-before.txt') -Encoding UTF8

$health = Wait-Health
Save-Json $health (Join-Path $EvidenceDir 'health-before.json')

$prompt = @'
This is Functional Acceptance Test T2.

Use both peers for two genuinely independent bounded assignments and issue the delegations together.

- A: compute the first 12 Fibonacci numbers beginning 0, 1 and report the sequence plus its sum.
- B: compute the first 10 prime numbers beginning 2 and report the sequence plus its sum.

Give A and B meaningfully differentiated instructions. Neither assignment depends on the other. Do not solve their work on C. When both results are available, integrate them into a compact final report and COMPLETE.
'@

$body = @{
    title = 'T2 — Independent parallel delegation'
    topic = $prompt
    auto_start = $false
    max_turns = 10
    max_consecutive_passes = 3
    inactivity_seconds = 900
    starting_agent = 'agent_c'
    completion_policy = 'auto_settle'
    required_contributors = @('agent_a','agent_b')
} | ConvertTo-Json -Depth 20

$created = Invoke-RestMethod -Method Post -Uri "$Base/api/rooms" -ContentType 'application/json' -Body $body
Save-Json $created (Join-Path $EvidenceDir 'room-created.json')

$roomId = [string]$created.id
$roundId = [string]$created.active_round_id
$workspace = Join-Path $Root ("data\rooms\{0}\shared" -f $roomId)
New-Item -ItemType Directory -Force -Path $workspace | Out-Null



Invoke-RestMethod -Method Post -Uri "$Base/api/rooms/$roomId/rounds/$roundId/start" | Out-Null

$final = Wait-RoomTerminal -RoomId $roomId
Save-Json $final (Join-Path $EvidenceDir 'room-final.json')

Invoke-WebRequest -UseBasicParsing -Method Get `
    -Uri "$Base/api/rooms/$roomId/export?format=json" `
    -OutFile (Join-Path $EvidenceDir 'room-export.json')



$statusAfter = @(git status --short)
$statusAfter | Set-Content -LiteralPath (Join-Path $EvidenceDir 'git-status-after.txt') -Encoding UTF8

$summary = [ordered]@{
    test_id = $TestId
    repository_head = $head
    room_id = $roomId
    round_id = $roundId
    room_status = [string]$final.status
    evidence_directory = $EvidenceDir
    tracked_status_before = $statusBefore
    tracked_status_after = $statusAfter
}
Save-Json $summary (Join-Path $EvidenceDir 'run-summary.json')

Write-Host ""
Write-Host "$TestId complete."
Write-Host "Room: $roomId"
Write-Host "Status: $($final.status)"
Write-Host "Evidence: $EvidenceDir"
}
```
## 8. T3 — Artifact dependency sequencing

**Purpose.** Exercise dependency-aware coordination: implementation must exist before artifact-dependent verification begins.

**Fixture/result.** A must create `t3_artifact.json` in the Room shared workspace. B must verify the resulting artifact only after A's implementation completes.

**PASS.** A creates the artifact first; B's artifact-dependent Assignment is created/run after the artifact exists; B verifies the exact artifact; C integrates; the file contains the requested JSON.

**PowerShell:**

```powershell
& {
$ErrorActionPreference = 'Stop'

$Root = 'C:\Codex Room'
$Base = 'http://127.0.0.1:8765'
$TestId = 'T3'
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$EvidenceDir = Join-Path $Root ("output\functional-acceptance\{0}-{1}" -f $TestId, $Stamp)

Set-Location $Root
New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null

function Save-Json {
    param([Parameter(Mandatory=$true)]$Value, [Parameter(Mandatory=$true)][string]$Path)
    $Value | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Wait-Health {
    param([int]$TimeoutSeconds = 120)
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        try {
            $health = Invoke-RestMethod -Method Get -Uri "$Base/api/health"
            if ($health.ok) { return $health }
        }
        catch {
        }
        Start-Sleep -Seconds 1
    } while ((Get-Date) -lt $deadline)
    throw "Codex Room did not become healthy within $TimeoutSeconds seconds."
}

function Get-Room {
    param([Parameter(Mandatory=$true)][string]$RoomId)
    Invoke-RestMethod -Method Get -Uri "$Base/api/rooms/$RoomId"
}

function Wait-RoomTerminal {
    param(
        [Parameter(Mandatory=$true)][string]$RoomId,
        [int]$TimeoutSeconds = 1800
    )
    $terminal = @('finished', 'error', 'stopped', 'paused')
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        $room = Get-Room -RoomId $RoomId
        if ($terminal -contains [string]$room.status) { return $room }
        Start-Sleep -Seconds 1
    } while ((Get-Date) -lt $deadline)
    throw "Room $RoomId did not reach a terminal/paused state within $TimeoutSeconds seconds."
}

$head = (git rev-parse HEAD).Trim()
$statusBefore = @(git status --short)
$head | Set-Content -LiteralPath (Join-Path $EvidenceDir 'git-head.txt') -Encoding ASCII
$statusBefore | Set-Content -LiteralPath (Join-Path $EvidenceDir 'git-status-before.txt') -Encoding UTF8

$health = Wait-Health
Save-Json $health (Join-Path $EvidenceDir 'health-before.json')

$prompt = @'
This is Functional Acceptance Test T3.

Coordinate the following dependent work.

1. Delegate A to create a UTF-8 JSON file named `t3_artifact.json` in the Room shared workspace. It must contain exactly these data values:
   - `canary`: `T3-DEPENDENCY-CANARY`
   - `value`: 1729
   - `status`: `ready`
   A should validate that the file is valid JSON before completing.

2. Only after A has completed and the artifact exists, delegate B to independently inspect the actual `t3_artifact.json` bytes/content and verify all three required values. B must not perform artifact-dependent verification before the artifact exists.

3. Integrate B's verification and COMPLETE. Do not rewrite the artifact on C.
'@

$body = @{
    title = 'T3 — Artifact dependency sequencing'
    topic = $prompt
    auto_start = $false
    max_turns = 12
    max_consecutive_passes = 3
    inactivity_seconds = 900
    starting_agent = 'agent_c'
    completion_policy = 'auto_settle'
    required_contributors = @('agent_a','agent_b')
} | ConvertTo-Json -Depth 20

$created = Invoke-RestMethod -Method Post -Uri "$Base/api/rooms" -ContentType 'application/json' -Body $body
Save-Json $created (Join-Path $EvidenceDir 'room-created.json')

$roomId = [string]$created.id
$roundId = [string]$created.active_round_id
$workspace = Join-Path $Root ("data\rooms\{0}\shared" -f $roomId)
New-Item -ItemType Directory -Force -Path $workspace | Out-Null



Invoke-RestMethod -Method Post -Uri "$Base/api/rooms/$roomId/rounds/$roundId/start" | Out-Null

$final = Wait-RoomTerminal -RoomId $roomId
Save-Json $final (Join-Path $EvidenceDir 'room-final.json')

Invoke-WebRequest -UseBasicParsing -Method Get `
    -Uri "$Base/api/rooms/$roomId/export?format=json" `
    -OutFile (Join-Path $EvidenceDir 'room-export.json')

$artifact = Join-Path $workspace 't3_artifact.json'
if (Test-Path -LiteralPath $artifact) {
Copy-Item -LiteralPath $artifact -Destination (Join-Path $EvidenceDir 't3_artifact.json')
Get-FileHash -Algorithm SHA256 -LiteralPath $artifact |
    Format-List * |
    Out-String |
    Set-Content -LiteralPath (Join-Path $EvidenceDir 't3_artifact.sha256.txt') -Encoding UTF8
}
else {
'Artifact missing' | Set-Content -LiteralPath (Join-Path $EvidenceDir 't3_artifact-missing.txt') -Encoding UTF8
}

$statusAfter = @(git status --short)
$statusAfter | Set-Content -LiteralPath (Join-Path $EvidenceDir 'git-status-after.txt') -Encoding UTF8

$summary = [ordered]@{
    test_id = $TestId
    repository_head = $head
    room_id = $roomId
    round_id = $roundId
    room_status = [string]$final.status
    evidence_directory = $EvidenceDir
    tracked_status_before = $statusBefore
    tracked_status_after = $statusAfter
}
Save-Json $summary (Join-Path $EvidenceDir 'run-summary.json')

Write-Host ""
Write-Host "$TestId complete."
Write-Host "Room: $roomId"
Write-Host "Status: $($final.status)"
Write-Host "Evidence: $EvidenceDir"
}
```
## 9. T4 — Direct-result return

**Purpose.** Exercise nested delegation and the BCTX-2 direct-result return path, where an intermediate parent has no material work left after its child finishes.

**PASS.** C delegates to A; A delegates the substantive final computation to B using coordinator return; B's finished result returns directly to C; A is mechanically waived/resolved as relay-only; C integrates; no unnecessary A relay turn is purchased.

**PowerShell:**

```powershell
& {
$ErrorActionPreference = 'Stop'

$Root = 'C:\Codex Room'
$Base = 'http://127.0.0.1:8765'
$TestId = 'T4'
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$EvidenceDir = Join-Path $Root ("output\functional-acceptance\{0}-{1}" -f $TestId, $Stamp)

Set-Location $Root
New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null

function Save-Json {
    param([Parameter(Mandatory=$true)]$Value, [Parameter(Mandatory=$true)][string]$Path)
    $Value | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Wait-Health {
    param([int]$TimeoutSeconds = 120)
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        try {
            $health = Invoke-RestMethod -Method Get -Uri "$Base/api/health"
            if ($health.ok) { return $health }
        }
        catch {
        }
        Start-Sleep -Seconds 1
    } while ((Get-Date) -lt $deadline)
    throw "Codex Room did not become healthy within $TimeoutSeconds seconds."
}

function Get-Room {
    param([Parameter(Mandatory=$true)][string]$RoomId)
    Invoke-RestMethod -Method Get -Uri "$Base/api/rooms/$RoomId"
}

function Wait-RoomTerminal {
    param(
        [Parameter(Mandatory=$true)][string]$RoomId,
        [int]$TimeoutSeconds = 1800
    )
    $terminal = @('finished', 'error', 'stopped', 'paused')
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        $room = Get-Room -RoomId $RoomId
        if ($terminal -contains [string]$room.status) { return $room }
        Start-Sleep -Seconds 1
    } while ((Get-Date) -lt $deadline)
    throw "Room $RoomId did not reach a terminal/paused state within $TimeoutSeconds seconds."
}

$head = (git rev-parse HEAD).Trim()
$statusBefore = @(git status --short)
$head | Set-Content -LiteralPath (Join-Path $EvidenceDir 'git-head.txt') -Encoding ASCII
$statusBefore | Set-Content -LiteralPath (Join-Path $EvidenceDir 'git-status-before.txt') -Encoding UTF8

$health = Wait-Health
Save-Json $health (Join-Path $EvidenceDir 'health-before.json')

$prompt = @'
This is Functional Acceptance Test T4.

Exercise the direct-result-return mechanism.

C should delegate one bounded assignment to A. A's assignment is to delegate the actual final computation to B and request coordinator return because A will have no material intellectual work after B finishes.

B's task: compute `137 * 211`, show a short arithmetic check, and return the final integer as the finished required result.

A must not relay or re-summarize B after B completes. C should receive B's completed result through the direct coordinator-return path, report it, and COMPLETE.
'@

$body = @{
    title = 'T4 — Direct-result return'
    topic = $prompt
    auto_start = $false
    max_turns = 10
    max_consecutive_passes = 3
    inactivity_seconds = 900
    starting_agent = 'agent_c'
    completion_policy = 'auto_settle'
    required_contributors = @('agent_a','agent_b')
} | ConvertTo-Json -Depth 20

$created = Invoke-RestMethod -Method Post -Uri "$Base/api/rooms" -ContentType 'application/json' -Body $body
Save-Json $created (Join-Path $EvidenceDir 'room-created.json')

$roomId = [string]$created.id
$roundId = [string]$created.active_round_id
$workspace = Join-Path $Root ("data\rooms\{0}\shared" -f $roomId)
New-Item -ItemType Directory -Force -Path $workspace | Out-Null



Invoke-RestMethod -Method Post -Uri "$Base/api/rooms/$roomId/rounds/$roundId/start" | Out-Null

$final = Wait-RoomTerminal -RoomId $roomId
Save-Json $final (Join-Path $EvidenceDir 'room-final.json')

Invoke-WebRequest -UseBasicParsing -Method Get `
    -Uri "$Base/api/rooms/$roomId/export?format=json" `
    -OutFile (Join-Path $EvidenceDir 'room-export.json')



$statusAfter = @(git status --short)
$statusAfter | Set-Content -LiteralPath (Join-Path $EvidenceDir 'git-status-after.txt') -Encoding UTF8

$summary = [ordered]@{
    test_id = $TestId
    repository_head = $head
    room_id = $roomId
    round_id = $roundId
    room_status = [string]$final.status
    evidence_directory = $EvidenceDir
    tracked_status_before = $statusBefore
    tracked_status_after = $statusAfter
}
Save-Json $summary (Join-Path $EvidenceDir 'run-summary.json')

Write-Host ""
Write-Host "$TestId complete."
Write-Host "Room: $roomId"
Write-Host "Status: $($final.status)"
Write-Host "Evidence: $EvidenceDir"
}
```
## 10. T5 — Structured EVIDENCE retrieval

**Purpose.** Verify that an agent can request bounded authorized CORE source evidence through transaction `EVIDENCE` instead of launching shell/CLI discovery loops.

**PASS.** C uses structured source evidence to inspect `codex_room/__main__.py`; the answer reports default host `127.0.0.1` and port `8765`; evidence provenance is present; no unnecessary peer delegation is needed.

**PowerShell:**

```powershell
& {
$ErrorActionPreference = 'Stop'

$Root = 'C:\Codex Room'
$Base = 'http://127.0.0.1:8765'
$TestId = 'T5'
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$EvidenceDir = Join-Path $Root ("output\functional-acceptance\{0}-{1}" -f $TestId, $Stamp)

Set-Location $Root
New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null

function Save-Json {
    param([Parameter(Mandatory=$true)]$Value, [Parameter(Mandatory=$true)][string]$Path)
    $Value | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Wait-Health {
    param([int]$TimeoutSeconds = 120)
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        try {
            $health = Invoke-RestMethod -Method Get -Uri "$Base/api/health"
            if ($health.ok) { return $health }
        }
        catch {
        }
        Start-Sleep -Seconds 1
    } while ((Get-Date) -lt $deadline)
    throw "Codex Room did not become healthy within $TimeoutSeconds seconds."
}

function Get-Room {
    param([Parameter(Mandatory=$true)][string]$RoomId)
    Invoke-RestMethod -Method Get -Uri "$Base/api/rooms/$RoomId"
}

function Wait-RoomTerminal {
    param(
        [Parameter(Mandatory=$true)][string]$RoomId,
        [int]$TimeoutSeconds = 1800
    )
    $terminal = @('finished', 'error', 'stopped', 'paused')
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        $room = Get-Room -RoomId $RoomId
        if ($terminal -contains [string]$room.status) { return $room }
        Start-Sleep -Seconds 1
    } while ((Get-Date) -lt $deadline)
    throw "Room $RoomId did not reach a terminal/paused state within $TimeoutSeconds seconds."
}

$head = (git rev-parse HEAD).Trim()
$statusBefore = @(git status --short)
$head | Set-Content -LiteralPath (Join-Path $EvidenceDir 'git-head.txt') -Encoding ASCII
$statusBefore | Set-Content -LiteralPath (Join-Path $EvidenceDir 'git-status-before.txt') -Encoding UTF8

$health = Wait-Health
Save-Json $health (Join-Path $EvidenceDir 'health-before.json')

$prompt = @'
This is Functional Acceptance Test T5.

Using the transaction EVIDENCE mechanism, inspect authorized CORE source `codex_room/__main__.py` and determine the default server host and port.

Use bounded READ, SEARCH, or FIND evidence as appropriate. Do not use a shell command or direct CLI source-search loop for this task. Do not invoke A or B unless necessary.

Report the exact default host and port with a brief statement of the source file used, then COMPLETE.
'@

$body = @{
    title = 'T5 — Structured EVIDENCE retrieval'
    topic = $prompt
    auto_start = $false
    max_turns = 8
    max_consecutive_passes = 3
    inactivity_seconds = 900
    starting_agent = 'agent_c'
    completion_policy = 'auto_settle'
    required_contributors = @()
} | ConvertTo-Json -Depth 20

$created = Invoke-RestMethod -Method Post -Uri "$Base/api/rooms" -ContentType 'application/json' -Body $body
Save-Json $created (Join-Path $EvidenceDir 'room-created.json')

$roomId = [string]$created.id
$roundId = [string]$created.active_round_id
$workspace = Join-Path $Root ("data\rooms\{0}\shared" -f $roomId)
New-Item -ItemType Directory -Force -Path $workspace | Out-Null



Invoke-RestMethod -Method Post -Uri "$Base/api/rooms/$roomId/rounds/$roundId/start" | Out-Null

$final = Wait-RoomTerminal -RoomId $roomId
Save-Json $final (Join-Path $EvidenceDir 'room-final.json')

Invoke-WebRequest -UseBasicParsing -Method Get `
    -Uri "$Base/api/rooms/$roomId/export?format=json" `
    -OutFile (Join-Path $EvidenceDir 'room-export.json')



$statusAfter = @(git status --short)
$statusAfter | Set-Content -LiteralPath (Join-Path $EvidenceDir 'git-status-after.txt') -Encoding UTF8

$summary = [ordered]@{
    test_id = $TestId
    repository_head = $head
    room_id = $roomId
    round_id = $roundId
    room_status = [string]$final.status
    evidence_directory = $EvidenceDir
    tracked_status_before = $statusBefore
    tracked_status_after = $statusAfter
}
Save-Json $summary (Join-Path $EvidenceDir 'run-summary.json')

Write-Host ""
Write-Host "$TestId complete."
Write-Host "Room: $roomId"
Write-Host "Status: $($final.status)"
Write-Host "Evidence: $EvidenceDir"
}
```
## 11. T6 — Explicit worker-context continuation

**Purpose.** Exercise deliberate same-worker Assignment context continuity through explicit `context_from_assignment_id`, while preserving fresh context as the default for unrelated work.

**PASS.** C creates an initial A Assignment, later creates a causally continuous A follow-up that explicitly names the first A Assignment as its context source, and the export records the continuation lineage/context ownership. No implicit identity-only reuse is sufficient for PASS.

**PowerShell:**
```powershell
& {
$ErrorActionPreference = 'Stop'

$Root = 'C:\Codex Room'
$Base = 'http://127.0.0.1:8765'
$TestId = 'T6'
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$EvidenceDir = Join-Path $Root ("output\functional-acceptance\{0}-{1}" -f $TestId, $Stamp)

Set-Location $Root
New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null

function Save-Json {
    param([Parameter(Mandatory=$true)]$Value, [Parameter(Mandatory=$true)][string]$Path)
    $Value | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Wait-Health {
    param([int]$TimeoutSeconds = 120)
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        try {
            $health = Invoke-RestMethod -Method Get -Uri "$Base/api/health"
            if ($health.ok) { return $health }
        }
        catch {
        }
        Start-Sleep -Seconds 1
    } while ((Get-Date) -lt $deadline)
    throw "Codex Room did not become healthy within $TimeoutSeconds seconds."
}

function Get-Room {
    param([Parameter(Mandatory=$true)][string]$RoomId)
    Invoke-RestMethod -Method Get -Uri "$Base/api/rooms/$RoomId"
}

function Wait-RoomTerminal {
    param(
        [Parameter(Mandatory=$true)][string]$RoomId,
        [int]$TimeoutSeconds = 1800
    )
    $terminal = @('finished', 'error', 'stopped', 'paused')
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        $room = Get-Room -RoomId $RoomId
        if ($terminal -contains [string]$room.status) { return $room }
        Start-Sleep -Seconds 1
    } while ((Get-Date) -lt $deadline)
    throw "Room $RoomId did not reach a terminal/paused state within $TimeoutSeconds seconds."
}

$head = (git rev-parse HEAD).Trim()
$statusBefore = @(git status --short)
$head | Set-Content -LiteralPath (Join-Path $EvidenceDir 'git-head.txt') -Encoding ASCII
$statusBefore | Set-Content -LiteralPath (Join-Path $EvidenceDir 'git-status-before.txt') -Encoding UTF8

$health = Wait-Health
Save-Json $health (Join-Path $EvidenceDir 'health-before.json')

$prompt = @'
This is Functional Acceptance Test T6.

Exercise explicit same-worker Assignment context continuation.

First, delegate A a bounded assignment to inspect the conceptual fields of `DelegationRequest` in the current CORE source and report the two fields that control execution configuration and context continuation.

After A completes, create a second, causally continuous A assignment. Explicitly set `context_from_assignment_id` to the first A assignment. Ask A to explain, using its prior work, why those two fields serve different purposes.

Do not delegate B. C should integrate the second A result and COMPLETE. The important test condition is explicit recorded context lineage between the two A assignments.
'@

$body = @{
    title = 'T6 — Explicit worker-context continuation'
    topic = $prompt
    auto_start = $false
    max_turns = 10
    max_consecutive_passes = 3
    inactivity_seconds = 900
    starting_agent = 'agent_c'
    completion_policy = 'auto_settle'
    required_contributors = @('agent_a')
} | ConvertTo-Json -Depth 20

$created = Invoke-RestMethod -Method Post -Uri "$Base/api/rooms" -ContentType 'application/json' -Body $body
Save-Json $created (Join-Path $EvidenceDir 'room-created.json')

$roomId = [string]$created.id
$roundId = [string]$created.active_round_id
$workspace = Join-Path $Root ("data\rooms\{0}\shared" -f $roomId)
New-Item -ItemType Directory -Force -Path $workspace | Out-Null



Invoke-RestMethod -Method Post -Uri "$Base/api/rooms/$roomId/rounds/$roundId/start" | Out-Null

$final = Wait-RoomTerminal -RoomId $roomId
Save-Json $final (Join-Path $EvidenceDir 'room-final.json')

Invoke-WebRequest -UseBasicParsing -Method Get `
    -Uri "$Base/api/rooms/$roomId/export?format=json" `
    -OutFile (Join-Path $EvidenceDir 'room-export.json')



$statusAfter = @(git status --short)
$statusAfter | Set-Content -LiteralPath (Join-Path $EvidenceDir 'git-status-after.txt') -Encoding UTF8

$summary = [ordered]@{
    test_id = $TestId
    repository_head = $head
    room_id = $roomId
    round_id = $roundId
    room_status = [string]$final.status
    evidence_directory = $EvidenceDir
    tracked_status_before = $statusBefore
    tracked_status_after = $statusAfter
}
Save-Json $summary (Join-Path $EvidenceDir 'run-summary.json')

Write-Host ""
Write-Host "$TestId complete."
Write-Host "Room: $roomId"
Write-Host "Status: $($final.status)"
Write-Host "Evidence: $EvidenceDir"
}
```
## 12. T7 — Bounded HISTORY across rounds

**Purpose.** Verify that a fresh Assignment can retrieve a prior completed result through bounded Room `HISTORY` without restoring wholesale provider transcript inheritance.

**PASS.** Round 1 completes with the hidden codeword result. Round 2 uses transaction `HISTORY` with query `Archive codeword`, retrieves the prior completed result, reports `saffron-echo-581`, records selected event provenance, and closes normally.

**PowerShell:**

```powershell
& {
$ErrorActionPreference = 'Stop'

$Root = 'C:\Codex Room'
$Base = 'http://127.0.0.1:8765'
$TestId = 'T7'
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$EvidenceDir = Join-Path $Root ("output\functional-acceptance\{0}-{1}" -f $TestId, $Stamp)

Set-Location $Root
New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null

function Save-Json {
    param([Parameter(Mandatory=$true)]$Value, [Parameter(Mandatory=$true)][string]$Path)
    $Value | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Get-Room {
    param([Parameter(Mandatory=$true)][string]$RoomId)
    Invoke-RestMethod -Method Get -Uri "$Base/api/rooms/$RoomId"
}

function Wait-RoundTerminal {
    param([Parameter(Mandatory=$true)][string]$RoomId, [int]$TimeoutSeconds = 1200)
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        $room = Get-Room -RoomId $RoomId
        if (@('finished','error','stopped','paused') -contains [string]$room.status) {
            return $room
        }
        Start-Sleep -Seconds 1
    } while ((Get-Date) -lt $deadline)
    throw "Room $RoomId did not settle."
}

$head = (git rev-parse HEAD).Trim()
$head | Set-Content -LiteralPath (Join-Path $EvidenceDir 'git-head.txt') -Encoding ASCII
$health = Invoke-RestMethod -Method Get -Uri "$Base/api/health"
Save-Json $health (Join-Path $EvidenceDir 'health-before.json')

$round1Prompt = @'
This is Functional Acceptance Test T7, Round 1.

Complete this bounded Task with exactly this durable result sentence:
Archive codeword: saffron-echo-581

Do not invoke peers. Then COMPLETE.
'@

$createBody = @{
    title = 'T7 — Bounded HISTORY across rounds'
    topic = $round1Prompt
    auto_start = $false
    max_turns = 6
    max_consecutive_passes = 3
    inactivity_seconds = 900
    starting_agent = 'agent_c'
    completion_policy = 'auto_settle'
    required_contributors = @()
} | ConvertTo-Json -Depth 20

$created = Invoke-RestMethod -Method Post -Uri "$Base/api/rooms" -ContentType 'application/json' -Body $createBody
Save-Json $created (Join-Path $EvidenceDir 'round1-created.json')
$roomId = [string]$created.id
$round1 = [string]$created.active_round_id

Invoke-RestMethod -Method Post -Uri "$Base/api/rooms/$roomId/rounds/$round1/start" | Out-Null
$afterRound1 = Wait-RoundTerminal -RoomId $roomId
Save-Json $afterRound1 (Join-Path $EvidenceDir 'round1-final.json')

if ([string]$afterRound1.status -ne 'finished') {
    throw "T7 Round 1 did not finish normally: $($afterRound1.status)"
}

$round2Prompt = @'
This is Functional Acceptance Test T7, Round 2.

Do not infer or invent the earlier codeword. Use the transaction HISTORY mechanism with a SEARCH for the phrase `Archive codeword` over prior completed Room results. Retrieve the relevant earlier result, report the exact codeword that follows `Archive codeword:`, identify that HISTORY supplied it, then COMPLETE.

Do not invoke A or B.
'@

$round2Body = @{
    title = 'T7 — HISTORY retrieval'
    prompt = $round2Prompt
    starting_agent = 'agent_c'
    work_model_version = 2
    provider_context_mode = 'assignment_thread'
    completion_policy = 'auto_settle'
    required_contributors = @()
} | ConvertTo-Json -Depth 20

$prepared = Invoke-RestMethod -Method Post -Uri "$Base/api/rooms/$roomId/rounds" -ContentType 'application/json' -Body $round2Body
Save-Json $prepared (Join-Path $EvidenceDir 'round2-prepared.json')
$round2 = [string]$prepared.active_round_id

Invoke-RestMethod -Method Post -Uri "$Base/api/rooms/$roomId/rounds/$round2/start" | Out-Null
$afterRound2 = Wait-RoundTerminal -RoomId $roomId
Save-Json $afterRound2 (Join-Path $EvidenceDir 'round2-final.json')

Invoke-WebRequest -UseBasicParsing -Method Get `
    -Uri "$Base/api/rooms/$roomId/export?format=json" `
    -OutFile (Join-Path $EvidenceDir 'room-export.json')

Write-Host ""
Write-Host "T7 complete."
Write-Host "Room: $roomId"
Write-Host "Round 1: $round1"
Write-Host "Round 2: $round2"
Write-Host "Final status: $($afterRound2.status)"
Write-Host "Evidence: $EvidenceDir"
}
```

---

## 13. T8 — Restart during active work

**Purpose.** Exercise durable transaction state, exact execution reconciliation, restart recovery, serialized work, and the server-only restart path while a Room is active.

**PASS.** The server restarts cleanly; the same Room/transaction survives; work resumes without duplicate completed Assignments or split-brain execution; the Room eventually finishes normally or reaches a clearly recoverable paused state. Any terminal `error` caused by restart is FAIL.

**PowerShell:**

```powershell
& {
$ErrorActionPreference = 'Stop'

$Root = 'C:\Codex Room'
$Base = 'http://127.0.0.1:8765'
$TestId = 'T8'
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$EvidenceDir = Join-Path $Root ("output\functional-acceptance\{0}-{1}" -f $TestId, $Stamp)

Set-Location $Root
New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null

function Save-Json {
    param([Parameter(Mandatory=$true)]$Value, [Parameter(Mandatory=$true)][string]$Path)
    $Value | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $Path -Encoding UTF8
}
function Get-Room {
    param([Parameter(Mandatory=$true)][string]$RoomId)
    Invoke-RestMethod -Method Get -Uri "$Base/api/rooms/$RoomId"
}
function Wait-Health {
    param([int]$TimeoutSeconds = 180)
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        try {
            $h = Invoke-RestMethod -Method Get -Uri "$Base/api/health"
            if ($h.ok) { return $h }
        } catch {
        }
        Start-Sleep -Seconds 1
    } while ((Get-Date) -lt $deadline)
    throw 'Codex Room did not become healthy after restart.'
}
function Wait-Terminal {
    param([string]$RoomId, [int]$TimeoutSeconds = 1800)
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        $r = Get-Room $RoomId
        if (@('finished','error','stopped','paused') -contains [string]$r.status) { return $r }
        Start-Sleep -Seconds 1
    } while ((Get-Date) -lt $deadline)
    throw "Room $RoomId did not settle."
}

$head = (git rev-parse HEAD).Trim()
$head | Set-Content -LiteralPath (Join-Path $EvidenceDir 'git-head.txt') -Encoding ASCII
Wait-Health | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath (Join-Path $EvidenceDir 'health-before.json') -Encoding UTF8

$prompt = @'
This is Functional Acceptance Test T8.

Use both A and B for independent bounded analysis before integrating:
- A: list five invariants a restart-safe task system should preserve.
- B: list five failure modes a restart-safe task system should guard against.

Issue both delegations together. After both return, integrate them into one compact checklist and COMPLETE.
'@

$body = @{
    title = 'T8 — Restart during active work'
    topic = $prompt
    auto_start = $false
    max_turns = 12
    max_consecutive_passes = 3
    inactivity_seconds = 900
    starting_agent = 'agent_c'
    completion_policy = 'auto_settle'
    required_contributors = @('agent_a','agent_b')
} | ConvertTo-Json -Depth 20

$created = Invoke-RestMethod -Method Post -Uri "$Base/api/rooms" -ContentType 'application/json' -Body $body
Save-Json $created (Join-Path $EvidenceDir 'room-created.json')
$roomId = [string]$created.id
$roundId = [string]$created.active_round_id

Invoke-RestMethod -Method Post -Uri "$Base/api/rooms/$roomId/rounds/$roundId/start" | Out-Null

$deadline = (Get-Date).AddSeconds(120)
$busy = $false
do {
    $beforeRestart = Get-Room $roomId
    $busyAgents = @(
        $beforeRestart.agents | Where-Object {
            $_.execution.processing_count -gt 0 -or
            $_.execution.pending_count -gt 0 -or
            @('claimed','active','recovering','result_ready') -contains [string]$_.execution.durable_execution_state
        }
    )
    if ($busyAgents.Count -gt 0) {
        $busy = $true
        break
    }
    if (@('finished','error','stopped','paused') -contains [string]$beforeRestart.status) {
        break
    }
    Start-Sleep -Milliseconds 250
} while ((Get-Date) -lt $deadline)

Save-Json $beforeRestart (Join-Path $EvidenceDir 'room-before-restart.json')

if (-not $busy) {
    throw 'T8 INCONCLUSIVE: the Room settled before an active/pending execution could be interrupted.'
}

& (Join-Path $Root 'Restart-Codex-Room.bat')
if ($LASTEXITCODE -ne 0) {
    throw "T8 failed: Restart-Codex-Room.bat exited $LASTEXITCODE."
}

$healthAfter = Wait-Health
Save-Json $healthAfter (Join-Path $EvidenceDir 'health-after-restart.json')

$afterRestart = Get-Room $roomId
Save-Json $afterRestart (Join-Path $EvidenceDir 'room-after-restart.json')

if ([string]$afterRestart.status -eq 'paused') {
    Invoke-RestMethod -Method Post -Uri "$Base/api/rooms/$roomId/resume" | Out-Null
}

$final = Wait-Terminal -RoomId $roomId
Save-Json $final (Join-Path $EvidenceDir 'room-final.json')

Invoke-WebRequest -UseBasicParsing -Method Get `
    -Uri "$Base/api/rooms/$roomId/export?format=json" `
    -OutFile (Join-Path $EvidenceDir 'room-export.json')

if ([string]$final.status -eq 'error') {
    throw 'T8 FAIL candidate: Room entered error after restart. Preserve the evidence directory.'
}

Write-Host ""
Write-Host "T8 complete."
Write-Host "Room: $roomId"
Write-Host "Final status: $($final.status)"
Write-Host "Evidence: $EvidenceDir"
}
```

---

## 14. T9 — Deliberate coordinator REFRESH

**Purpose.** Exercise BCTX-4's explicit C-only checkpoint refresh at a clean bounded point without forcing the expensive 64K/96K threshold benchmark.

**PASS.** C performs one peer assignment, deliberately emits one `REFRESH` with a useful checkpoint, CORE changes to a distinct coordinator provider context, the refreshed C turn receives reconstructed transaction state plus checkpoint, and the Task completes normally.

**PowerShell:**

```powershell
& {
$ErrorActionPreference = 'Stop'

$Root = 'C:\Codex Room'
$Base = 'http://127.0.0.1:8765'
$TestId = 'T9'
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$EvidenceDir = Join-Path $Root ("output\functional-acceptance\{0}-{1}" -f $TestId, $Stamp)

Set-Location $Root
New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null

function Save-Json {
    param([Parameter(Mandatory=$true)]$Value, [Parameter(Mandatory=$true)][string]$Path)
    $Value | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Wait-Health {
    param([int]$TimeoutSeconds = 120)
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        try {
            $health = Invoke-RestMethod -Method Get -Uri "$Base/api/health"
            if ($health.ok) { return $health }
        }
        catch {
        }
        Start-Sleep -Seconds 1
    } while ((Get-Date) -lt $deadline)
    throw "Codex Room did not become healthy within $TimeoutSeconds seconds."
}

function Get-Room {
    param([Parameter(Mandatory=$true)][string]$RoomId)
    Invoke-RestMethod -Method Get -Uri "$Base/api/rooms/$RoomId"
}

function Wait-RoomTerminal {
    param(
        [Parameter(Mandatory=$true)][string]$RoomId,
        [int]$TimeoutSeconds = 1800
    )
    $terminal = @('finished', 'error', 'stopped', 'paused')
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        $room = Get-Room -RoomId $RoomId
        if ($terminal -contains [string]$room.status) { return $room }
        Start-Sleep -Seconds 1
    } while ((Get-Date) -lt $deadline)
    throw "Room $RoomId did not reach a terminal/paused state within $TimeoutSeconds seconds."
}

$head = (git rev-parse HEAD).Trim()
$statusBefore = @(git status --short)
$head | Set-Content -LiteralPath (Join-Path $EvidenceDir 'git-head.txt') -Encoding ASCII
$statusBefore | Set-Content -LiteralPath (Join-Path $EvidenceDir 'git-status-before.txt') -Encoding UTF8

$health = Wait-Health
Save-Json $health (Join-Path $EvidenceDir 'health-before.json')

$prompt = @'
This is Functional Acceptance Test T9.

Exercise the explicit coordinator REFRESH mechanism once.

1. Delegate A one bounded assignment: compute the SHA-256 hexadecimal digest of the UTF-8 text `Codex Room T9 refresh canary` and report it.
2. After A completes and at the next clean coordinator boundary, before giving the final answer, deliberately issue exactly one REFRESH action. The checkpoint must include A's reported digest, the fact that A is complete, and the remaining step: report the digest to the human and complete.
3. After the fresh coordinator context resumes, report A's digest and COMPLETE.

Do not invoke B. Do not issue more than one REFRESH.
'@

$body = @{
    title = 'T9 — Deliberate coordinator REFRESH'
    topic = $prompt
    auto_start = $false
    max_turns = 10
    max_consecutive_passes = 3
    inactivity_seconds = 900
    starting_agent = 'agent_c'
    completion_policy = 'auto_settle'
    required_contributors = @('agent_a')
} | ConvertTo-Json -Depth 20

$created = Invoke-RestMethod -Method Post -Uri "$Base/api/rooms" -ContentType 'application/json' -Body $body
Save-Json $created (Join-Path $EvidenceDir 'room-created.json')

$roomId = [string]$created.id
$roundId = [string]$created.active_round_id
$workspace = Join-Path $Root ("data\rooms\{0}\shared" -f $roomId)
New-Item -ItemType Directory -Force -Path $workspace | Out-Null



Invoke-RestMethod -Method Post -Uri "$Base/api/rooms/$roomId/rounds/$roundId/start" | Out-Null

$final = Wait-RoomTerminal -RoomId $roomId
Save-Json $final (Join-Path $EvidenceDir 'room-final.json')

Invoke-WebRequest -UseBasicParsing -Method Get `
    -Uri "$Base/api/rooms/$roomId/export?format=json" `
    -OutFile (Join-Path $EvidenceDir 'room-export.json')



$statusAfter = @(git status --short)
$statusAfter | Set-Content -LiteralPath (Join-Path $EvidenceDir 'git-status-after.txt') -Encoding UTF8

$summary = [ordered]@{
    test_id = $TestId
    repository_head = $head
    room_id = $roomId
    round_id = $roundId
    room_status = [string]$final.status
    evidence_directory = $EvidenceDir
    tracked_status_before = $statusBefore
    tracked_status_after = $statusAfter
}
Save-Json $summary (Join-Path $EvidenceDir 'run-summary.json')

Write-Host ""
Write-Host "$TestId complete."
Write-Host "Room: $roomId"
Write-Host "Status: $($final.status)"
Write-Host "Evidence: $EvidenceDir"
}
```
## 15. T10 — Custom deterministic capability lifecycle

**Purpose.** Exercise the P4 custom-capability path as an agent-facing workflow: author a bounded package, verify it deterministically, request protected registration, rediscover it on a later turn, and invoke the registered version.

**Fixture.** The PowerShell procedure creates `acceptance-lines.txt` with exactly three lines in the Room workspace.

**PASS.** A creates and verifies/registers `acceptance_count_lines`; registration becomes active after the authoring turn settles; a later Assignment rediscovers and invokes the registered capability; the reported count is 3; protected binding/registration evidence exists.

**PowerShell:**

```powershell
& {
$ErrorActionPreference = 'Stop'

$Root = 'C:\Codex Room'
$Base = 'http://127.0.0.1:8765'
$TestId = 'T10'
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$EvidenceDir = Join-Path $Root ("output\functional-acceptance\{0}-{1}" -f $TestId, $Stamp)

Set-Location $Root
New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null

function Save-Json {
    param([Parameter(Mandatory=$true)]$Value, [Parameter(Mandatory=$true)][string]$Path)
    $Value | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Wait-Health {
    param([int]$TimeoutSeconds = 120)
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        try {
            $health = Invoke-RestMethod -Method Get -Uri "$Base/api/health"
            if ($health.ok) { return $health }
        }
        catch {
        }
        Start-Sleep -Seconds 1
    } while ((Get-Date) -lt $deadline)
    throw "Codex Room did not become healthy within $TimeoutSeconds seconds."
}

function Get-Room {
    param([Parameter(Mandatory=$true)][string]$RoomId)
    Invoke-RestMethod -Method Get -Uri "$Base/api/rooms/$RoomId"
}

function Wait-RoomTerminal {
    param(
        [Parameter(Mandatory=$true)][string]$RoomId,
        [int]$TimeoutSeconds = 1800
    )
    $terminal = @('finished', 'error', 'stopped', 'paused')
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        $room = Get-Room -RoomId $RoomId
        if ($terminal -contains [string]$room.status) { return $room }
        Start-Sleep -Seconds 1
    } while ((Get-Date) -lt $deadline)
    throw "Room $RoomId did not reach a terminal/paused state within $TimeoutSeconds seconds."
}

$head = (git rev-parse HEAD).Trim()
$statusBefore = @(git status --short)
$head | Set-Content -LiteralPath (Join-Path $EvidenceDir 'git-head.txt') -Encoding ASCII
$statusBefore | Set-Content -LiteralPath (Join-Path $EvidenceDir 'git-status-before.txt') -Encoding UTF8

$health = Wait-Health
Save-Json $health (Join-Path $EvidenceDir 'health-before.json')

$prompt = @'
This is Functional Acceptance Test T10.

Use A for the custom deterministic capability workflow. C should coordinate and integrate, not implement the capability itself.

Have A consult the built-in capability authoring contract and create a lineage-scoped custom capability named `acceptance_count_lines`. It must:
- accept either explicit text or a workspace-relative text-file path;
- return JSON with boolean `ok` and integer `count`;
- count logical text lines;
- declare workspace read only, with no workspace write, network, or external-process permission;
- have no side effects;
- include deterministic verification cases for inline text and a fixture file.

A must run `codex-room-cap register acceptance_count_lines --cases-file <workspace-relative cases file>` from the Room workspace and COMPLETE that authoring Assignment after verification succeeds.

After that turn settles and host registration becomes active, create a fresh A Assignment. It must rediscover `acceptance_count_lines`, inspect it if useful, invoke it on the existing workspace file `acceptance-lines.txt`, and report the count.

C should report the registration/invocation result and COMPLETE. Do not substitute an ad-hoc one-off Python calculation for the registered-capability invocation.
'@

$body = @{
    title = 'T10 — Custom deterministic capability lifecycle'
    topic = $prompt
    auto_start = $false
    max_turns = 16
    max_consecutive_passes = 3
    inactivity_seconds = 900
    starting_agent = 'agent_c'
    completion_policy = 'auto_settle'
    required_contributors = @('agent_a')
} | ConvertTo-Json -Depth 20

$created = Invoke-RestMethod -Method Post -Uri "$Base/api/rooms" -ContentType 'application/json' -Body $body
Save-Json $created (Join-Path $EvidenceDir 'room-created.json')

$roomId = [string]$created.id
$roundId = [string]$created.active_round_id
$workspace = Join-Path $Root ("data\rooms\{0}\shared" -f $roomId)
New-Item -ItemType Directory -Force -Path $workspace | Out-Null

@(
'alpha'
'beta'
'gamma'
) | Set-Content -LiteralPath (Join-Path $workspace 'acceptance-lines.txt') -Encoding UTF8

Invoke-RestMethod -Method Post -Uri "$Base/api/rooms/$roomId/rounds/$roundId/start" | Out-Null

$final = Wait-RoomTerminal -RoomId $roomId
Save-Json $final (Join-Path $EvidenceDir 'room-final.json')

Invoke-WebRequest -UseBasicParsing -Method Get `
    -Uri "$Base/api/rooms/$roomId/export?format=json" `
    -OutFile (Join-Path $EvidenceDir 'room-export.json')

$bindingRoot = Join-Path $Root ("data\custom-capabilities\bindings\{0}" -f $roomId)
if (Test-Path -LiteralPath $bindingRoot) {
Get-ChildItem -LiteralPath $bindingRoot -Recurse -File |
    Select-Object FullName, Length |
    ConvertTo-Json -Depth 20 |
    Set-Content -LiteralPath (Join-Path $EvidenceDir 'custom-capability-binding-files.json') -Encoding UTF8
}

$statusAfter = @(git status --short)
$statusAfter | Set-Content -LiteralPath (Join-Path $EvidenceDir 'git-status-after.txt') -Encoding UTF8

$summary = [ordered]@{
    test_id = $TestId
    repository_head = $head
    room_id = $roomId
    round_id = $roundId
    room_status = [string]$final.status
    evidence_directory = $EvidenceDir
    tracked_status_before = $statusBefore
    tracked_status_after = $statusAfter
}
Save-Json $summary (Join-Path $EvidenceDir 'run-summary.json')

Write-Host ""
Write-Host "$TestId complete."
Write-Host "Room: $roomId"
Write-Host "Status: $($final.status)"
Write-Host "Evidence: $EvidenceDir"
}
```
## 16. T11 — Rollover continuity

**Purpose.** Exercise the public rollover path from a finished/quiescent Room into a prepared successor.

**PASS.** The predecessor finishes and becomes archived/sealed; rollover returns one successor in `preparing`; successor contains A/B/C, starts with C, uses production v2 assignment context, has distinct fresh participant provider/thread identities where required, carries the explicit checkpoint once, and can start/finish its successor Round normally.

**PowerShell:**

```powershell
& {
$ErrorActionPreference = 'Stop'

$Root = 'C:\Codex Room'
$Base = 'http://127.0.0.1:8765'
$TestId = 'T11'
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$EvidenceDir = Join-Path $Root ("output\functional-acceptance\{0}-{1}" -f $TestId, $Stamp)

Set-Location $Root
New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null

function Save-Json {
    param([Parameter(Mandatory=$true)]$Value, [Parameter(Mandatory=$true)][string]$Path)
    $Value | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $Path -Encoding UTF8
}
function Get-Room {
    param([string]$RoomId)
    Invoke-RestMethod -Method Get -Uri "$Base/api/rooms/$RoomId"
}
function Wait-Terminal {
    param([string]$RoomId, [int]$TimeoutSeconds = 1200)
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        $r = Get-Room $RoomId
        if (@('finished','error','stopped','paused') -contains [string]$r.status) { return $r }
        Start-Sleep -Seconds 1
    } while ((Get-Date) -lt $deadline)
    throw "Room $RoomId did not settle."
}

$head = (git rev-parse HEAD).Trim()
$head | Set-Content -LiteralPath (Join-Path $EvidenceDir 'git-head.txt') -Encoding ASCII

$sourcePrompt = @'
This is Functional Acceptance Test T11 source Room.
Report exactly: SOURCE-ROLLOVER-READY
Do not invoke peers. COMPLETE.
'@

$createBody = @{
    title = 'T11 — Rollover source'
    topic = $sourcePrompt
    auto_start = $false
    max_turns = 6
    max_consecutive_passes = 3
    inactivity_seconds = 900
    starting_agent = 'agent_c'
    completion_policy = 'auto_settle'
    required_contributors = @()
} | ConvertTo-Json -Depth 20

$source = Invoke-RestMethod -Method Post -Uri "$Base/api/rooms" -ContentType 'application/json' -Body $createBody
Save-Json $source (Join-Path $EvidenceDir 'source-created.json')
$sourceId = [string]$source.id
$sourceRound = [string]$source.active_round_id

Invoke-RestMethod -Method Post -Uri "$Base/api/rooms/$sourceId/rounds/$sourceRound/start" | Out-Null
$sourceFinal = Wait-Terminal $sourceId
Save-Json $sourceFinal (Join-Path $EvidenceDir 'source-final.json')
if ([string]$sourceFinal.status -ne 'finished') {
    throw "T11 source did not finish normally: $($sourceFinal.status)"
}

Start-Sleep -Seconds 1

$rolloverBody = @{
    checkpoint = 'T11 successor checkpoint: predecessor completed SOURCE-ROLLOVER-READY. Begin from this checkpoint only and report SUCCESSOR-ROLLOVER-READY.'
    title = 'T11 — Rollover successor'
} | ConvertTo-Json -Depth 10

$successor = Invoke-RestMethod -Method Post -Uri "$Base/api/rooms/$sourceId/rollover" -ContentType 'application/json' -Body $rolloverBody
Save-Json $successor (Join-Path $EvidenceDir 'successor-created.json')
$successorId = [string]$successor.id
$successorRound = [string]$successor.active_round_id

$predecessorAfter = Get-Room $sourceId
Save-Json $predecessorAfter (Join-Path $EvidenceDir 'predecessor-after-rollover.json')

Invoke-RestMethod -Method Post -Uri "$Base/api/rooms/$successorId/rounds/$successorRound/start" | Out-Null
$successorFinal = Wait-Terminal $successorId
Save-Json $successorFinal (Join-Path $EvidenceDir 'successor-final.json')

Invoke-WebRequest -UseBasicParsing -Method Get `
    -Uri "$Base/api/rooms/$sourceId/export?format=json" `
    -OutFile (Join-Path $EvidenceDir 'predecessor-export.json')
Invoke-WebRequest -UseBasicParsing -Method Get `
    -Uri "$Base/api/rooms/$successorId/export?format=json" `
    -OutFile (Join-Path $EvidenceDir 'successor-export.json')

Write-Host ""
Write-Host "T11 complete."
Write-Host "Predecessor: $sourceId ($($predecessorAfter.status))"
Write-Host "Successor:   $successorId ($($successorFinal.status))"
Write-Host "Evidence: $EvidenceDir"
}
```

---

## 17. T12 — Export and offline backup/verify

**Purpose.** Exercise a real complete Room export plus the offline persistent-data integrity/backup/verification workflow. Restore is intentionally excluded because it is destructive and adds no acceptance value when backup verification already proves the archive.

**PASS.** Room export succeeds; normal Kill stops the service; `check --offline-confirmed` succeeds; `backup --offline-confirmed` succeeds; the returned backup passes `verify`; the server restarts and `/api/health` becomes healthy.

**PowerShell:**

```powershell
& {
$ErrorActionPreference = 'Stop'

$Root = 'C:\Codex Room'
$Base = 'http://127.0.0.1:8765'
$TestId = 'T12'
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$EvidenceDir = Join-Path $Root ("output\functional-acceptance\{0}-{1}" -f $TestId, $Stamp)

Set-Location $Root
New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null

function Wait-Health {
    param([int]$TimeoutSeconds = 180)
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        try {
            $h = Invoke-RestMethod -Method Get -Uri "$Base/api/health"
            if ($h.ok) { return $h }
        } catch {
        }
        Start-Sleep -Seconds 1
    } while ((Get-Date) -lt $deadline)
    throw 'Codex Room did not become healthy.'
}
function Get-Room {
    param([string]$RoomId)
    Invoke-RestMethod -Method Get -Uri "$Base/api/rooms/$RoomId"
}
function Wait-Terminal {
    param([string]$RoomId, [int]$TimeoutSeconds = 900)
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        $r = Get-Room $RoomId
        if (@('finished','error','stopped','paused') -contains [string]$r.status) { return $r }
        Start-Sleep -Seconds 1
    } while ((Get-Date) -lt $deadline)
    throw "Room $RoomId did not settle."
}

$head = (git rev-parse HEAD).Trim()
$head | Set-Content -LiteralPath (Join-Path $EvidenceDir 'git-head.txt') -Encoding ASCII
Wait-Health | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath (Join-Path $EvidenceDir 'health-before.json') -Encoding UTF8

$body = @{
    title = 'T12 — Export and backup'
    topic = 'This is Functional Acceptance Test T12. Report exactly EXPORT-BACKUP-CANARY and COMPLETE. Do not invoke peers.'
    auto_start = $false
    max_turns = 6
    max_consecutive_passes = 3
    inactivity_seconds = 900
    starting_agent = 'agent_c'
    completion_policy = 'auto_settle'
    required_contributors = @()
} | ConvertTo-Json -Depth 20

$created = Invoke-RestMethod -Method Post -Uri "$Base/api/rooms" -ContentType 'application/json' -Body $body
$roomId = [string]$created.id
$roundId = [string]$created.active_round_id
Invoke-RestMethod -Method Post -Uri "$Base/api/rooms/$roomId/rounds/$roundId/start" | Out-Null
$final = Wait-Terminal $roomId
$final | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath (Join-Path $EvidenceDir 'room-final.json') -Encoding UTF8

Invoke-WebRequest -UseBasicParsing -Method Get `
    -Uri "$Base/api/rooms/$roomId/export?format=json" `
    -OutFile (Join-Path $EvidenceDir 'room-export.json')

& (Join-Path $Root 'Kill-Codex-Room.bat')
if ($LASTEXITCODE -ne 0) {
    throw "T12 failed: Kill-Codex-Room.bat exited $LASTEXITCODE."
}

$checkText = & (Join-Path $Root 'codex-room-maint.cmd') check --offline-confirmed | Out-String
$checkText | Set-Content -LiteralPath (Join-Path $EvidenceDir 'maintenance-check.json') -Encoding UTF8
if ($LASTEXITCODE -ne 0) {
    throw "T12 failed: maintenance check exited $LASTEXITCODE."
}
$check = $checkText | ConvertFrom-Json

$backupText = & (Join-Path $Root 'codex-room-maint.cmd') backup --offline-confirmed | Out-String
$backupText | Set-Content -LiteralPath (Join-Path $EvidenceDir 'maintenance-backup.json') -Encoding UTF8
if ($LASTEXITCODE -ne 0) {
    throw "T12 failed: maintenance backup exited $LASTEXITCODE."
}
$backup = $backupText | ConvertFrom-Json
$backupPath = [string]$backup.backup

$verifyText = & (Join-Path $Root 'codex-room-maint.cmd') verify $backupPath | Out-String
$verifyText | Set-Content -LiteralPath (Join-Path $EvidenceDir 'maintenance-verify.json') -Encoding UTF8
if ($LASTEXITCODE -ne 0) {
    throw "T12 failed: backup verify exited $LASTEXITCODE."
}

Start-Process -FilePath 'cmd.exe' -ArgumentList @('/c', "`"$Root\Start-Codex-Room.cmd`" --no-browser")
$healthAfter = Wait-Health
$healthAfter | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath (Join-Path $EvidenceDir 'health-after.json') -Encoding UTF8

Write-Host ""
Write-Host "T12 PASS candidate."
Write-Host "Room: $roomId"
Write-Host "Backup: $backupPath"
Write-Host "Evidence: $EvidenceDir"
}
```

---

## 18. T13 — Explicit model-allocation exercise

**Purpose.** Verify the production execution-config surface across admitted Luna/Terra/Sol configurations and that exact per-assignment execution metadata is observable.

This is a mechanical allocation test. It deliberately specifies configurations so that a failure can be attributed to execution selection rather than to C's discretionary model-choice judgment.

**PASS.** C delegates both assignments together; A runs with `luna-medium`; B runs with `sol-medium`; both complete; C integrates. Export/runtime evidence reflects the requested configurations. Any Astra use is FAIL.

**PowerShell:**

```powershell
& {
$ErrorActionPreference = 'Stop'

$Root = 'C:\Codex Room'
$Base = 'http://127.0.0.1:8765'
$TestId = 'T13'
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$EvidenceDir = Join-Path $Root ("output\functional-acceptance\{0}-{1}" -f $TestId, $Stamp)

Set-Location $Root
New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null

function Save-Json {
    param([Parameter(Mandatory=$true)]$Value, [Parameter(Mandatory=$true)][string]$Path)
    $Value | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Wait-Health {
    param([int]$TimeoutSeconds = 120)
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        try {
            $health = Invoke-RestMethod -Method Get -Uri "$Base/api/health"
            if ($health.ok) { return $health }
        }
        catch {
        }
        Start-Sleep -Seconds 1
    } while ((Get-Date) -lt $deadline)
    throw "Codex Room did not become healthy within $TimeoutSeconds seconds."
}

function Get-Room {
    param([Parameter(Mandatory=$true)][string]$RoomId)
    Invoke-RestMethod -Method Get -Uri "$Base/api/rooms/$RoomId"
}

function Wait-RoomTerminal {
    param(
        [Parameter(Mandatory=$true)][string]$RoomId,
        [int]$TimeoutSeconds = 1800
    )
    $terminal = @('finished', 'error', 'stopped', 'paused')
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        $room = Get-Room -RoomId $RoomId
        if ($terminal -contains [string]$room.status) { return $room }
        Start-Sleep -Seconds 1
    } while ((Get-Date) -lt $deadline)
    throw "Room $RoomId did not reach a terminal/paused state within $TimeoutSeconds seconds."
}

$head = (git rev-parse HEAD).Trim()
$statusBefore = @(git status --short)
$head | Set-Content -LiteralPath (Join-Path $EvidenceDir 'git-head.txt') -Encoding ASCII
$statusBefore | Set-Content -LiteralPath (Join-Path $EvidenceDir 'git-status-before.txt') -Encoding UTF8

$health = Wait-Health
Save-Json $health (Join-Path $EvidenceDir 'health-before.json')

$prompt = @'
This is Functional Acceptance Test T13.

Issue two independent delegations together with these explicit execution configurations:

- A with `luna-medium`: count the vowels in the exact string `functional acceptance telemetry` and show the counted letters.
- B with `sol-medium`: analyze this ambiguity in at most five sentences: `A system must minimize model calls, preserve independent verification where it materially improves correctness, and avoid unnecessary duplication. Explain when a second model call is justified.`

Do not change the requested execution configurations. After both return, report each result and which requested configuration was used, then COMPLETE.
'@

$body = @{
    title = 'T13 — Explicit model allocation'
    topic = $prompt
    auto_start = $false
    max_turns = 10
    max_consecutive_passes = 3
    inactivity_seconds = 900
    starting_agent = 'agent_c'
    completion_policy = 'auto_settle'
    required_contributors = @('agent_a','agent_b')
} | ConvertTo-Json -Depth 20

$created = Invoke-RestMethod -Method Post -Uri "$Base/api/rooms" -ContentType 'application/json' -Body $body
Save-Json $created (Join-Path $EvidenceDir 'room-created.json')

$roomId = [string]$created.id
$roundId = [string]$created.active_round_id
$workspace = Join-Path $Root ("data\rooms\{0}\shared" -f $roomId)
New-Item -ItemType Directory -Force -Path $workspace | Out-Null



Invoke-RestMethod -Method Post -Uri "$Base/api/rooms/$roomId/rounds/$roundId/start" | Out-Null

$final = Wait-RoomTerminal -RoomId $roomId
Save-Json $final (Join-Path $EvidenceDir 'room-final.json')

Invoke-WebRequest -UseBasicParsing -Method Get `
    -Uri "$Base/api/rooms/$roomId/export?format=json" `
    -OutFile (Join-Path $EvidenceDir 'room-export.json')



$statusAfter = @(git status --short)
$statusAfter | Set-Content -LiteralPath (Join-Path $EvidenceDir 'git-status-after.txt') -Encoding UTF8

$summary = [ordered]@{
    test_id = $TestId
    repository_head = $head
    room_id = $roomId
    round_id = $roundId
    room_status = [string]$final.status
    evidence_directory = $EvidenceDir
    tracked_status_before = $statusBefore
    tracked_status_after = $statusAfter
}
Save-Json $summary (Join-Path $EvidenceDir 'run-summary.json')

Write-Host ""
Write-Host "$TestId complete."
Write-Host "Room: $roomId"
Write-Host "Status: $($final.status)"
Write-Host "Evidence: $EvidenceDir"
}
```
## 19. T14 — Integrated naturalistic mission

**Purpose.** Capstone acceptance exercise. This tests whether the organization can transform a small concrete objective into implementation, verification, evidence, and an integrated result using ordinary production behavior.

**Fixture.** The script creates `orders.csv` in the fresh Room workspace.

**Requested outcome.** Produce:
- `summarize_orders.py`;
- `acceptance-summary.json`;
- a concise final report.

Expected summary values:
- `total_orders`: 5
- `total_amount`: 150.0
- regional totals: North 62.5, South 70.0, West 17.5

**PASS.** C chooses a coherent work topology; implementation precedes artifact-dependent verification; A/B responsibilities are meaningfully differentiated when both are used; deterministic evidence/capabilities are used where they add value; the produced JSON is correct; independent verification occurs; transaction closes without lifecycle anomalies. Exact delegation wording is not part of PASS.

**PowerShell:**

```powershell
& {
$ErrorActionPreference = 'Stop'

$Root = 'C:\Codex Room'
$Base = 'http://127.0.0.1:8765'
$TestId = 'T14'
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$EvidenceDir = Join-Path $Root ("output\functional-acceptance\{0}-{1}" -f $TestId, $Stamp)

Set-Location $Root
New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null

function Save-Json {
    param([Parameter(Mandatory=$true)]$Value, [Parameter(Mandatory=$true)][string]$Path)
    $Value | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Wait-Health {
    param([int]$TimeoutSeconds = 120)
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        try {
            $health = Invoke-RestMethod -Method Get -Uri "$Base/api/health"
            if ($health.ok) { return $health }
        }
        catch {
        }
        Start-Sleep -Seconds 1
    } while ((Get-Date) -lt $deadline)
    throw "Codex Room did not become healthy within $TimeoutSeconds seconds."
}

function Get-Room {
    param([Parameter(Mandatory=$true)][string]$RoomId)
    Invoke-RestMethod -Method Get -Uri "$Base/api/rooms/$RoomId"
}

function Wait-RoomTerminal {
    param(
        [Parameter(Mandatory=$true)][string]$RoomId,
        [int]$TimeoutSeconds = 1800
    )
    $terminal = @('finished', 'error', 'stopped', 'paused')
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        $room = Get-Room -RoomId $RoomId
        if ($terminal -contains [string]$room.status) { return $room }
        Start-Sleep -Seconds 1
    } while ((Get-Date) -lt $deadline)
    throw "Room $RoomId did not reach a terminal/paused state within $TimeoutSeconds seconds."
}

$head = (git rev-parse HEAD).Trim()
$statusBefore = @(git status --short)
$head | Set-Content -LiteralPath (Join-Path $EvidenceDir 'git-head.txt') -Encoding ASCII
$statusBefore | Set-Content -LiteralPath (Join-Path $EvidenceDir 'git-status-before.txt') -Encoding UTF8

$health = Wait-Health
Save-Json $health (Join-Path $EvidenceDir 'health-before.json')

$prompt = @'
This is Functional Acceptance Test T14, the capstone.

The Room workspace contains `orders.csv`. Deliver a verified mini data-processing artifact.

Required outputs in the shared workspace:
1. `summarize_orders.py` — a small Python program using only the standard library. It reads `orders.csv` and writes `acceptance-summary.json`.
2. `acceptance-summary.json` with:
   - `total_orders`
   - `total_amount`
   - `region_totals`
3. A concise integrated final report stating what was implemented and how the exact artifact was verified.

Coordinate the organization normally. Preserve dependency ordering: artifact-dependent verification must inspect the artifact after implementation exists. Use deterministic registered capabilities or structured evidence where they are adequate. Keep implementation and verification responsibilities meaningfully distinct. If a correction is needed, use the ordinary bounded correction/verification path.

Do not expand scope beyond this fixture and these outputs. COMPLETE when the exact generated artifact has been verified.
'@

$body = @{
    title = 'T14 — Integrated naturalistic mission'
    topic = $prompt
    auto_start = $false
    max_turns = 18
    max_consecutive_passes = 3
    inactivity_seconds = 900
    starting_agent = 'agent_c'
    completion_policy = 'auto_settle'
    required_contributors = @('agent_a','agent_b')
} | ConvertTo-Json -Depth 20

$created = Invoke-RestMethod -Method Post -Uri "$Base/api/rooms" -ContentType 'application/json' -Body $body
Save-Json $created (Join-Path $EvidenceDir 'room-created.json')

$roomId = [string]$created.id
$roundId = [string]$created.active_round_id
$workspace = Join-Path $Root ("data\rooms\{0}\shared" -f $roomId)
New-Item -ItemType Directory -Force -Path $workspace | Out-Null

@'
order_id,region,amount
1,North,12.50
2,South,20.00
3,West,17.50
4,North,50.00
5,South,50.00
'@ | Set-Content -LiteralPath (Join-Path $workspace 'orders.csv') -Encoding UTF8

Invoke-RestMethod -Method Post -Uri "$Base/api/rooms/$roomId/rounds/$roundId/start" | Out-Null

$final = Wait-RoomTerminal -RoomId $roomId
Save-Json $final (Join-Path $EvidenceDir 'room-final.json')

Invoke-WebRequest -UseBasicParsing -Method Get `
    -Uri "$Base/api/rooms/$roomId/export?format=json" `
    -OutFile (Join-Path $EvidenceDir 'room-export.json')

$summaryPath = Join-Path $workspace 'acceptance-summary.json'
$scriptPath = Join-Path $workspace 'summarize_orders.py'
if (Test-Path -LiteralPath $summaryPath) {
Copy-Item -LiteralPath $summaryPath -Destination (Join-Path $EvidenceDir 'acceptance-summary.json')
}
if (Test-Path -LiteralPath $scriptPath) {
Copy-Item -LiteralPath $scriptPath -Destination (Join-Path $EvidenceDir 'summarize_orders.py')
}

$statusAfter = @(git status --short)
$statusAfter | Set-Content -LiteralPath (Join-Path $EvidenceDir 'git-status-after.txt') -Encoding UTF8

$summary = [ordered]@{
    test_id = $TestId
    repository_head = $head
    room_id = $roomId
    round_id = $roundId
    room_status = [string]$final.status
    evidence_directory = $EvidenceDir
    tracked_status_before = $statusBefore
    tracked_status_after = $statusAfter
}
Save-Json $summary (Join-Path $EvidenceDir 'run-summary.json')

Write-Host ""
Write-Host "$TestId complete."
Write-Host "Room: $roomId"
Write-Host "Status: $($final.status)"
Write-Host "Evidence: $EvidenceDir"
}
```
## 20. Results ledger

Update this table only with evidence from an actual run. Keep the exact HEAD and evidence-directory path.

| Test | Status | HEAD | Room / evidence reference | Notes |
|---|---|---|---|---|
| T0 | PASS | `ef92dcf6991db58208a9340c28d14ad7e3478a1c` | `output\functional-acceptance\T0-20260919-005013` | `/api/health` healthy; `verify-fast.cmd` PASS: Linux focused core 63/63, Windows portability 118/118, browser transcript stability 3/3; repository status unchanged. |
| T1 | PASS | `fcd9e8b4c643388e71e4c15a2ee95664f319aa7a` | `room_ec1beb0323644ebf8d1d842e993fa492` / `output\functional-acceptance\T1-20260919-005645` | Fresh Room contained A/B/C; C started; one C Assignment completed; `peer_invocations=0`; no A/B execution; Room settled normally. |
| T2 | NOT RUN | — | — | — |
| T3 | NOT RUN | — | — | — |
| T4 | NOT RUN | — | — | — |
| T5 | NOT RUN | — | — | — |
| T6 | NOT RUN | — | — | — |
| T7 | NOT RUN | — | — | — |
| T8 | NOT RUN | — | — | — |
| T9 | NOT RUN | — | — | — |
| T10 | NOT RUN | — | — | — |
| T11 | NOT RUN | — | — | — |
| T12 | NOT RUN | — | — | — |
| T13 | NOT RUN | — | — | — |
| T14 | NOT RUN | — | — | — |

## 21. Evaluation procedure after each live test

For T1–T14, retain the generated evidence directory and evaluate the complete `room-export.json`, not only the final prose answer.

Check, as applicable:

- exact Room/Round/Task/Assignment/Join lifecycle;
- participants actually invoked;
- assignment creation order and dependency release;
- provider-context lineage IDs;
- direct-return / relay-waiver provenance;
- EVIDENCE/HISTORY selected-source or selected-event provenance;
- REFRESH old/new context identities and checkpoint provenance;
- exact execution model/effort metadata;
- duplicate/stale execution indicators;
- Room terminal state;
- fixture/output bytes and hashes;
- tracked Git status before/after where captured.

A surprising model choice should first be classified as:
1. permitted variation;
2. test did not exercise intended branch → INCONCLUSIVE;
3. behavioral quality concern;
4. product/runtime invariant violation → FAIL.

Only category 4 automatically implies a demonstrated implementation defect.

## 22. Campaign stop and closeout

The campaign is complete when T0–T14 have each reached PASS, FAIL, or a deliberately accepted INCONCLUSIVE disposition and the results ledger references preserved evidence.

At closeout:

1. summarize demonstrated failures and behavioral concerns separately;
2. avoid opening repair work for healthy features;
3. promote only consequential new empirical findings into the Evidence Register;
4. update Development Control only if the evidence changes current priority, issue state, or planned work;
5. keep this file as the repeatable operational specification for later regression/acceptance campaigns.

If a test procedure itself is found defective, revise the procedure with a new date and preserve the evidence from the invalid run as test-harness evidence, not product-failure evidence.
