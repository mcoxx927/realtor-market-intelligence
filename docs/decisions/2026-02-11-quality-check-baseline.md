# Decision Record - Quality Check Baseline

## Context
The repo needed standardized lint/typecheck commands and a clear answer on whether a build step exists.

## Decision
- Standard lint command: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/lint.ps1`
- Standard typecheck command: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/typecheck.ps1`
- Build command: not required (`N/A`) for now because this is a script pipeline repo with no package/binary artifact.

## Alternatives Considered
- Option A: Add strict lint/typecheck gates immediately across the entire codebase.
- Option B: Keep minimal correctness-focused lint/typecheck and tighten later.

## Consequences
- Positive:
  - Repeatable checks are now explicit and wired into `scripts/verify.ps1`.
  - Pre-commit guardrail picks up lint/typecheck automatically via verify fast mode.
  - Avoids forcing broad refactors just to pass style rules.
- Negative:
  - Typecheck is non-blocking when `mypy` is missing until dev deps are installed.
  - Lint scope is intentionally narrow (runtime-risk rules only), not style-complete.
