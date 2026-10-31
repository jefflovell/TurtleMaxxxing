<#
.SYNOPSIS
    Builds the release ZIP: the app's files plus its screens already built,
    so installing needs no Node.js and no Git.

.DESCRIPTION
    Used by .github/workflows/release.yml and the installer test in CI.
    Packs the files committed at HEAD (via git archive, so nothing private or
    local like .venv, node_modules or a data folder can sneak in), adds the
    freshly built frontend/dist and a VERSION file, then writes:

        <OutDir>\TurtleMaxxxing-<version>.zip
        <OutDir>\TurtleMaxxxing-<version>.zip.sha256

    Needs git, Node.js and uv (it's a build machine, not a user's computer).

.PARAMETER OutDir
    Where to write the ZIP. Default: bundle-out in the repo (ignored by git).
.PARAMETER WorkingTree
    For testing uncommitted changes locally: pack the current files instead of HEAD
    (still only files git tracks or would track, so .gitignore'd things stay out).
    Releases and CI never use this.
#>
param(
    [string]$OutDir = (Join-Path (Split-Path -Parent $PSScriptRoot) 'bundle-out'),
    [switch]$WorkingTree
)

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot

$version = (& uv run --directory (Join-Path $repo 'backend') python -c "import turtlemaxxxing; print(turtlemaxxxing.__version__)").Trim()
if ($LASTEXITCODE -ne 0 -or -not $version) { throw "Couldn't read the app version." }
Write-Output "Building TurtleMaxxxing $version"

& npm ci --prefix (Join-Path $repo 'frontend')
if ($LASTEXITCODE -ne 0) { throw 'npm ci failed' }
& npm run build --prefix (Join-Path $repo 'frontend')
if ($LASTEXITCODE -ne 0) { throw 'frontend build failed' }

$stage = Join-Path ([IO.Path]::GetTempPath()) ("turtle-bundle-" + [guid]::NewGuid().ToString('N'))
$root = Join-Path $stage 'TurtleMaxxxing'
New-Item -ItemType Directory -Force -Path $root | Out-Null
try {
    if ($WorkingTree) {
        $files = & git -C $repo ls-files --cached --others --exclude-standard
        foreach ($f in $files) {
            $from = Join-Path $repo $f
            if (-not (Test-Path -LiteralPath $from -PathType Leaf)) { continue }  # deleted but not yet committed
            $to = Join-Path $root $f
            New-Item -ItemType Directory -Force -Path (Split-Path -Parent $to) | Out-Null
            Copy-Item -LiteralPath $from -Destination $to
        }
    } else {
        # Committed files only.
        $tar = Join-Path $stage 'src.tar'
        & git -C $repo archive --format=tar -o $tar HEAD
        if ($LASTEXITCODE -ne 0) { throw 'git archive failed' }
        & tar -xf $tar -C $root
        if ($LASTEXITCODE -ne 0) { throw 'unpacking the archive failed' }
        Remove-Item $tar
    }

    Copy-Item -Recurse (Join-Path $repo 'frontend\dist') (Join-Path $root 'frontend\dist')
    Set-Content -Path (Join-Path $root 'VERSION') -Value $version -Encoding ascii -NoNewline

    New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
    $zip = Join-Path $OutDir "TurtleMaxxxing-$version.zip"
    if (Test-Path $zip) { Remove-Item $zip }
    Compress-Archive -Path $root -DestinationPath $zip
    $hash = (Get-FileHash $zip -Algorithm SHA256).Hash.ToLower()
    Set-Content -Path "$zip.sha256" -Value "$hash  TurtleMaxxxing-$version.zip" -Encoding ascii
    Write-Output "Wrote $zip"
    Write-Output "SHA-256 $hash"
} finally {
    Remove-Item -Recurse -Force $stage -ErrorAction SilentlyContinue
}
