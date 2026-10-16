$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

$python = Get-Command py -ErrorAction SilentlyContinue
if ($python) {
    & $python.Source -3.12 -m venv work\.venv
} else {
    $python = Get-Command python -ErrorAction Stop
    & $python.Source -m venv work\.venv
}

& work\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt

$pnpm = Get-Command pnpm -ErrorAction SilentlyContinue
if ($pnpm) {
    & $pnpm.Source --dir frontend install
} else {
    $corepack = Get-Command corepack -ErrorAction Stop
    & $corepack.Source pnpm --dir frontend install
}

Write-Host "EvalAI setup is complete." -ForegroundColor Green
Write-Host "In VS Code, press Ctrl+Shift+B to start the website."

