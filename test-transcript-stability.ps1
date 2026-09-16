[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$node = (Get-Command node.exe -ErrorAction Stop).Source
$npm = (Get-Command npm.cmd -ErrorAction Stop).Source
$playwrightVersion = "1.63.0"
$playwrightPackage = "@playwright/test@$playwrightVersion"

$toolCacheRoot = if ($env:RUNNER_TOOL_CACHE) {
    $env:RUNNER_TOOL_CACHE
}
else {
    Join-Path ([System.IO.Path]::GetTempPath()) "codex-room-tool-cache"
}

$toolRoot = Join-Path $toolCacheRoot "codex-room-playwright/$playwrightVersion"
$nodeModules = Join-Path $toolRoot "node_modules"
$packageJson = Join-Path $nodeModules "@playwright/test/package.json"
$playwrightCli = Join-Path $nodeModules "@playwright/test/cli.js"

$previousNodePath = $env:NODE_PATH
$previousChannel = $env:ROOM_TEST_CHANNEL
$previousLastRunFile = $env:PLAYWRIGHT_LAST_RUN_OUTPUT_FILE
$previousSkipBrowserDownload = $env:PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD
$previousLocation = Get-Location
$exitCode = 1
$outputPath = Join-Path $PSScriptRoot "output/playwright/transcript-stability"

try {
    Set-Location -LiteralPath $PSScriptRoot

    if (-not $env:ROOM_TEST_CHANNEL) {
        if (Test-Path -LiteralPath "C:\Program Files\Google\Chrome\Application\chrome.exe") {
            $env:ROOM_TEST_CHANNEL = "chrome"
        }
        elseif (
            (Test-Path -LiteralPath "C:\Program Files\Microsoft\Edge\Application\msedge.exe") -or
            (Test-Path -LiteralPath "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
        ) {
            $env:ROOM_TEST_CHANNEL = "msedge"
        }
        else {
            throw "The transcript stability test requires installed Chrome or Edge."
        }
    }

    $installedVersion = $null
    if (Test-Path -LiteralPath $packageJson -PathType Leaf) {
        try {
            $installedVersion = (Get-Content -LiteralPath $packageJson -Raw | ConvertFrom-Json).version
        }
        catch {
            $installedVersion = $null
        }
    }

    if ($installedVersion -ne $playwrightVersion -or -not (Test-Path -LiteralPath $playwrightCli -PathType Leaf)) {
        New-Item -ItemType Directory -Path $toolRoot -Force | Out-Null
        $env:PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD = "1"

        $npmArgs = @(
            "install",
            "--prefix", $toolRoot,
            "--no-save",
            "--no-package-lock",
            "--ignore-scripts",
            $playwrightPackage
        )
        & $npm @npmArgs

        if ($LASTEXITCODE -ne 0) {
            throw "Could not install pinned Playwright package $playwrightPackage."
        }
    }

    if (-not (Test-Path -LiteralPath $playwrightCli -PathType Leaf)) {
        throw "Pinned Playwright CLI was not found at $playwrightCli."
    }

    $env:NODE_PATH = $nodeModules
    $env:PLAYWRIGHT_LAST_RUN_OUTPUT_FILE = Join-Path $outputPath ".last-run.json"

    $playwrightArgs = @(
        $playwrightCli,
        "test",
        "tests/transcript-stability.spec.js",
        "--workers=1",
        "--reporter=line",
        "--output=$outputPath"
    )
    & $node @playwrightArgs
    $exitCode = $LASTEXITCODE
}
finally {
    $env:NODE_PATH = $previousNodePath
    $env:ROOM_TEST_CHANNEL = $previousChannel
    $env:PLAYWRIGHT_LAST_RUN_OUTPUT_FILE = $previousLastRunFile
    $env:PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD = $previousSkipBrowserDownload
    Set-Location -LiteralPath $previousLocation.Path

    if ($exitCode -eq 0 -and (Test-Path -LiteralPath $outputPath)) {
        Remove-Item -LiteralPath $outputPath -Recurse -Force
    }

    foreach ($emptyParent in @(
        (Join-Path $PSScriptRoot "output/playwright"),
        (Join-Path $PSScriptRoot "output")
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
