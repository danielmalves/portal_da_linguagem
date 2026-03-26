$appsPath = ".\myproject\apps"

Get-ChildItem $appsPath -Directory | ForEach-Object {
    $appDir = $_.FullName
    $migrationsDir = Join-Path $appDir "migrations"
    $initFile = Join-Path $migrationsDir "__init__.py"

    # Create migrations folder if missing
    if (-not (Test-Path $migrationsDir)) {
        New-Item -ItemType Directory -Path $migrationsDir | Out-Null
        Write-Host "Created folder: $migrationsDir"
    }

    # Create __init__.py if missing
    if (-not (Test-Path $initFile)) {
        New-Item -ItemType File -Path $initFile | Out-Null
        Write-Host "Created file: $initFile"
    }
}
