[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepoRoot = $PSScriptRoot

Write-Host "=== I-028 OUB v2 Phase 3 WSL validation ==="

$probeOutput = @(wsl.exe -e sh -c 'printf ok' 2>&1)
$wslProbeExit = $LASTEXITCODE
$probeText = $probeOutput -join [Environment]::NewLine

if ($wslProbeExit -ne 0) {
    Write-Host "ERROR: WSL is not available."
    $probeOutput | ForEach-Object { Write-Host $_ }
    return
}

if ($probeText -match "Failed to start the systemd user session") {
    Write-Host "ERROR: WSL still reports a failed systemd user session."
    Write-Host "Run .\Repair-WSL-Codex-Room.ps1 first."
    return
}

Write-Host ""
Write-Host "=== Provisioning Ubuntu build prerequisites ==="

wsl.exe -u root -- env DEBIAN_FRONTEND=noninteractive apt-get update -o Acquire::ForceIPv4=true -o Acquire::Retries=3
$aptUpdateExit = $LASTEXITCODE
if ($aptUpdateExit -ne 0) {
    Write-Host "ERROR: Ubuntu package-index refresh failed with exit code $aptUpdateExit."
    return
}

wsl.exe -u root -- env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends build-essential pkg-config libssl-dev ca-certificates curl git python3 python3-venv
$aptInstallExit = $LASTEXITCODE
if ($aptInstallExit -ne 0) {
    Write-Host "ERROR: Ubuntu prerequisite installation failed with exit code $aptInstallExit."
    return
}

Write-Host ""
Write-Host "=== Provisioning isolated user toolchains ==="

$toolchainCommand = 'set -eu; export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"; if ! command -v uv >/dev/null 2>&1; then curl -LsSf https://astral.sh/uv/install.sh | sh; fi; export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"; uv python install 3.10 3.11; if ! command -v rustup >/dev/null 2>&1; then curl --proto "=https" --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal --default-toolchain 1.80.0; fi; export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"; rustup toolchain install 1.80.0 --profile minimal; printf "uv: "; uv --version; printf "rustc: "; RUSTUP_TOOLCHAIN=1.80.0 rustc --version; printf "cargo: "; RUSTUP_TOOLCHAIN=1.80.0 cargo --version'

wsl.exe -e bash -lc $toolchainCommand
$toolchainExit = $LASTEXITCODE
if ($toolchainExit -ne 0) {
    Write-Host "ERROR: WSL user-toolchain provisioning failed with exit code $toolchainExit."
    return
}

$repoWslLines = @(wsl.exe wslpath -a -u "$RepoRoot" 2>&1)
$wslPathExit = $LASTEXITCODE
if ($wslPathExit -ne 0) {
    Write-Host "ERROR: Could not resolve the repository path inside WSL."
    $repoWslLines | ForEach-Object { Write-Host $_ }
    return
}

$repoWsl = ($repoWslLines | Select-Object -Last 1).Trim()
if ([string]::IsNullOrWhiteSpace($repoWsl)) {
    Write-Host "ERROR: WSL returned an empty repository path."
    return
}

Write-Host ""
Write-Host "=== Running frozen Phase 3 checks ==="

$phaseCommand = 'set -eu; export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"; cd "' + $repoWsl + '"; python3 benchmarks/oub/v2/validate_phase3_native.py'
wsl.exe -e bash -lc $phaseCommand
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
