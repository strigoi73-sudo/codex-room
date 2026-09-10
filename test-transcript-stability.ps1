[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$npx = (Get-Command npx.cmd -ErrorAction Stop).Source
$previousNodePath = $env:NODE_PATH
$previousChannel = $env:ROOM_TEST_CHANNEL
$previousLastRunFile = $env:PLAYWRIGHT_LAST_RUN_OUTPUT_FILE
$previousLocation = Get-Location
$exitCode = 1
$outputPath = Join-Path $PSScriptRoot 'output/playwright/transcript-stability'

try {
    Set-Location -LiteralPath $PSScriptRoot
    if (-not $env:ROOM_TEST_CHANNEL) {
        if (Test-Path -LiteralPath 'C:\Program Files\Google\Chrome\Application\chrome.exe') {
            $env:ROOM_TEST_CHANNEL = 'chrome'
        }
        elseif (
            (Test-Path -LiteralPath 'C:\Program Files\Microsoft\Edge\Application\msedge.exe') -or
            (Test-Path -LiteralPath 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe')
        ) {
            $env:ROOM_TEST_CHANNEL = 'msedge'
        }
        else {
            throw 'The transcript stability test requires installed Chrome or Edge.'
        }
    }

    $packageBin = & $npx --yes --package '@playwright/test' node -p `
        "process.env.PATH.split(require('path').delimiter)[0]"
    if ($LASTEXITCODE -ne 0 -or -not $packageBin) {
        throw 'Could not resolve the temporary Playwright package.'
    }

    $env:NODE_PATH = Split-Path -Parent $packageBin.Trim()
    $env:PLAYWRIGHT_LAST_RUN_OUTPUT_FILE = Join-Path $outputPath '.last-run.json'
    & $npx --yes --package '@playwright/test' playwright test `
        'tests/transcript-stability.spec.js' `
        --workers=1 `
        --reporter=line `
        --output=$outputPath
    $exitCode = $LASTEXITCODE
}
finally {
    $env:NODE_PATH = $previousNodePath
    $env:ROOM_TEST_CHANNEL = $previousChannel
    $env:PLAYWRIGHT_LAST_RUN_OUTPUT_FILE = $previousLastRunFile
    Set-Location -LiteralPath $previousLocation.Path
    if ($exitCode -eq 0 -and (Test-Path -LiteralPath $outputPath)) {
        Remove-Item -LiteralPath $outputPath -Recurse -Force
    }
    foreach ($emptyParent in @(
        (Join-Path $PSScriptRoot 'output/playwright'),
        (Join-Path $PSScriptRoot 'output')
    )) {
        if (
            (Test-Path -LiteralPath $emptyParent -PathType Container) -and
            @(Get-ChildItem -LiteralPath $emptyParent -Force).Count -eq 0
        ) {
            Remove-Item -LiteralPath $emptyParent -Force
        }
    }
}

exit $exitCode
