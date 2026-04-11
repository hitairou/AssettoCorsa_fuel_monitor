param(
    [string]$Destination = "C:\Program Files (x86)\Steam\steamapps\common\assettocorsa\apps\python\ecoran_fuel_monitor",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$Source = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not (Test-Path -LiteralPath $Source)) {
    throw "Source directory does not exist: $Source"
}

if (-not (Test-Path -LiteralPath $Destination)) {
    New-Item -ItemType Directory -Path $Destination | Out-Null
}

$robocopyArgs = @(
    $Source,
    $Destination,
    "/E",
    "/R:1",
    "/W:1",
    "/XD",
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "logs",
    "/XF",
    "*.pyc",
    "*.pyo",
    "*.log",
    "*.png",
    "*.jpg",
    "*.jpeg",
    "*.bmp",
    "*.local.ini",
    "ui_state.json",
    ".gitignore",
    "README.md",
    "deploy.ps1",
    "/NFL",
    "/NDL",
    "/NP"
)

if ($DryRun) {
    $robocopyArgs += "/L"
}

Write-Host "Deploy source:      $Source"
Write-Host "Deploy destination: $Destination"
if ($DryRun) {
    Write-Host "Dry run: no files will be copied"
}

& robocopy @robocopyArgs
$code = $LASTEXITCODE

if ($code -ge 8) {
    throw "robocopy failed with exit code $code"
}

Write-Host "Deploy completed. robocopy exit code: $code"
exit 0
