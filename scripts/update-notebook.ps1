param(
    [switch]$SkipInstall,
    [switch]$SkipBuild,
    [switch]$SkipMigrate
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$python = Resolve-Path ".\.venv\Scripts\python.exe"

Write-Host "Pulling latest changes from origin/main..."
git pull --ff-only origin main

if (-not $SkipInstall) {
    Write-Host "Syncing Python dependencies..."
    & $python -m pip install -r .\requirements.txt

    Write-Host "Syncing Node dependencies..."
    npm install
}

if (-not $SkipBuild) {
    Write-Host "Rebuilding frontend assets..."
    npm run build
}

if (-not $SkipMigrate) {
    Write-Host "Applying Django migrations..."
    & $python .\manage.py migrate
}

Write-Host ""
Write-Host "Notebook update complete."
