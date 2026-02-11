param(
    [switch]$Fast
)

$ErrorActionPreference = "Stop"

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][scriptblock]$Action
    )
    Write-Host "[VERIFY] $Name"
    & $Action
}

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Warning "python not found; skipping checks (non-blocking)."
    exit 0
}

if (Test-Path "scripts/lint.ps1") {
    Invoke-Step -Name "Lint" -Action { & "scripts/lint.ps1" }
} else {
    Write-Warning "scripts/lint.ps1 not found; skipping lint (non-blocking)."
}

if (Test-Path "scripts/typecheck.ps1") {
    Invoke-Step -Name "Typecheck" -Action { & "scripts/typecheck.ps1" }
} else {
    Write-Warning "scripts/typecheck.ps1 not found; skipping typecheck (non-blocking)."
}

if (Test-Path "tests") {
    Invoke-Step -Name "Unit tests" -Action { python -m unittest discover -s tests -p "test_*.py" }
} else {
    Write-Warning "tests/ not found; skipping unit tests (non-blocking)."
}

if (-not $Fast) {
    if (Test-Path "run_scheduled.py") {
        Invoke-Step -Name "Pipeline dry-run" -Action { python run_scheduled.py --no-fetch --no-notify --no-ai --dry-run }
    } else {
        Write-Warning "run_scheduled.py not found; skipping dry-run (non-blocking)."
    }
}

Write-Host "[VERIFY] Complete"
