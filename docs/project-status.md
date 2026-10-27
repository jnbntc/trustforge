# Project status — 2026-10-27

Phase: Architecture Baseline v1.0 accepted as design; M0 Foundation in progress.
Repository: public [jnbntc/trustforge](https://github.com/jnbntc/trustforge), published.
Inspection base: `835347569b01c169c9c2fbca9cda4b7f1266d643`.
Issues: 28 created, all open at inspection; six milestones M0–M5. See [mapping](ISSUE_MAP.md).
Runtime environment: dedicated `trustforge-dev` planned; host and existing containers not audited here.
Application code: NOT STARTED. CI: NOT CONFIGURED. Releases: NONE (GitHub releases API returned an empty list at inspection).

## Current documentation proposal
TF-002 / #2: reconcile bootstrap status and prepare the read-only TF-003 handoff.
The ADR index contains 12 accepted design decisions, with environment validation pending; expanded ADR files do not yet exist. No baseline decision is changed.

## Next operational task
[TF-003 / #3](https://github.com/jnbntc/trustforge/issues/3): execute only the read-only phase in [Fedora Atomic preflight](FEDORA_ATOMIC_PREFLIGHT.md) on the actual host, produce a private evidence report and a sanitized summary, then present a concrete Distrobox plan for approval.
This proposal prepares instructions; it has NOT executed the host audit and does NOT authorize container creation.

## Remaining gates and blockers
- TF-001 / #1: add the planned Apache-2.0 LICENSE, verify clean clone and finish review.
- TF-002 / #2: documentation reconciliation pending PR review/merge; individual ADR expansion can be scoped separately without changing accepted decisions.
- TF-003 / #3: host edition/version, tool availability, storage, SELinux and static rootless prerequisites unknown. Runtime behavior and networking remain untested until separately authorized.
- TF-004 / #4: Python src layout, selected/pinned toolchain, tests, lint and type checks pending.
- TF-005 / #5: hardened CI and protection instructions pending; branch API reported main unprotected. Full rulesets and private reporting settings unverified.
- KVM/libvirt/bootc remain deferred to M5. No installation, host configuration or runtime change is part of this proposal.
