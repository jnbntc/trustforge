# TrustForge — Codex working contract

Read `README.md`, `docs/adr/INDEX.md`, `docs/BACKLOG.md`, and `docs/project-status.md` before changing code.

## Workflow
- Work on one assigned GitHub issue at a time; use a dedicated branch and PR.
- Confirm scope and acceptance criteria before implementation. Propose architecture/policy changes in an ADR; do not quietly change the baseline.
- Never claim commands or tests passed unless they were actually run. Report commands, outputs, and limits.
- Use Python type hints and test negative/security cases; follow Ruff, mypy and pytest checks once installed.
- Changes to signing identities, trust roots, security policies, release workflows, or GitHub permissions require explicit human approval.
- Do not modify host system configuration, install host packages, change libvirt settings, deploy, publish, or access secrets without an explicitly scoped task and authorization.
- For OCI verification, bind all checks to canonical digest and verify authenticated evidence before passing claims to policy.
- Keep `docs/project-status.md` current for accepted changes, including next steps and blockers.

## Delivery summary required
- Linked issue/PR, exact files changed, tests run and their results, security implications, deviations and unresolved risks.
