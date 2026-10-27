# Chat architect ↔ Codex implementation protocol

## Responsibility separation
Architecture chat: scope, threat model, ADRs, issue briefs, review and release recommendation.
Codex: implement only current issue; propose but do not silently accept architecture changes; produce branch/PR and evidence.
GitHub: durable source of truth, ADRs, PRs, issues, CI artifacts and milestones.
Human owner: approve sensitive architecture changes, merges and releases.

## Issue/agent contract
Issue must include objective, in/out scope, file boundaries, required tests, acceptance criteria, safety limits, evidence and dependencies.
Agent must read AGENTS.md + relevant ADRs, report assumptions, perform tests, provide reproducible commands, and request separate issue for scope changes.

## Review checklist
- Correct feature / smallest reasonable diff?
- Code/test safety: does inspect avoid executing target content?
- Digest pinning and trust boundaries?
- Signature verified before using attestation claims?
- Negative paths tested, fail closed?
- Exact tests and CI links documented?
- Policy and ADR changes approved?

## Suggested first implementation prompt (for later)
Read AGENTS.md, README.md, docs/adr/INDEX.md, and issue TF-003. Implement only the approved Fedora/Distrobox preflight/bootstrap acceptance criteria. Do not modify the host or create other project modules. Provide command outputs, test results and a PR; propose any deviations for review.
