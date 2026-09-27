[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepoRoot = $PSScriptRoot

Write-Host "=== I-028 OUB v2 Phase 3 WSL validation ==="

wsl.exe -e bash -lc "true"
$wslProbeExit = $LASTEXITCODE
if ($wslProbeExit -ne 0) {
    Write-Host "ERROR: WSL is not available."
    return
}

Write-Host ""
Write-Host "=== Provisioning Ubuntu build prerequisites ==="
wsl.exe -u root -- bash -lc @'
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update -o Acquire::ForceIPv4=true -o Acquire::Retries=3
apt-get install -y --no-install-recommends   build-essential   pkg-config   libssl-dev   ca-certificates   curl   git   python3   python3-venv
'@
$aptExit = $LASTEXITCODE
if ($aptExit -ne 0) {
    Write-Host "ERROR: Ubuntu prerequisite installation failed with exit code $aptExit."
    return
}

Write-Host ""
Write-Host "=== Provisioning isolated user toolchains ==="
wsl.exe -e bash -lc @'
set -euo pipefail

export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

if ! command -v uv >/dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

uv python install 3.10 3.11

if ! command -v rustup >/dev/null 2>&1; then
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs       | sh -s -- -y --profile minimal --default-toolchain 1.80.0
fi

export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
rustup toolchain install 1.80.0 --profile minimal

printf 'uv: '
uv --version
printf 'rustc: '
RUSTUP_TOOLCHAIN=1.80.0 rustc --version
printf 'cargo: '
RUSTUP_TOOLCHAIN=1.80.0 cargo --version
'@
$toolchainExit = $LASTEXITCODE
if ($toolchainExit -ne 0) {
    Write-Host "ERROR: WSL user-toolchain provisioning failed with exit code $toolchainExit."
    return
}

$repoWsl = (wsl.exe wslpath -a -u "$RepoRoot" | Select-Object -Last 1).Trim()
$wslPathExit = $LASTEXITCODE
if (($wslPathExit -ne 0) -or [string]::IsNullOrWhiteSpace($repoWsl)) {
    Write-Host "ERROR: Could not resolve the repository path inside WSL."
    return
}

$escapedRepo = $repoWsl.Replace("'", "'"'"'")

Write-Host ""
Write-Host "=== Running frozen Phase 3 checks ==="
$command = @"
set -euo pipefail
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
cd '$escapedRepo'
python3 benchmarks/oub/v2/validate_phase3_native.py
"@

wsl.exe -e bash -lc $command
$phase3Exit = $LASTEXITCODE

Write-Host ""
Write-Host "Phase 3 validator exit code: $phase3Exit"

if ($phase3Exit -eq 0) {
    Write-Host "Phase 3 deterministic gate: PASS"
} elseif ($phase3Exit -eq 3) {
    Write-Host "Phase 3 deterministic gate: ENVIRONMENT FAILURE"
} else {
    Write-Host "Phase 3 deterministic gate: TASK/VALIDATION FAILURE"
}
