param()

$ErrorActionPreference = "Stop"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Warning "python not found; cannot run lint."
    exit 1
}

# Keep lint strict on runtime-breaking issues without forcing a style refactor.
python -m ruff check . --select E9,F63,F7,F82 --exclude core_markets,market_radar/outputs,market_radar/outputs_distressed_fit
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
