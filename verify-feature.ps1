[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidatePattern("^[0-9a-fA-F]{40}$")]
    [string]$Base,

    [Parameter(Mandatory)]
    [ValidatePattern("^[0-9a-fA-F]{40}$")]
    [string]$Head,

    [string[]]$FocusedTests = @(),

    [ValidateSet("Fast", "Full")]
    [string]$Mode = "Fast",

    [switch]$RequireDirectParent
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $false

$repoRoot = $PSScriptRoot
$startingLocation = (Get-Location).Path
$killScript = Join-Path $repoRoot "Kill-Codex-Room.bat"
$verifyCommandName = if ($Mode -eq "Full") {
    "verify-full.cmd"
}
else {
    "verify-fast.cmd"
}
$verifyCommand = Join-Path $repoRoot $verifyCommandName
$verifyPython = Join-Path $env:LOCALAPPDATA "CodexRoom\verify\windows\Scripts\python.exe"

$originalBranch = $null
$originalHead = $null
$didCheckout = $false
$primaryError = $null
$restoreError = $null
$broadVerificationRan = $false

function Write-Phase {
    param([string]$Message)

    Write-Host ""
    Write-Host "=== $Message ==="
}

function Assert-NativeSuccess {
    param(
        [int]$ExitCode,
        [string]$Operation
    )

    if ($ExitCode -ne 0) {
        throw "$Operation failed with exit code $ExitCode."
    }
}

function Invoke-BroadVerification {
    Write-Phase "REPOSITORY $($Mode.ToUpperInvariant()) GATE"
    & $verifyCommand
    $code = $LASTEXITCODE
    Assert-NativeSuccess -ExitCode $code -Operation "$Mode repository verification"
    $script:broadVerificationRan = $true
}

function Invoke-FocusedVerification {
    if ($FocusedTests.Count -eq 0) {
        return
    }

    if (-not (Test-Path -LiteralPath $verifyPython)) {
        Write-Host "Verification Python is not initialized; running the repository gate first."
        Invoke-BroadVerification
    }

    Write-Phase "FOCUSED PYTEST"
    $pytestArgs = @("-m", "pytest", "-q") + $FocusedTests
    & $verifyPython @pytestArgs
    $code = $LASTEXITCODE
    Assert-NativeSuccess -ExitCode $code -Operation "Focused pytest"
}

try {
    Set-Location $repoRoot

    Write-Phase "PRECHECK"
    Write-Host "Base: $Base"
    Write-Host "Head: $Head"
    Write-Host "Mode: $Mode"

    $originalBranchRaw = & git branch --show-current
    $code = $LASTEXITCODE
    Assert-NativeSuccess -ExitCode $code -Operation "Read current branch"
    $originalBranch = "$originalBranchRaw".Trim()

    $originalHeadRaw = & git rev-parse HEAD
    $code = $LASTEXITCODE
    Assert-NativeSuccess -ExitCode $code -Operation "Read current HEAD"
    $originalHead = "$originalHeadRaw".Trim()

    $trackedStatus = @(& git status --porcelain --untracked-files=no)
    $code = $LASTEXITCODE
    Assert-NativeSuccess -ExitCode $code -Operation "Read tracked working-tree status"

    if ($trackedStatus.Count -gt 0) {
        throw "Tracked working-tree changes are present. Verification requires a clean tracked tree."
    }

    $listeners = @(
        Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue
    )

    if ($listeners.Count -gt 0) {
        Write-Phase "STOP ROOM"
        & $killScript
        $code = $LASTEXITCODE
        Assert-NativeSuccess -ExitCode $code -Operation "Kill-Codex-Room.bat"

        Start-Sleep -Seconds 2

        $listenersAfterKill = @(
            Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue
        )
        if ($listenersAfterKill.Count -gt 0) {
            throw "Codex Room is still listening on port 8765 after Kill-Codex-Room.bat."
        }
    }

    Write-Phase "RESOLVE EXACT REFS"

    & git fetch origin --prune
    $code = $LASTEXITCODE
    Assert-NativeSuccess -ExitCode $code -Operation "git fetch origin --prune"

    $remoteMainRaw = & git rev-parse refs/remotes/origin/main
    $code = $LASTEXITCODE
    Assert-NativeSuccess -ExitCode $code -Operation "Resolve origin/main"
    $remoteMain = "$remoteMainRaw".Trim()

    if ($remoteMain -ne $Base) {
        throw "origin/main does not match the requested base. Expected $Base; found $remoteMain."
    }

    $resolvedHeadRaw = & git rev-parse "$Head^{commit}"
    $code = $LASTEXITCODE
    Assert-NativeSuccess -ExitCode $code -Operation "Resolve requested head"
    $resolvedHead = "$resolvedHeadRaw".Trim()

    if ($resolvedHead -ne $Head) {
        throw "Requested head did not resolve exactly. Expected $Head; found $resolvedHead."
    }

    & git merge-base --is-ancestor $Base $Head
    $code = $LASTEXITCODE
    if ($code -eq 1) {
        throw "Requested base $Base is not an ancestor of head $Head."
    }
    Assert-NativeSuccess -ExitCode $code -Operation "Verify base ancestry"

    if ($RequireDirectParent) {
        $parentRaw = & git rev-parse "$Head^"
        $code = $LASTEXITCODE
        Assert-NativeSuccess -ExitCode $code -Operation "Resolve head parent"
        $parent = "$parentRaw".Trim()

        if ($parent -ne $Base) {
            throw "Head parent does not match the requested base. Expected $Base; found $parent."
        }
    }

    & git diff --check "$Base...$Head"
    $code = $LASTEXITCODE
    Assert-NativeSuccess -ExitCode $code -Operation "git diff --check"

    Write-Phase "CHECKOUT EXACT HEAD"

    & git switch --detach $Head
    $code = $LASTEXITCODE
    Assert-NativeSuccess -ExitCode $code -Operation "Checkout exact head"
    $didCheckout = $true

    $checkedHeadRaw = & git rev-parse HEAD
    $code = $LASTEXITCODE
    Assert-NativeSuccess -ExitCode $code -Operation "Confirm checked-out HEAD"
    $checkedHead = "$checkedHeadRaw".Trim()

    if ($checkedHead -ne $Head) {
        throw "Checked-out HEAD does not match the requested head."
    }

    $checkedStatus = @(& git status --porcelain --untracked-files=no)
    $code = $LASTEXITCODE
    Assert-NativeSuccess -ExitCode $code -Operation "Confirm checked-out tracked tree"

    if ($checkedStatus.Count -gt 0) {
        throw "Exact-head checkout has tracked working-tree changes."
    }

    Invoke-FocusedVerification

    if (-not $broadVerificationRan) {
        Invoke-BroadVerification
    }

    Write-Phase "FINAL EXACT-HEAD CHECK"

    $finalHeadRaw = & git rev-parse HEAD
    $code = $LASTEXITCODE
    Assert-NativeSuccess -ExitCode $code -Operation "Read final HEAD"
    $finalHead = "$finalHeadRaw".Trim()

    if ($finalHead -ne $Head) {
        throw "HEAD changed during verification. Expected $Head; found $finalHead."
    }

    $finalStatus = @(& git status --porcelain --untracked-files=no)
    $code = $LASTEXITCODE
    Assert-NativeSuccess -ExitCode $code -Operation "Read final tracked tree"

    if ($finalStatus.Count -gt 0) {
        throw "Verification left tracked working-tree changes."
    }
}
catch {
    $primaryError = $_
}
finally {
    try {
        if ($didCheckout -and $null -ne $originalHead) {
            Write-Phase "RESTORE"

            if ($originalBranch) {
                & git switch --quiet $originalBranch
                $code = $LASTEXITCODE
                Assert-NativeSuccess -ExitCode $code -Operation "Restore original branch"
            }
            else {
                & git switch --detach $originalHead
                $code = $LASTEXITCODE
                Assert-NativeSuccess -ExitCode $code -Operation "Restore original detached HEAD"
            }

            $restoredHeadRaw = & git rev-parse HEAD
            $code = $LASTEXITCODE
            Assert-NativeSuccess -ExitCode $code -Operation "Confirm restored HEAD"
            $restoredHead = "$restoredHeadRaw".Trim()

            if ($restoredHead -ne $originalHead) {
                throw "Restored HEAD does not match the starting HEAD. Expected $originalHead; found $restoredHead."
            }
        }
    }
    catch {
        $restoreError = $_
    }
    finally {
        Set-Location $startingLocation
    }
}

if ($null -ne $primaryError) {
    Write-Host ""
    Write-Host "RESULT: FAIL"
    Write-Host $primaryError.Exception.Message

    if ($null -ne $restoreError) {
        Write-Host "RESTORE ERROR: $($restoreError.Exception.Message)"
    }

    throw $primaryError
}

if ($null -ne $restoreError) {
    Write-Host ""
    Write-Host "RESULT: FAIL"
    Write-Host "RESTORE ERROR: $($restoreError.Exception.Message)"
    throw $restoreError
}

Write-Host ""
Write-Host "RESULT: PASS"
Write-Host "Verified exact feature head: $Head"
