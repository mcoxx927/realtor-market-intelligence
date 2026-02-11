# AI Ops Playbook

## Quickstart Commands
- Install: `pip install -r requirements.txt`
- Install dev checks: `pip install -r requirements-dev.txt`
- Enable guardrail hook: `git config core.hooksPath .githooks`
- Dev run (safe): `python run_scheduled.py --no-fetch --no-notify --no-ai --dry-run`
- Lint: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/lint.ps1`
- Typecheck: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/typecheck.ps1`
- Test: `python -m unittest discover -s tests -p "test_*.py"`
- Build: `N/A` (no package/binary build step for this pipeline repository)

## Repo Map
- Pipeline scripts: repo root (`run_market_analysis.py`, `run_scheduled.py`, stage scripts)
- Radar and distressed fit code: `market_radar/`
- Tests: `tests/`
- Generated outputs: `core_markets/` and `market_radar/outputs*/`
- Docs: `docs/` (AI ops in `docs/ai/`, handoffs in `docs/handoffs/`, decisions in `docs/decisions/`)

## Minimum Viable Standards
1. Follow the truth policy: never claim checks passed unless run.
2. Keep scope tight to the requested deliverable.
3. Do not add dependencies unless necessary; document why and alternatives.
4. Prefer isolated, small changes over broad refactors.
5. Do not edit generated output files unless explicitly requested.
6. Do not modify secrets/config values in `.env`, `notifications_config.json`, or key files unless asked.
7. Use existing project commands; do not invent new pipeline behavior.
8. Run `scripts/verify.ps1` before finalizing meaningful code/doc changes.
9. If a check is not runnable, report it explicitly as `NOT RUN`.
10. Record notable regressions/process failures in `docs/ai/LESSONS.md`.
11. Record non-trivial architecture choices in `docs/decisions/`.
12. End meaningful sessions with a handoff note in `docs/handoffs/`.

## Protected Files and Areas
- Sensitive/local config: `.env`, `notifications_config.json`, `api_key.txt`
- Large source datasets: `city_market_tracker.tsv000.gz`, `county_market_tracker.tsv000.gz`
- Scheduler/automation infra: `setup_task_scheduler.ps1`, task scheduler guidance docs
- CI/hook guardrails: `.githooks/pre-commit`, `scripts/verify.ps1`
- Generated artifacts: `core_markets/**/YYYY-MM/*`, `market_radar/outputs*/**`

Do not touch these without explicit instruction and a short rationale in the handoff/devlog.

## Definition of Done
- Requested change implemented with minimal scope.
- `scripts/verify.ps1` run, or clearly marked `NOT RUN` with reason.
- Risks/open questions captured in handoff note.
- `docs/DEVLOG.md` appended for meaningful changes.
- User-facing change noted in `CHANGELOG.md` when applicable.

## Session Protocol
1. Read this playbook and relevant local docs before edits.
2. Make the smallest change set that satisfies the request.
3. Run verification checks.
4. Append `docs/DEVLOG.md`.
5. Add handoff note in `docs/handoffs/` using `docs/handoffs/TEMPLATE.md`.

## Failure Loop
- Add a short entry to `docs/ai/LESSONS.md` when a session causes:
  - Repeated breakage/regression
  - Avoidable command/config mistakes
  - Mismatch between claimed and actual validation
- Promote a lesson into this playbook when the same issue appears twice or the blast radius is high.

## TODO: Missing Standard Commands
- No build command is required currently. Revisit only if packaging/deployment artifacts are introduced.
