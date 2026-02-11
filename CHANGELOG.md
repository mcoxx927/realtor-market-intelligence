# Changelog

## Unreleased
- Added AI Ops playbook, lessons loop, handoff template, decision template, devlog, verification script, and pre-commit guardrail.
- Added standardized lint/typecheck scripts and wired them into verification.
- Added `requirements-dev.txt` for quality tooling dependencies.
- Documented build decision as `N/A` for current pipeline architecture.
- Fixed radar `--month` runs so requested month now controls data selection (instead of output naming only).
- Fixed report attachment lookup to use metro slug from config even when `output_directory` leaf differs.

## 2026-02-11
- Initialized project-level AI Ops workflow and session documentation scaffolding.
