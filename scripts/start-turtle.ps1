<#
.SYNOPSIS
    Starts TurtleMaxxxing (if it isn't already running) and opens it in your browser.

.DESCRIPTION
    This is what the "I like turtles" Start-menu shortcut runs. It starts the app
    in a small minimized window (close that window to stop the app), waits until
    the app answers, then opens your saved address, e.g. http://turtle.localhost:8765.

    It only ever talks to 127.0.0.1. It changes nothing on your computer.

.PARAMETER Browser
    Which browser to open: default, chrome, edge or firefox. Pick your *personal*
    browser, not the one you use for work.

.PARAMETER NoOpen
    Start the app but don't open a browser (used for testing).
#>
param(
    [ValidateSet('default', 'chrome', 'edge', 'firefox')]
    [string]$Browser = 'default',
    [switch]$NoOpen
)

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $repo 'backend'

# Ask the app for its saved address (settings.json), so this never goes stale.
$settings = & uv run --directory $backend python -c "from turtlemaxxxing import config; s = config.load_settings(); print(s.port); print(s.url)"
if ($LASTEXITCODE -ne 0 -or $settings.Count -lt 2) {
    Write-Error "Couldn't read TurtleMaxxxing's settings. See docs\troubleshooting\app-wont-start.md"
    exit 1
}
$port = $settings[0].Trim()
$url = $settings[1].Trim()

function Test-TurtleRunning {
    try {
        return [bool](Invoke-RestMethod "http://127.0.0.1:$port/api/health" -TimeoutSec 2).ok
    } catch {
        return $false
    }
}

if (-not (Test-TurtleRunning)) {
    $command = "`$host.UI.RawUI.WindowTitle = 'TurtleMaxxxing (close this window to stop)'; " +
               "Set-Location -LiteralPath '$backend'; uv run turtlemaxxxing"
    Start-Process powershell -WindowStyle Minimized -ArgumentList '-NoProfile', '-NoExit', '-Command', $command

    $waited = 0
    while (-not (Test-TurtleRunning) -and $waited -lt 30) {
        Start-Sleep -Milliseconds 500
        $waited += 0.5
    }
    if (-not (Test-TurtleRunning)) {
        Write-Error "TurtleMaxxxing didn't start. Open the minimized TurtleMaxxxing window to see why, or see docs\troubleshooting\app-wont-start.md"
        exit 1
    }
}

if ($NoOpen) {
    Write-Output "TurtleMaxxxing is running at $url"
    exit 0
}

$exe = @{ chrome = 'chrome.exe'; edge = 'msedge.exe'; firefox = 'firefox.exe' }[$Browser]
$path = $null
if ($exe) {
    foreach ($root in 'HKCU:', 'HKLM:') {
        $key = "$root\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\$exe"
        if (Test-Path $key) {
            $path = (Get-ItemProperty $key).'(default)'
            break
        }
    }
}
if ($path) {
    Start-Process -FilePath $path -ArgumentList $url
} else {
    Start-Process $url
}
