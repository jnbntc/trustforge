# Project status — 2026-10-28

M0 software foundation is integrated; M0 as a whole is NOT complete. TF-003 operational acceptance and effective GitHub protections remain pending. All issues are left open for owner decisions.

## Confirmed integrated state
Current main: a1e74c922697cbcb6d46b87c71dc1607f9ea4733. HEAD #38 squash 79200a23f2d438458a517cfb5a3f6320408361bc passed [post-merge CI](https://github.com/jnbntc/trustforge/actions/runs/40707936814), 252 tests, Python 3.13.16. Referrers #39 was rebased to one own commit/seven own files on that main, preserving HEAD; its final head/base [PR CI](https://github.com/jnbntc/trustforge/actions/runs/40741997100) passed 302 tests before squash a1e74c922697cbcb6d46b87c71dc1607f9ea4733. [Post-merge main CI](https://github.com/jnbntc/trustforge/actions/runs/40743034646) passed 302 tests and quality/lock/distribution/install checks on Python 3.13.17.

Earlier foundations: license #32, package #33, CI #34, governance #31, OCI models #35, inspection #36 and platform selection #37 are integrated. Canonical trusted workspace stays in distrobox-stack main 541115eecce9e72bd4989ad5ac1c28f14a1a0c59, with separate ADR-013/M4 boundaries. No image build/signing/runtime acceptance follows from source integration.

## M0 recommendations
[Per-issue evidence and acceptance](M0_ACCEPTANCE.md):
- TF-001: license/bootstrap documents and clean clone verified; recommend owner acceptance/closure after content review.
- TF-002: contract/templates/ADRs/backlog exist and #31 is integrated; recommend owner acceptance/closure for its explicit contract criteria.
- TF-003: continue; roots/source/identity/environment approvals and real operational evidence are missing.
- TF-004: package/CLI/tests integrated and post-merge CI green; recommend owner acceptance/closure.
- TF-005: minimal CI integrated; continue until governance instructions are accepted and effective controls are applied/verified.

Current read-only API and authenticated Settings: both main branches are unprotected with no rulesets; both repositories have no environments. Actions default tokens are read-only, Actions PR creation/approval is disabled, all actions are allowed, global SHA enforcement is off, and fork workflow approval is first-time contributors. [Concrete owner steps](GITHUB_GOVERNANCE.md) remain unapplied. Exact commercial/legacy plan and future enforcement remain NOT VERIFIED.

## M1 acceptance and next draft
TF-101 #6 primitives/fixtures and TF-103 #8 digest/platform selection meet their scoped implementation/negative-test criteria on main; [acceptance evidence](M0_ACCEPTANCE.md) recommends closure for human decision, not automatic closure. TF-102 GET/HEAD and TF-104 one-page API/standard-fallback discovery are integrated; their issues remain open for acceptance/follow-up. TF-105 temporary-local-registry integration remains pending.

New TF-104 pagination draft: strict same-endpoint next links, aggregate limits, per-page validation and explicit multi-page counts, with unchanged single-page JSON. Local 372 tests and separate real registry smoke are recorded in [Referrers documentation](OCI_REFERRERS.md). No public paginated example was identified; actual pagination remains NOT VERIFIED. This draft must not be merged automatically.

TF-003 stays open and independent. M0/M1 as a whole are not declared complete. Only #38/#39 were authorized and integrated this sprint. No issue closure, host/container/Settings/permission changes, OCI images/blobs/configs/layers/payloads, publication, signing or deployment occurred.
