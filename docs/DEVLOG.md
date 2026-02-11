# Dev Log

Append-only. Add newest entry at bottom.

- 2026-02-11: Bootstrapped minimal AI Ops system: added `docs/ai/PLAYBOOK.md`, `docs/ai/LESSONS.md`, handoff/decision templates, `scripts/verify.ps1`, and a single pre-commit guardrail at `.githooks/pre-commit`. Updated `AGENTS.md` and `CLAUDE.md` to point to the playbook.
- 2026-02-11: Standardized quality checks by adding `scripts/lint.ps1` (ruff runtime-risk rules) and `scripts/typecheck.ps1` (mypy, non-blocking when missing), wired both into `scripts/verify.ps1`, added `requirements-dev.txt`, and recorded build decision (`N/A`) in playbook + decision log.
- 2026-02-11: Fixed mypy errors in `market_radar/distressed_fit/features.py` and `tests/test_distressed_fit_scoring.py`; hardened `_safe_float`/`_pct_change` null handling and explicit typing in test factory. Also made `scripts/lint.ps1` and `scripts/typecheck.ps1` propagate non-zero exits so verify/pre-commit enforcement is real.
