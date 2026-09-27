[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ProtocolArguments
)

$ErrorActionPreference = 'Stop'
$RepoRoot = $PSScriptRoot

Push-Location $RepoRoot
try {
    & .\.venv\Scripts\python.exe -m codex_room.oub_v2 @ProtocolArguments
    $pythonExit = $LASTEXITCODE
}
finally {
    Pop-Location
}

if ($pythonExit -ne 0) {
    throw "OUB v2 command failed with exit code $pythonExit"
}
