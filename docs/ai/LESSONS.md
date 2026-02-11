# Lessons Learned

Use this file to prevent repeat failures. Keep entries short and factual.

## Entry Template
- Date: `YYYY-MM-DD`
- Issue: What broke or nearly broke.
- Root cause: Why it happened.
- Detection gap: Why checks did not catch it early.
- Fix applied: What was changed.
- Prevention: Guardrail/check/doc update added.
- Promote to Playbook?: `Yes/No` (Yes when repeated twice or high impact).

## Entries
- Date: `2026-02-11`
- Issue: AI sessions can drift and re-break known behavior due to missing canonical process docs.
- Root cause: No single enforced workflow for validation, handoff, and change logging.
- Detection gap: Validation and session-close protocol were optional and inconsistent.
- Fix applied: Added playbook, verify script, pre-commit guardrail, handoff template, devlog/changelog, and decisions template.
- Prevention: Use `scripts/verify.ps1`, add session handoff notes, and log lessons/decisions consistently.
- Promote to Playbook?: `Yes`
