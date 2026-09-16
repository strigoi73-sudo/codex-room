[CmdletBinding()]
param(
    [ValidateSet("Fast", "Full")]
    [string]$Mode = "Fast",

    [string]$Distro = "Ubuntu"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0

$repoRoot = $PSScriptRoot
$wsl = "$env:SystemRoot\System32\wsl.exe"
$results = @()

function Write-Phase {
    param([string]$Message)
    Write-Host ""
    Write-Host "=== $Message ==="
}

function Invoke-NativeStep {
    param(
        [string]$Name,
        [scriptblock]$Action
    )

    Write-Phase $Name
    $timer = [System.Diagnostics.Stopwatch]::StartNew()
    & $Action
    $code = $LASTEXITCODE
    $timer.Stop()

    $script:results += New-Object PSObject -Property @{
        Step = $Name
        Seconds = [math]::Round($timer.Elapsed.TotalSeconds, 1)
        ExitCode = $code
    }

    if ($code -ne 0) {
        throw "$Name failed with exit code $code."
    }
}

function Get-WindowsPython {
    $cacheRoot = Join-Path $env:LOCALAPPDATA "CodexRoom\verify\windows"
    $python = Join-Path $cacheRoot "Scripts\python.exe"

    if (Test-Path -LiteralPath $python) {
        return $python
    }

    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $cacheRoot) | Out-Null

    $py = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($py) {
        & $py.Source -3.12 -m venv $cacheRoot
    }
    else {
        $systemPython = Get-Command python.exe -ErrorAction SilentlyContinue
        if (-not $systemPython) {
            throw "No Windows Python launcher was found."
        }
        & $systemPython.Source -m venv $cacheRoot
    }

    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $python)) {
        throw "Could not create the Windows verification environment."
    }

    return $python
}

function Invoke-LinuxPytest {
    param(
        [string]$Series,
        [string]$Label
    )

    if (-not (Test-Path -LiteralPath $wsl)) {
        throw "WSL was not found at $wsl."
    }

    $wslRepo = (& $wsl -d $Distro -- wslpath -a $repoRoot).Trim()
    if ($LASTEXITCODE -ne 0 -or -not $wslRepo) {
        throw "Could not resolve the repository path inside WSL."
    }

    $bash = @'
set -euo pipefail

repo="$CODEX_ROOM_REPO"
series="$CODEX_ROOM_PYTHON_SERIES"

find_python() {
    if command -v "python${series}" >/dev/null 2>&1; then
        command -v "python${series}"
        return
    fi

    candidate="$(
        find "$HOME/actions-runner/_work/_tool/Python" \
            -type f \
            -path "*/${series}.*/*/bin/python" \
            2>/dev/null |
        sort -V |
        tail -n 1
    )"

    if [ -n "$candidate" ]; then
        printf '%s\n' "$candidate"
        return
    fi

    if [ "$series" = "3.12" ] && command -v python3 >/dev/null 2>&1; then
        command -v python3
        return
    fi

    return 1
}

source_python="$(find_python)" || {
    echo "Python ${series} is not available inside WSL." >&2
    exit 2
}

venv="$HOME/.cache/codex-room-verify/python-${series}"

if [ ! -x "$venv/bin/python" ]; then
    mkdir -p "$(dirname "$venv")"
    "$source_python" -m venv "$venv"
fi

cd "$repo"
"$venv/bin/python" -m pip install --disable-pip-version-check -q \
    -c constraints-test.txt "${repo}[test]"

tmp_dir="$(mktemp -d /dev/shm/codex-room-verify.XXXXXX)"
trap 'rm -rf "$tmp_dir"' EXIT

TMPDIR="$tmp_dir" "$venv/bin/python" -m pytest -q
'@

    # Windows checkouts may convert this PowerShell file to CRLF. Bash requires LF.
    $bash = $bash.Replace("`r`n", "`n").Replace("`r", "")

    Invoke-NativeStep $Label {
        $args = @(
            "-d", $Distro,
            "--",
            "env",
            "CODEX_ROOM_REPO=$wslRepo",
            "CODEX_ROOM_PYTHON_SERIES=$Series",
            "bash", "-lc", $bash
        )
        & $wsl @args
    }
}

function Sync-WindowsDependencies {
    param([string]$Python)

    Invoke-NativeStep "Windows dependency sync" {
        Push-Location $repoRoot
        try {
            $args = @(
                "-m", "pip", "install",
                "--disable-pip-version-check", "-q",
                "-c", "constraints-test.txt",
                ".[test]"
            )
            & $Python @args
        }
        finally {
            Pop-Location
        }
    }
}

function Invoke-WindowsFocused {
    param([string]$Python)

    Invoke-NativeStep "Windows focused portability tests" {
        Push-Location $repoRoot
        try {
            $args = @(
                "-m", "pytest", "-q",
                "tests/test_capabilities.py",
                "tests/test_source_inspection.py",
                "tests/test_launcher.py",
                "tests/test_orchestrator.py::test_multiple_retry_warnings_project_to_one_recovered_logical_turn",
                "tests/test_orchestrator.py::test_retry_exhaustion_is_the_only_terminal_agent_error"
            )
            & $Python @args
        }
        finally {
            Pop-Location
        }
    }

    Invoke-NativeStep "Browser transcript stability" {
        $args = @(
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-File", (Join-Path $repoRoot "test-transcript-stability.ps1")
        )
        & powershell.exe @args
    }
}

function Invoke-WindowsFull {
    param([string]$Python)

    Invoke-NativeStep "Windows full pytest" {
        Push-Location $repoRoot
        try {
            & $Python -m pytest -q --durations=25
        }
        finally {
            Pop-Location
        }
    }

    Invoke-NativeStep "Browser transcript stability" {
        $args = @(
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-File", (Join-Path $repoRoot "test-transcript-stability.ps1")
        )
        & powershell.exe @args
    }
}

function Invoke-DependencyAudit {
    param([string]$Python)

    Invoke-NativeStep "Install dependency auditor" {
        & $Python -m pip install --disable-pip-version-check -q "pip-audit==2.10.1"
    }

    Invoke-NativeStep "Dependency audit" {
        Push-Location $repoRoot
        try {
            & $Python -m pip_audit -r constraints-test.txt --strict --no-deps
        }
        finally {
            Pop-Location
        }
    }
}

Write-Phase "Codex Room local verification"

$commit = (& git -C $repoRoot rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0) {
    throw "Could not read the repository commit."
}

$status = @(& git -C $repoRoot status --porcelain)
if ($LASTEXITCODE -ne 0) {
    throw "Could not read the repository working-tree status."
}

Write-Host "Mode:   $Mode"
Write-Host "Commit: $commit"

if ($status.Count -gt 0) {
    Write-Warning "Working tree is dirty. Results apply to the exact working tree, not only commit $commit."
}
else {
    Write-Host "Tree:   clean"
}

$overall = [System.Diagnostics.Stopwatch]::StartNew()

try {
    $windowsPython = Get-WindowsPython

    Invoke-LinuxPytest -Series "3.12" -Label "Linux Python 3.12 full pytest"
    Sync-WindowsDependencies -Python $windowsPython

    if ($Mode -eq "Fast") {
        Invoke-WindowsFocused -Python $windowsPython
    }
    else {
        Invoke-LinuxPytest -Series "3.11" -Label "Linux Python 3.11 full pytest"
        Invoke-WindowsFull -Python $windowsPython
        Invoke-DependencyAudit -Python $windowsPython
    }

    $overall.Stop()

    Write-Phase "Verification summary"
    $results | Sort-Object Step | Format-Table Step, Seconds, ExitCode -AutoSize
    Write-Host "Total seconds: $([math]::Round($overall.Elapsed.TotalSeconds, 1))"
    Write-Host "RESULT: PASS"
    exit 0
}
catch {
    $overall.Stop()

    Write-Host ""
    Write-Host "RESULT: FAIL"
    Write-Host $_.Exception.Message

    if ($results.Count -gt 0) {
        Write-Host ""
        $results | Sort-Object Step | Format-Table Step, Seconds, ExitCode -AutoSize
    }

    Write-Host "Total seconds: $([math]::Round($overall.Elapsed.TotalSeconds, 1))"
    exit 1
}
