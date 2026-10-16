$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$frontend = Join-Path $projectRoot "frontend"

# VS Code may inherit a PATH that contains pnpm but not Node.js. Prefer the
# user's Node installation, then fall back to the Node runtime bundled with
# Codex on this machine.
$node = Get-Command node -ErrorAction SilentlyContinue
if (-not $node) {
    $codexNodeDirectory = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin"
    $codexNode = Join-Path $codexNodeDirectory "node.exe"
    if (Test-Path -LiteralPath $codexNode) {
        $env:Path = "$codexNodeDirectory;$env:Path"
        $node = Get-Command node -ErrorAction SilentlyContinue
    }
}

if (-not $node) {
    Write-Error "Node.js was not found. Install the Node.js LTS release, restart VS Code, and try again."
}

$pnpm = Get-Command pnpm -ErrorAction SilentlyContinue
if ($pnpm) {
    & $pnpm.Source --dir $frontend dev
    exit $LASTEXITCODE
}

$corepack = Get-Command corepack -ErrorAction SilentlyContinue
if ($corepack) {
    & $corepack.Source pnpm --dir $frontend dev
    exit $LASTEXITCODE
}

$codexPnpm = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\bin\fallback\pnpm.cmd"
if (Test-Path -LiteralPath $codexPnpm) {
    & $codexPnpm --dir $frontend dev
    exit $LASTEXITCODE
}

Write-Error "pnpm was not found. Install Node.js, then run: corepack enable"

