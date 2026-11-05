param(
    [string]$Version = "0.1.0"
)

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$appDirectory = Join-Path $projectRoot "dist\YTDISK"
$releaseDirectory = Join-Path $projectRoot "release"
$archive = Join-Path $releaseDirectory "YTDISK-windows-x64-v$Version.zip"

if (-not (Test-Path (Join-Path $appDirectory "YTDISK.exe"))) {
    throw "Application not found. Run .\\build-windows.ps1 first."
}

New-Item -ItemType Directory -Force -Path $releaseDirectory | Out-Null
if (Test-Path $archive) {
    Remove-Item -LiteralPath $archive -Force
}

Compress-Archive -Path (Join-Path $appDirectory "*") -DestinationPath $archive -Force
Write-Host "Release archive created: $archive"
