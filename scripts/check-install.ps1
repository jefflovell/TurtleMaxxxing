<#
.SYNOPSIS
    Checks your TurtleMaxxxing install and makes a short report you can paste into a
    chat when asking for help. "Check my TurtleMaxxxing install" in the Start menu runs this.

.DESCRIPTION
    The report contains NO data from your TurtleMaxxxing database: no accounts, amounts,
    tasks, contacts or labels. Folder paths have your user name replaced with <you>.
    It only reads files and asks the app on 127.0.0.1 whether it's running. It changes
    nothing and connects to nothing on the internet.

.PARAMETER Tests
    Also run the full test suite (takes about half a minute).
.PARAMETER NoClipboard
    Don't copy the report to the clipboard.
#>
param(
    [switch]$Tests,
    [switch]$NoClipboard
)

$ErrorActionPreference = 'Continue'
. (Join-Path $PSScriptRoot 'turtle-common.ps1')
$install = Split-Path -Parent $PSScriptRoot
$lines = New-Object System.Collections.Generic.List[string]
function Add-Line([string]$Label, [string]$Value) { $lines.Add(('{0,-16} {1}' -f ($Label + ':'), (Hide-UserPath $Value))) }

$lines.Add('TurtleMaxxxing install check')
$lines.Add('(No data from the app''s database is included.)')
Add-Line 'Version' (Get-TurtleVersion $install)
Add-Line 'Install type' $(if (Test-Path (Join-Path $install '.git')) { 'Git' } else { 'Release ZIP' })
Add-Line 'Install folder' $install
$risky = Test-RiskyFolder $install
if ($risky) { Add-Line 'WARNING' "install folder is inside $risky (AI tools or sync services may see it)" }
$os = Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue
Add-Line 'Windows' $(if ($os) { "$($os.Caption) $($os.Version)" } else { [Environment]::OSVersion.VersionString })
Add-Line 'PowerShell' $PSVersionTable.PSVersion.ToString()

if (Test-Command 'uv') {
    Add-Line 'uv' ((& uv --version) -join ' ')
    $py = & uv run --directory (Join-Path $install 'backend') python --version 2>&1
    Add-Line 'Python' (($py | Select-Object -Last 1) -as [string])
} else {
    Add-Line 'uv' 'NOT FOUND (needed to run the app)'
}
Add-Line 'Screens built' $(if (Test-Path (Join-Path $install 'frontend\dist\index.html')) { 'yes' } else { 'NO (frontend\dist is missing)' })
Add-Line 'App parts' $(if (Test-Path (Join-Path $install 'backend\.venv')) { 'installed' } else { 'NOT installed (backend\.venv missing)' })

$settings = if (Test-Command 'uv') { Get-TurtleSettings $install } else { $null }
if ($settings) {
    Add-Line 'Address' $settings.Url
    Add-Line 'App running' $(if (Test-TurtleRunning $settings.Port) { 'yes, answering on 127.0.0.1' } else { 'no' })
    $busy = Get-NetTCPConnection -LocalPort $settings.Port -State Listen -ErrorAction SilentlyContinue
    if ($busy -and -not (Test-TurtleRunning $settings.Port)) {
        $name = (Get-Process -Id $busy[0].OwningProcess -ErrorAction SilentlyContinue).ProcessName
        Add-Line 'PORT PROBLEM' "port $($settings.Port) is used by another program ($name)"
    }
} else {
    Add-Line 'Address' 'could not read the settings'
}

$data = if ($env:TURTLE_DATA_DIR) { $env:TURTLE_DATA_DIR } else { Join-Path $env:LOCALAPPDATA 'TurtleMaxxxing' }
Add-Line 'Data folder' $(if (Test-Path $data) { "$data (exists)" } else { "$data (not created yet)" })
$dataRisky = Test-RiskyFolder $data
if ($dataRisky) { Add-Line 'WARNING' "data folder is inside $dataRisky" }
$backups = @(Get-ChildItem (Join-Path $data 'backups') -Filter '*.db' -ErrorAction SilentlyContinue)
Add-Line 'Backups' "$($backups.Count)$(if ($backups) { ', newest ' + ($backups | Sort-Object LastWriteTime | Select-Object -Last 1).LastWriteTime.ToString('yyyy-MM-dd') })"
Add-Line 'Previous version' $(if (Test-Path "$install.previous") { "kept ($(Get-TurtleVersion "$install.previous"))" } else { 'none' })

if ($Tests -and (Test-Command 'uv')) {
    $out = & uv run --directory (Join-Path $install 'backend') pytest -q 2>&1
    Add-Line 'Tests' (($out | Select-Object -Last 1) -as [string])
}

$report = $lines -join "`r`n"
Write-Host ''
Write-Host $report
Write-Host ''
if (-not $NoClipboard) {
    try { Set-Clipboard -Value $report; Write-Host 'Copied to your clipboard. Paste it into your help chat.' -ForegroundColor Green } catch { }
}
Write-Host 'Getting help: see docs\troubleshooting\README.md, or paste this report into a free Claude chat'
Write-Host 'along with the help prompt in docs\HELP_PROMPT.md.'
