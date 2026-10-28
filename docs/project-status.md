# Project status — 2026-10-28

M0 software foundation is integrated; M0 as a whole is NOT complete. TF-003 operational acceptance and effective GitHub protections remain pending. All issues are left open for owner decisions.

## Confirmed integrated state
TrustForge main after this sprint: 51e46f9d8fce61218abdcf4841453660bfd051dd. License #32 (7cde9a63ee7fe9b90d79545f6dd2b79613832969), package #33 (af83598dceef0ee7660f73eb199071bf9fa3196f) and CI #34 (722d24e99e534196f17eb6eda0c91b325315b5e6) were merged by the owner. [Post-merge CI](https://github.com/jnbntc/trustforge/actions/runs/40682933075) passed Python 3.13 tests/lint/types/lock/distribution/install checks.

Canonical workspace: distrobox-stack main 541115eecce9e72bd4989ad5ac1c28f14a1a0c59, merged via #18; TrustForge #30 integrated consumer docs/ADR-013. Trusted development only; separate M4 boundary. No OCI build, final signed image, real crypto verification, runtime or reproducibility result follows from these merges.

## M0 recommendations
[Per-issue evidence and acceptance](M0_ACCEPTANCE.md):
- TF-001: license/bootstrap documents and clean clone verified; recommend owner acceptance/closure after content review.
- TF-002: contract/templates/ADRs/backlog exist; tracking corrections integrated via #31; owner acceptance remains pending.
- TF-003: continue; roots/source/identity/environment approvals and real operational evidence are missing.
- TF-004: package/CLI/tests integrated and post-merge CI green; recommend owner acceptance/closure.
- TF-005: minimal CI integrated; continue until governance instructions are accepted and effective controls are applied/verified.

Main is unprotected in both repositories, rulesets are absent and trustforge-bootstrap-publish does not exist. [Owner runbook](GITHUB_GOVERNANCE.md) proposes controls; no Settings were changed. These are the prior read-only governance observations; this sprint does not refresh Settings. Exact commercial/legacy plan and future enforcement remain NOT VERIFIED.

## Integrated M1 and next draft
[TF-101 #35](https://github.com/jnbntc/trustforge/pull/35) merged via squash 3ac0b6cfe5966ed6f0ba9fcbd1b15f2daf55c7da: reference parsing, models, fixtures and exact-byte digests.
[TF-102 #36](https://github.com/jnbntc/trustforge/pull/36) merged via squash 51e46f9d8fce61218abdcf4841453660bfd051dd: bounded HTTPS/Bearer and CLI. It was rebased to one own commit/ten own files on actual main; fresh CI verified the new head/base before merge. Governance #31 merged via squash 39b92af9d429d4116b2006683ff7b93360c17e5f.

[Final main CI](https://github.com/jnbntc/trustforge/actions/runs/40692755282): PASS on Python 3.13.17, 177 tests, Ruff/format, mypy, lock, wheel/sdist and clean installation. [Separate real installed-CLI metadata tests](M1_INTEROPERABILITY.md): Docker Hub, Quay and GHCR passed both tag and immutable-digest queries; observed registry headers matched raw-byte hashes. No configs/layers/images were downloaded.

Next capability: TF-103 #8, explicit platform selection and one same-repository child-manifest GET, with descriptor digest/size/media verification and distinct index/child digests. This is a new draft for human review and is not merged. It contributes to TF-105 #10. Unit/negative CI remains offline; manual public interoperability is separately labelled.

M1 remains partial: TF-102 HEAD, TF-104 referrers and TF-105 temporary-local-registry integration remain pending. TF-003 is open and does not block this authorized metadata sprint. No issue closure, Settings/host/container changes, image build, publication, signing or deployment occurred. Only existing #31/#35/#36 were authorized for integration; do not merge the new platform draft without a new review/authorization.
