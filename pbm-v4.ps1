[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$PBMArguments
)

$ErrorActionPreference = 'Stop'

$RepoRoot = $PSScriptRoot
$Python = Join-Path $RepoRoot '.venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Codex Room Python environment not found: $Python"
}

$pbmExit = $null

Push-Location $RepoRoot
try {
    & $Python -m codex_room.pbm_v4 @PBMArguments
    $pbmExit = $LASTEXITCODE
}
finally {
    Pop-Location
}

if ($pbmExit -ne 0) {
    throw "PBM v4 command failed with exit code $pbmExit"
}
