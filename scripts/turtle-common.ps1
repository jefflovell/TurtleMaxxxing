<#
    Shared helpers for setup.ps1, update.ps1 and check-install.ps1.
    Dot-source it:  . (Join-Path $PSScriptRoot 'turtle-common.ps1')

    Plain ASCII on purpose: Windows PowerShell 5.1 misreads other characters
    in scripts saved without a byte-order mark.
#>

$script:Unattended = $false   # set by callers run with -Yes: take every default, ask nothing
$script:Repo = 'jefflovell/TurtleMaxxxing'

function Write-Step([string]$Text) { Write-Host ''; Write-Host "== $Text" -ForegroundColor Cyan }
function Write-Ok([string]$Text) { Write-Host "  [ok] $Text" -ForegroundColor Green }
function Write-Note([string]$Text) { Write-Host "  $Text" }
function Write-Warn([string]$Text) { Write-Host "  [!] $Text" -ForegroundColor Yellow }
function Write-Fail([string]$Text) { Write-Host "  [x] $Text" -ForegroundColor Red }

function Read-YesNo([string]$Question, [bool]$Default = $true) {
    if ($script:Unattended) { return $Default }
    $hint = if ($Default) { '[Y/n]' } else { '[y/N]' }
    while ($true) {
        $answer = "$(Read-Host "  $Question $hint")".Trim().ToLower()
        if ($answer -eq '') { return $Default }
        if ($answer -in 'y', 'yes') { return $true }
        if ($answer -in 'n', 'no') { return $false }
    }
}

function Read-Choice([string]$Question, [string]$Default) {
    if ($script:Unattended) { return $Default }
    $answer = "$(Read-Host "  $Question [$Default]")".Trim()
    if ($answer) { return $answer } else { return $Default }
}

function Update-SessionPath {
    $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' +
                [Environment]::GetEnvironmentVariable('Path', 'User')
}

function Test-Command([string]$Name) { return [bool](Get-Command $Name -ErrorAction SilentlyContinue) }

function Get-TurtleVersion([string]$InstallDir) {
    $file = Join-Path $InstallDir 'VERSION'
    if (Test-Path $file) { return (Get-Content $file -Raw).Trim() }
    $init = Join-Path $InstallDir 'backend\turtlemaxxxing\__init__.py'
    if (Test-Path $init) {
        $m = Select-String -Path $init -Pattern '__version__\s*=\s*"([^"]+)"'
        if ($m) { return $m.Matches[0].Groups[1].Value }
    }
    return 'unknown'
}

function Get-TurtleSettings([string]$InstallDir) {
    $backend = Join-Path $InstallDir 'backend'
    $out = & uv run --directory $backend python -c "from turtlemaxxxing import config; s = config.load_settings(); print(s.port); print(s.url)"
    if ($LASTEXITCODE -ne 0 -or $out.Count -lt 2) { return $null }
    return @{ Port = [int]$out[0].Trim(); Url = $out[1].Trim() }
}

function Test-TurtleRunning([int]$Port) {
    try { return [bool](Invoke-RestMethod "http://127.0.0.1:$Port/api/health" -TimeoutSec 2).ok } catch { return $false }
}

function Stop-Turtle([int]$Port) {
    # Stops whatever is serving TurtleMaxxxing on this port (the app's Python and the uv that started it).
    $conns = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    foreach ($c in $conns) {
        $proc = Get-CimInstance Win32_Process -Filter "ProcessId = $($c.OwningProcess)" -ErrorAction SilentlyContinue
        Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue
        if ($proc -and $proc.ParentProcessId) {
            $parent = Get-Process -Id $proc.ParentProcessId -ErrorAction SilentlyContinue
            if ($parent -and $parent.ProcessName -eq 'uv') { Stop-Process -Id $parent.Id -Force -ErrorAction SilentlyContinue }
        }
    }
    $waited = 0
    while ((Test-TurtleRunning $Port) -and $waited -lt 10) { Start-Sleep -Milliseconds 500; $waited += 0.5 }
    return -not (Test-TurtleRunning $Port)
}

function Get-Browsers {
    # Browsers Windows knows about, by the name start-turtle.ps1 uses.
    $found = [ordered]@{}
    foreach ($pair in @(@('chrome', 'chrome.exe'), @('edge', 'msedge.exe'), @('firefox', 'firefox.exe'))) {
        foreach ($root in 'HKCU:', 'HKLM:') {
            $key = "$root\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\$($pair[1])"
            if (Test-Path $key) { $found[$pair[0]] = (Get-ItemProperty $key).'(default)'; break }
        }
    }
    return $found
}

function Test-RiskyFolder([string]$Path) {
    # Folders that AI tools, sync services or work files often share. The app shouldn't live there.
    $full = [IO.Path]::GetFullPath($Path).TrimEnd('\') + '\'
    $risky = @(
        [Environment]::GetFolderPath('MyDocuments'), [Environment]::GetFolderPath('Desktop'),
        (Join-Path $env:USERPROFILE 'Downloads'), $env:OneDrive, $env:OneDriveCommercial, $env:OneDriveConsumer
    ) | Where-Object { $_ }
    foreach ($r in $risky) {
        if ($full.StartsWith(([IO.Path]::GetFullPath($r).TrimEnd('\') + '\'), [StringComparison]::OrdinalIgnoreCase)) { return $r }
    }
    return $null
}

function Invoke-TurtleTests([string]$InstallDir) {
    # The privacy and security tests run first, on their own, so their result is easy to see.
    $backend = Join-Path $InstallDir 'backend'
    Write-Note 'Privacy and security tests (no internet connections; other websites can not reach your data)...'
    $privacy = & uv run --directory $backend pytest -q tests/test_privacy.py tests/test_local_security.py 2>&1
    $privacyOk = $LASTEXITCODE -eq 0
    Write-Note ("  " + ($privacy | Select-Object -Last 1))
    Write-Note 'All tests...'
    $all = & uv run --directory $backend pytest -q 2>&1
    $allOk = $LASTEXITCODE -eq 0
    Write-Note ("  " + ($all | Select-Object -Last 1))
    if (-not ($privacyOk -and $allOk)) { $all | Select-Object -Last 30 | ForEach-Object { Write-Host "    $_" } }
    return ($privacyOk -and $allOk)
}

function New-TurtleShortcuts([string]$InstallDir, [string]$Browser, [string]$StartMenu) {
    # "I like turtles" starts the app; a TurtleMaxxxing folder holds Update and Check.
    $ps = (Get-Command powershell.exe).Source
    $shell = New-Object -ComObject WScript.Shell
    $folder = Join-Path $StartMenu 'TurtleMaxxxing'
    New-Item -ItemType Directory -Force -Path $folder | Out-Null
    $items = @(
        @{ Path = (Join-Path $StartMenu 'I like turtles.lnk'); Script = 'start-turtle.ps1'; Args = "-Browser $Browser"; Style = 'Hidden'; Desc = 'Start TurtleMaxxxing' },
        @{ Path = (Join-Path $folder 'Update TurtleMaxxxing.lnk'); Script = 'update.ps1'; Args = ''; Style = 'Normal'; Desc = 'Update TurtleMaxxxing to the latest version' },
        @{ Path = (Join-Path $folder 'Check my TurtleMaxxxing install.lnk'); Script = 'check-install.ps1'; Args = ''; Style = 'Normal'; Desc = 'Make a privacy-safe report for getting help' }
    )
    foreach ($i in $items) {
        $s = $shell.CreateShortcut($i.Path)
        $s.TargetPath = $ps
        $keep = if ($i.Style -eq 'Normal') { '-NoExit ' } else { '' }
        $s.Arguments = "-NoProfile $keep-ExecutionPolicy Bypass -WindowStyle $($i.Style) -File `"$InstallDir\scripts\$($i.Script)`" $($i.Args)".Trim()
        $s.WorkingDirectory = $InstallDir
        $s.IconLocation = "$InstallDir\assets\turtle.ico"
        $s.Description = $i.Desc
        $s.Save()
    }
}

function Hide-UserPath([string]$Text) {
    # For reports people paste into chats: never include their user name.
    if (-not $Text) { return $Text }
    # LOCALAPPDATA sits inside USERPROFILE, so it's replaced first.
    $out = $Text
    if ($env:LOCALAPPDATA) { $out = $out.Replace($env:LOCALAPPDATA, '%LOCALAPPDATA%') }
    $out = $out.Replace($env:USERPROFILE, '%USERPROFILE%')
    if ($env:USERNAME) { $out = $out -replace [regex]::Escape($env:USERNAME), '<you>' }
    return $out
}
