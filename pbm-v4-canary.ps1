[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$CanaryArguments
)

$ErrorActionPreference = 'Stop'

$RepoRoot = $PSScriptRoot
$Python = Join-Path $RepoRoot '.venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Codex Room Python environment not found: $Python"
}

$canaryExit = $null

Push-Location $RepoRoot
try {
    & $Python -m codex_room.pbm_v4_canary @CanaryArguments
    $canaryExit = $LASTEXITCODE
}
finally {
    Pop-Location
}

if ($canaryExit -ne 0) {
    throw "PBM v4 canary command failed with exit code $canaryExit"
}
