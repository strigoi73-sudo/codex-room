[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ProtocolArguments
)

$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
$Protocol = Join-Path $RepoRoot 'pbm-v4-protocol.ps1'

if (-not (Test-Path -LiteralPath $Protocol)) {
    throw "PBM v4 protocol wrapper not found: $Protocol"
}

$protocolExit = $null

Push-Location $PSScriptRoot
try {
    & $Protocol @ProtocolArguments
    $protocolExit = $LASTEXITCODE
}
finally {
    Pop-Location
}

if ($protocolExit -ne 0) {
    throw "PBM v4 Desktop protocol command failed with exit code $protocolExit"
}
