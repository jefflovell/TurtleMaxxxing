<#
.SYNOPSIS
    Installs TurtleMaxxxing. Double-click "Install TurtleMaxxxing.cmd" to run it.

.DESCRIPTION
    Does what docs/SETUP_PROMPT.md asks Claude Code to do, without needing Claude:
      1. Checks for uv (the one tool the app needs) and offers to install it.
      2. Copies the app into its own folder (default: %USERPROFILE%\Apps\TurtleMaxxxing).
      3. Installs its parts and runs the privacy and security tests.
      4. Picks a free local port and your friendly address.
      5. Adds Start-menu shortcuts: "I like turtles", plus Update and Check.
      6. Starts the app in your personal browser.

    Guardrails: it asks before installing anything, never needs administrator rights,
    never asks for passwords, changes no system settings, and only writes to the install
    folder, the Start menu and the app's data folder (%LOCALAPPDATA%\TurtleMaxxxing).

.PARAMETER InstallDir
    Where to install. Default: %USERPROFILE%\Apps\TurtleMaxxxing.
.PARAMETER Browser
    default, chrome, edge or firefox. Asked if not given.
.PARAMETER Hostname
    The friendly address, ending in .localhost. Asked if not given.
.PARAMETER StartMenu
    Where shortcuts go. Default: your Start menu's Programs folder.
.PARAMETER Yes
    Accept every default without asking (for automated tests).
.PARAMETER NoStart
    Don't start the app at the end.
#>
param(
    [string]$InstallDir = (Join-Path $env:USERPROFILE 'Apps\TurtleMaxxxing'),
    [ValidateSet('', 'default', 'chrome', 'edge', 'firefox')]
    [string]$Browser = '',
    [string]$Hostname = '',
    [string]$StartMenu = [Environment]::GetFolderPath('Programs'),
    [switch]$Yes,
    [switch]$NoStart
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'turtle-common.ps1')
$script:Unattended = [bool]$Yes
$source = Split-Path -Parent $PSScriptRoot

function Stop-Setup([string]$Why) {
    Write-Fail $Why
    Write-Host ''
    Write-Host '  Setup stopped. Nothing outside the install folder was changed.'
    Write-Host '  For help, see docs\INSTALL.md (in the folder you unzipped).'
    exit 1
}

Write-Host ''
Write-Host '  TurtleMaxxxing setup  (I like turtles)' -ForegroundColor Green
Write-Host '  A local-first assistant. Your data stays on this computer.'
Write-Host '  Use this on your PERSONAL computer only, never a work computer.'

# ---------------------------------------------------------------- 1. folder
Write-Step 'Install folder'
if (-not $Yes) { $InstallDir = Read-Choice 'Install TurtleMaxxxing in' $InstallDir }
$InstallDir = [IO.Path]::GetFullPath($InstallDir)
$risky = Test-RiskyFolder $InstallDir
if ($risky) {
    Write-Warn "That's inside $(Hide-UserPath $risky), which AI tools or sync services may be able to see."
    if (-not (Read-YesNo 'Install there anyway?' $false)) { Stop-Setup 'Pick a folder outside Documents, Desktop, Downloads and OneDrive.' }
}
$sameFolder = [IO.Path]::GetFullPath($source).TrimEnd('\') -ieq $InstallDir.TrimEnd('\')
if (-not $sameFolder -and (Test-Path $InstallDir) -and (Get-ChildItem $InstallDir -Force | Select-Object -First 1)) {
    if (Test-Path (Join-Path $InstallDir 'backend\turtlemaxxxing')) {
        Write-Warn "TurtleMaxxxing is already installed there (version $(Get-TurtleVersion $InstallDir))."
        Write-Note 'To move to this version, use "Update TurtleMaxxxing" in the Start menu, or run:'
        Write-Note "  powershell -ExecutionPolicy Bypass -File `"$InstallDir\scripts\update.ps1`" -FromFolder `"$source`""
        exit 0
    }
    Stop-Setup "$InstallDir already has other files in it. Pick an empty or new folder."
}
Write-Ok (Hide-UserPath $InstallDir)

# ---------------------------------------------------------------- 2. uv
Write-Step 'Checking for uv (installs Python and the app''s parts for you)'
if (-not (Test-Command 'uv')) {
    Write-Note 'uv is a free, open-source tool from Astral that sets up Python for the app.'
    if (-not (Test-Command 'winget')) { Stop-Setup 'uv is missing and Windows'' winget is not available. Install uv by hand (docs\INSTALL.md, "Install uv yourself"), then run setup again.' }
    if (-not (Read-YesNo 'Install uv now with winget?' $true)) { Stop-Setup 'uv is needed. Install it by hand (docs\INSTALL.md), then run setup again.' }
    & winget install --id astral-sh.uv -e --source winget --accept-package-agreements --accept-source-agreements
    Update-SessionPath
    if (-not (Test-Command 'uv')) { Stop-Setup 'uv was installed but this window can''t see it yet. Close this window and run setup again.' }
}
Write-Ok ((& uv --version) -join ' ')

# ---------------------------------------------------------------- 3. copy
if (-not $sameFolder) {
    Write-Step 'Copying the app'
    New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
    & robocopy $source $InstallDir /E /NFL /NDL /NJH /NJS /NP /XD .venv node_modules .git bundle-out | Out-Null
    if ($LASTEXITCODE -ge 8) { Stop-Setup "Copying failed (robocopy code $LASTEXITCODE)." }
    Write-Ok "Version $(Get-TurtleVersion $InstallDir)"
}

# ---------------------------------------------------------------- 4. install and test
Write-Step 'Installing the app''s parts (a minute or two the first time)'
if (-not (Test-Path (Join-Path $InstallDir 'frontend\dist\index.html'))) {
    # Release ZIPs come with the screens built. A plain Git copy needs Node.js to build them.
    if (-not (Test-Command 'npm')) { Stop-Setup 'The screens aren''t built and Node.js isn''t installed. Download the release ZIP instead (it has them built), see docs\INSTALL.md.' }
    & npm ci --prefix (Join-Path $InstallDir 'frontend')
    & npm run build --prefix (Join-Path $InstallDir 'frontend')
    if ($LASTEXITCODE -ne 0) { Stop-Setup 'Building the screens failed.' }
}
& uv sync --locked --directory (Join-Path $InstallDir 'backend')
if ($LASTEXITCODE -ne 0) { Stop-Setup 'Installing the app''s parts failed. Check your internet connection and run setup again.' }
Write-Ok 'Installed'

Write-Step 'Running the self-check'
if (-not (Invoke-TurtleTests $InstallDir)) { Stop-Setup 'Some tests failed (shown above). Please report this; don''t use the app until it''s fixed.' }
Write-Ok 'All tests passed, including the privacy tests'

# ---------------------------------------------------------------- 5. address
Write-Step 'Your address'
$backend = Join-Path $InstallDir 'backend'
$hasSettings = (& uv run --directory $backend python -c "from turtlemaxxxing import config; print(config.settings_path().exists())").Trim() -eq 'True'
if (-not $hasSettings) {
    & uv run --directory $backend turtlemaxxxing --find-port | Out-Null
    if ($LASTEXITCODE -ne 0) { Stop-Setup 'Couldn''t find a free local port.' }
    if (-not $Hostname -and -not $Yes) {
        Write-Note 'What would you like to type to reach the app? It must end in .localhost, which keeps it on this computer.'
        Write-Note 'For example: turtle.localhost or i-like-turtles.localhost'
        $Hostname = Read-Choice 'Address name' 'turtle.localhost'
    }
    while ($Hostname -and $Hostname -ne 'turtle.localhost') {
        & uv run --directory $backend turtlemaxxxing --hostname $Hostname | Out-Null
        if ($LASTEXITCODE -eq 0) { break }
        Write-Warn "That name won't work. Use letters, numbers and dashes, ending in .localhost."
        if ($Yes) { Stop-Setup "Invalid -Hostname $Hostname" }
        $Hostname = Read-Choice 'Address name' 'turtle.localhost'
    }
} else {
    Write-Note 'Keeping your existing address settings.'
}
$settings = Get-TurtleSettings $InstallDir
if (-not $settings) { Stop-Setup 'Couldn''t read the address settings.' }
Write-Ok $settings.Url

# ---------------------------------------------------------------- 6. shortcuts
Write-Step 'Start-menu shortcuts'
if (-not $Browser) {
    $found = Get-Browsers
    Write-Note 'Which browser do you use for PERSONAL things? (Not the one you use for work.)'
    Write-Note ('Found: ' + (@('default') + @($found.Keys) -join ', '))
    $Browser = Read-Choice 'Browser' 'default'
    if ($Browser -notin @('default') + @($found.Keys)) { Write-Warn "Didn't recognize '$Browser'; using your default browser."; $Browser = 'default' }
}
New-TurtleShortcuts $InstallDir $Browser $StartMenu
Write-Ok '"I like turtles" (start), plus "Update TurtleMaxxxing" and "Check my TurtleMaxxxing install"'
Write-Note 'Press the Windows key and type: I like turtles'

# ---------------------------------------------------------------- 7. start
if (-not $NoStart) {
    Write-Step 'Starting TurtleMaxxxing'
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $InstallDir 'scripts\start-turtle.ps1') -Browser $Browser
    if ($LASTEXITCODE -ne 0) { Stop-Setup 'The app didn''t start. Run "Check my TurtleMaxxxing install" from the Start menu.' }
    Write-Ok 'Running. Close the minimized TurtleMaxxxing window to stop it.'
}

Write-Host ''
Write-Host '  All done!' -ForegroundColor Green
Write-Note "Installed in:  $(Hide-UserPath $InstallDir)"
Write-Note "Address:       $($settings.Url)  (bookmark it as: I like turtles)"
$dataDir = (& uv run --directory $backend python -c "from turtlemaxxxing import config; print(config.data_dir())").Trim()
Write-Note "Your data:     $(Hide-UserPath $dataDir)  (this computer only)"
Write-Note 'Next: read docs\SECURITY.md (5 minutes) and try the separation test (docs\testing\SEPARATION_TEST.md).'
