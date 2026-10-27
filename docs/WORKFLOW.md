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

## First operational handoff: TF-003 / issue #3
Read the [read-only preflight brief](FEDORA_ATOMIC_PREFLIGHT.md), not the historical GitHub creation script. Complete phase A on the actual Fedora Atomic host and report evidence before proposing phase B. Container creation, pulls, starts, package installation and any host configuration changes require approval of the concrete plan.

The audit is not a full TF-003 implementation and must not close #3. Work on one assigned issue at a time using a dedicated branch and PR. A documentation PR is not permission to execute its commands or merge it.

## Codex audit prompt
> Continue TrustForge TF-003, GitHub issue #3. Read AGENTS.md, README.md, docs/adr/INDEX.md, docs/BACKLOG.md, docs/project-status.md and docs/FEDORA_ATOMIC_PREFLIGHT.md from the reviewed repository version. Execute phase A only on the actual Fedora Atomic host as the normal user. If this session is a container, remote executor or cannot identify the target host, stop the host checks and report the boundary; do not substitute its environment as host evidence. Use only the allowed static/version queries; do not install, pull, start, create, reset, migrate, change services/network/SELinux/permissions, use sudo or read secrets. Keep raw output private outside the tracked repository; do not publish host identifiers or raw logs. Return exact commands, outputs, errors, unverified checks and a sanitized summary, plus a proposed version-pinned Distrobox plan with effects and cleanup for human approval. Do not execute phase B or close #3.
