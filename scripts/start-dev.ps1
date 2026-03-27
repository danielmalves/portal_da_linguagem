$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$python = Resolve-Path ".\.venv\Scripts\python.exe"

Write-Host "Checks..."
& $python .\manage.py check

Write-Host "Serving Django at http://127.0.0.1:8000 ..."
& $python .\manage.py runserver
