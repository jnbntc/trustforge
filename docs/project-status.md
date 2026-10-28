# Project status — 2026-10-28

M0 software foundation is integrated; M0 as a whole is NOT complete. TF-003 operational acceptance and effective GitHub protections remain pending. All issues are left open for owner decisions.

## Confirmed integrated state
TrustForge main: 722d24e99e534196f17eb6eda0c91b325315b5e6. License #32 (7cde9a63ee7fe9b90d79545f6dd2b79613832969), package #33 (af83598dceef0ee7660f73eb199071bf9fa3196f) and CI #34 (722d24e99e534196f17eb6eda0c91b325315b5e6) were merged by the owner. [Post-merge CI](https://github.com/jnbntc/trustforge/actions/runs/40682933075) passed Python 3.13 tests/lint/types/lock/distribution/install checks.

Canonical workspace: distrobox-stack main 541115eecce9e72bd4989ad5ac1c28f14a1a0c59, merged via #18; TrustForge #30 integrated consumer docs/ADR-013. Trusted development only; separate M4 boundary. No OCI build, final signed image, real crypto verification, runtime or reproducibility result follows from these merges.

## M0 recommendations
[Per-issue evidence and acceptance](M0_ACCEPTANCE.md):
- TF-001: license/bootstrap documents and clean clone verified; recommend owner acceptance/closure after content review.
- TF-002: contract/templates/ADRs/backlog exist; accept after reviewing the stale-state corrections in #31.
- TF-003: continue; roots/source/identity/environment approvals and real operational evidence are missing.
- TF-004: package/CLI/tests integrated and post-merge CI green; recommend owner acceptance/closure.
- TF-005: minimal CI integrated; continue until governance instructions are accepted and effective controls are applied/verified.

Main is unprotected in both repositories, rulesets are absent and trustforge-bootstrap-publish does not exist. [Owner runbook](GITHUB_GOVERNANCE.md) proposes controls; this PR does not configure them. Exact commercial/legacy plan and future enforcement remain NOT VERIFIED.

## Authorized initial M1 work
[TF-101 draft #35](https://github.com/jnbntc/trustforge/pull/35): reference parsing, typed metadata, fixtures and raw-byte SHA-256.
[TF-102 draft #36](https://github.com/jnbntc/trustforge/pull/36), based on #35: bounded anonymous HTTPS/Bearer and oci inspect CLI; initial portions of TF-103/105.
These drafts do not depend on Gate M3, do not execute images and do not complete M1. Referrers TF-104 and local/real-registry integration remain pending. Governance owns tracking docs; M1 drafts own OCI code/tests/guides without overlapping these edits.

Review #31 independently, #35 before #36, then rebase/retarget #36 to merged main and require fresh CI. No merges or issue closure by this executor. No host/container/Settings changes, publication, signing or deployment.
