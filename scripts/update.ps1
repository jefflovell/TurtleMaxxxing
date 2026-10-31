<#
.SYNOPSIS
    Updates TurtleMaxxxing to the latest version. "Update TurtleMaxxxing" in the Start menu runs this.

.DESCRIPTION
    Your data is never touched: it lives in %LOCALAPPDATA%\TurtleMaxxxing, not in the
    install folder. Database changes in a new version run automatically, with a backup first.

    Release installs (from the ZIP):
      1. Asks GitHub for the latest release and downloads its ZIP.
      2. Checks the ZIP against its published SHA-256 fingerprint.
      3. Stops the app, keeps the current version as <install folder>.previous,
         and puts the new version in place.
      4. Installs the new version's parts and runs the tests. If anything fails,
         it puts the previous version back.
      5. Starts the app again.

    Git installs (made with git clone, e.g. by Claude Code): pulls the latest commits,
    rebuilds and re-tests instead.

    The only internet connections are to github.com, when you run this.

.PARAMETER FromZip
    Update from a release ZIP you already downloaded, instead of fetching one.
.PARAMETER FromFolder
    Update from an unzipped release folder (what the installer suggests when you
    run it over an existing install).
.PARAMETER Force
    Reinstall even if this version is already installed.
.PARAMETER Yes
    Don't ask before updating (for automated tests).
.PARAMETER NoStart
    Don't start the app afterwards.
#>
param(
    [string]$FromZip = '',
    [string]$FromFolder = '',
    [switch]$Force,
    [switch]$Yes,
    [switch]$NoStart
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'turtle-common.ps1')
$script:Unattended = [bool]$Yes
$install = Split-Path -Parent $PSScriptRoot
$previous = "$install.previous"
# Don't hold the install folder open while it's being swapped.
Set-Location ([IO.Path]::GetTempPath())

function Stop-Update([string]$Why) {
    Write-Fail $Why
    Write-Host '  Update stopped. Your current version is unchanged.'
    exit 1
}

function Start-Again {
    if ($NoStart) { return }
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $install 'scripts\start-turtle.ps1') -NoOpen | Out-Null
    if ($LASTEXITCODE -eq 0) { Write-Ok 'TurtleMaxxxing is running. Open it with "I like turtles".' }
    else { Write-Warn 'The app didn''t restart by itself. Start it with "I like turtles".' }
}

Write-Host ''
Write-Host '  Update TurtleMaxxxing' -ForegroundColor Green
$current = Get-TurtleVersion $install
Write-Note "Installed: version $current in $(Hide-UserPath $install)"
if (-not (Test-Command 'uv')) { Stop-Update 'uv is missing. Run the installer again, or see docs\INSTALL.md.' }
$settings = Get-TurtleSettings $install
$port = if ($settings) { $settings.Port } else { 8765 }

# ---------------------------------------------------------------- git installs
if (Test-Path (Join-Path $install '.git')) {
    Write-Step 'This is a Git install: updating with git pull'
    if (-not (Test-Command 'git')) { Stop-Update 'Git is missing.' }
    $dirty = & git -C $install status --porcelain
    if ($dirty) { Stop-Update 'There are local changes in the install folder. Commit or undo them first (or ask for help).' }
    if (-not (Read-YesNo 'Update now? The app will restart.' $true)) { exit 0 }
    Stop-Turtle $port | Out-Null
    & git -C $install pull --ff-only
    if ($LASTEXITCODE -ne 0) { Stop-Update 'git pull failed.' }
    & uv sync --locked --directory (Join-Path $install 'backend')
    if (Test-Command 'npm') {
        & npm ci --prefix (Join-Path $install 'frontend')
        & npm run build --prefix (Join-Path $install 'frontend')
    } else {
        Write-Warn 'Node.js isn''t installed, so the screens weren''t rebuilt. Install Node.js, or switch to the release ZIP (docs\INSTALL.md).'
    }
    Write-Step 'Running the self-check'
    if (-not (Invoke-TurtleTests $install)) { Write-Warn 'Some tests failed. Undo with: git -C <install folder> reset --hard ORIG_HEAD'; exit 1 }
    Start-Again
    Write-Ok "Updated to version $(Get-TurtleVersion $install)"
    exit 0
}

# ---------------------------------------------------------------- release installs: get the new version
$work = Join-Path ([IO.Path]::GetTempPath()) ('turtle-update-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force -Path $work | Out-Null
try {
    if ($FromFolder) {
        $newRoot = [IO.Path]::GetFullPath($FromFolder)
    } else {
        if (-not $FromZip) {
            Write-Step 'Checking GitHub for the latest version'
            try {
                $release = Invoke-RestMethod "https://api.github.com/repos/$script:Repo/releases/latest" -Headers @{ 'User-Agent' = 'TurtleMaxxxing-updater' }
            } catch {
                Stop-Update 'Couldn''t reach GitHub, or no release has been published yet.'
            }
            $latest = $release.tag_name.TrimStart('v')
            Write-Note "Latest: version $latest"
            if ($latest -eq $current -and -not $Force) { Write-Ok 'You already have the latest version.'; exit 0 }
            $zipAsset = $release.assets | Where-Object { $_.name -like 'TurtleMaxxxing-*.zip' } | Select-Object -First 1
            $sumAsset = $release.assets | Where-Object { $_.name -eq "$($zipAsset.name).sha256" } | Select-Object -First 1
            if (-not $zipAsset -or -not $sumAsset) { Stop-Update 'That release is missing its ZIP or fingerprint file.' }
            $FromZip = Join-Path $work $zipAsset.name
            Write-Note "Downloading $($zipAsset.name)..."
            Invoke-WebRequest $zipAsset.browser_download_url -OutFile $FromZip -UseBasicParsing
            $expected = ((Invoke-WebRequest $sumAsset.browser_download_url -UseBasicParsing).Content -split '\s+')[0].Trim().ToLower()
            $actual = (Get-FileHash $FromZip -Algorithm SHA256).Hash.ToLower()
            if ($actual -ne $expected) { Stop-Update 'The download doesn''t match its published fingerprint. Not installing it.' }
            Write-Ok 'Download checked against its SHA-256 fingerprint'
        }
        Expand-Archive -Path $FromZip -DestinationPath $work -Force
        $newRoot = Join-Path $work 'TurtleMaxxxing'
    }
    if (-not (Test-Path (Join-Path $newRoot 'backend\turtlemaxxxing'))) { Stop-Update 'That doesn''t look like a TurtleMaxxxing release.' }
    if (-not (Test-Path (Join-Path $newRoot 'frontend\dist\index.html'))) { Stop-Update 'That release is missing its built screens.' }
    $newVersion = Get-TurtleVersion $newRoot
    if ($newVersion -eq $current -and -not $Force) { Write-Ok "Version $current is already installed."; exit 0 }
    if (-not (Read-YesNo "Update from $current to $newVersion now? The app will restart." $true)) { exit 0 }

    # ------------------------------------------------------------ swap, with a way back
    Write-Step "Installing version $newVersion"
    if (-not (Stop-Turtle $port)) { Stop-Update 'Couldn''t stop the running app. Close its window and try again.' }
    if (Test-Path $previous) { Remove-Item -Recurse -Force $previous }
    try {
        Rename-Item -Path $install -NewName (Split-Path -Leaf $previous)
    } catch {
        Start-Again
        Stop-Update 'The install folder is in use. Close any windows or programs open in it, then try again.'
    }
    New-Item -ItemType Directory -Force -Path $install | Out-Null
    & robocopy $newRoot $install /E /NFL /NDL /NJH /NJS /NP /XD .venv node_modules .git | Out-Null

    $ok = $LASTEXITCODE -lt 8
    if ($ok) {
        & uv sync --locked --directory (Join-Path $install 'backend')
        $ok = $LASTEXITCODE -eq 0
    }
    if ($ok) {
        Write-Step 'Running the self-check'
        $ok = Invoke-TurtleTests $install
    }
    if (-not $ok) {
        Write-Warn "Version $newVersion didn't pass its checks. Putting $current back."
        Remove-Item -Recurse -Force $install
        Rename-Item -Path $previous -NewName (Split-Path -Leaf $install)
        Start-Again
        Stop-Update 'Please report this. Your data and your previous version are fine.'
    }
    Start-Again
    Write-Host ''
    Write-Ok "Updated to version $newVersion. Your data is unchanged."
    Write-Note "The previous version is kept in $(Hide-UserPath $previous) until the next update, in case you need it."
} finally {
    Remove-Item -Recurse -Force $work -ErrorAction SilentlyContinue
}
