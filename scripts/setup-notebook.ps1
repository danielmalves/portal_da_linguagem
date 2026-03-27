param(
    [switch]$SkipMigrate,
    [switch]$SkipWiki
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
}

$python = Resolve-Path ".\.venv\Scripts\python.exe"

Write-Host "Installing Python dependencies..."
& $python -m pip install --upgrade pip
& $python -m pip install -r .\requirements.txt

Write-Host "Installing Node dependencies..."
npm install

Write-Host "Building frontend assets..."
npm run build

if (-not $SkipMigrate) {
    Write-Host "Applying Django migrations..."
    & $python .\manage.py migrate
}

if ((-not $SkipWiki) -and (Test-Path ".\tools\build_country_wiki.py")) {
    Write-Host "Refreshing cached mini wiki data..."
    & $python .\tools\build_country_wiki.py
}

Write-Host ""
Write-Host "Notebook setup complete."
Write-Host "Next:"
Write-Host "  .\scripts\start-dev.ps1"
