[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ProtocolArguments
)

$ErrorActionPreference = 'Stop'
$RepoRoot = $PSScriptRoot

Push-Location $RepoRoot
try {
    & .\.venv\Scripts\python.exe -m codex_room.pbm_v5_c_only @ProtocolArguments
    $pythonExit = $LASTEXITCODE
}
finally {
    Pop-Location
}

if ($pythonExit -ne 0) {
    throw "PBM v5 C-only command failed with exit code $pythonExit"
}
