[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ProtocolArguments
)

$ErrorActionPreference = 'Stop'

$RepoRoot = $PSScriptRoot
$Python = Join-Path $RepoRoot '.venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Codex Room Python environment not found: $Python"
}

$protocolExit = $null

Push-Location $RepoRoot
try {
    & $Python -m codex_room.pbm_v4_protocol @ProtocolArguments
    $protocolExit = $LASTEXITCODE
}
finally {
    Pop-Location
}

if ($protocolExit -ne 0) {
    throw "PBM v4 protocol command failed with exit code $protocolExit"
}
