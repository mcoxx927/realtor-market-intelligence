param()

$ErrorActionPreference = "Stop"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Warning "python not found; cannot run typecheck."
    exit 1
}

python -c "import importlib.util,sys; sys.exit(0 if importlib.util.find_spec('mypy') else 1)"
if ($LASTEXITCODE -ne 0) {
    Write-Warning "mypy is not installed; skipping typecheck (non-blocking). Install with: pip install -r requirements-dev.txt"
    exit 0
}

python -m mypy market_radar/distressed_fit tests --ignore-missing-imports --allow-untyped-defs --allow-incomplete-defs
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
