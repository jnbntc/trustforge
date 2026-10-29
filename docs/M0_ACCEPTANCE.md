# Scoped M0/M1 acceptance — 2026-10-28

Reviewed actual main a1e74c922697cbcb6d46b87c71dc1607f9ea4733. Recommendations concern each issue's own criteria, not completion of all M0/M1. No issue is closed automatically; no operational authorization follows.

## Current evidence

- Fresh anonymous HTTPS clone matched this main with empty git status. All 59 tracked files and the required license, contribution/security guidance, ignore rules, templates, ADRs, contract, package and tests are present.
- LICENSE matches full Apache-2.0, SHA-256 cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30; pyproject declares Apache-2.0 consistently. CODEOWNERS was optional.
- A bounded current-tree scan for private-key headers, GitHub token signatures and AWS access-key signatures found no matches. This is not a full-history/exhaustive secret certification.
- [Post-merge main CI](https://github.com/jnbntc/trustforge/actions/runs/40743034646): PASS, Python 3.13.17, 302 tests, Ruff check/format, strict mypy, lock, wheel/sdist, rebuilt wheel and fresh installed CLI smoke. Local checks use Python 3.14.8; local Python 3.13 is not claimed.
- HEAD #38 squash 79200a23f2d438458a517cfb5a3f6320408361bc had [post-merge CI](https://github.com/jnbntc/trustforge/actions/runs/40707936814), 252 tests. Referrers #39 preserved HEAD and passed fresh head/base CI before squash a1e74c922697cbcb6d46b87c71dc1607f9ea4733.

## Explicit recommendations to the owner

| Issue | Actual criterion and main evidence | Recommendation / residual limit |
|---|---|---|
| TF-001 #1 | Public Apache-2.0 repo, README/CONTRIBUTING/SECURITY/ignore rules, documented and repeated clean clone, bounded current-tree signature scan with no matches. [License #32](https://github.com/jnbntc/trustforge/pull/32), squash 7cde9a63ee7fe9b90d79545f6dd2b79613832969 | PASS for recorded checks; recommend closure after owner content acceptance. Not a certification that every possible secret/history leak is absent |
| TF-002 #2 | AGENTS gives explicit scope, approval boundaries and delivery contract; issue/PR templates, ADR index/013, backlog, roadmap and status exist. [Governance #31](https://github.com/jnbntc/trustforge/pull/31), squash 39b92af9d429d4116b2006683ff7b93360c17e5f | PASS for its explicit contract criterion; recommend closure after owner acceptance. Tracking reconciliation in this draft is not treated as merged evidence |
| TF-004 #4 | src-layout, uv/lock, Typer/Rich/Pydantic, pytest/Ruff/mypy, typing, help/version/doctor and installed distributions checked locally and in Python 3.13 CI. [Package #33](https://github.com/jnbntc/trustforge/pull/33), squash af83598dceef0ee7660f73eb199071bf9fa3196f | PASS; recommend closure. doctor checks Python/PATH only; TF-003 runtime work is separate |
| TF-101 #6 | Illustrative manifest/index/descriptor/blob fixtures, typed metadata, raw-byte SHA-256 tests and malformed/duplicate JSON, digest/schema/size/media negatives. [Models #35](https://github.com/jnbntc/trustforge/pull/35), squash 3ac0b6cfe5966ed6f0ba9fcbd1b15f2daf55c7da; regressions preserved in main CI | PASS for scoped conceptual/protocol-negative criteria; recommend closure. Fixtures are not authenticated images |
| TF-103 #8 | Tags resolve to raw-byte digests; expected/header/child digest and media/size checked; index/child digests distinct; explicit platform selection rejects missing/ambiguous descriptors. [Platform #37](https://github.com/jnbntc/trustforge/pull/37), squash 89f3fd817659b2aef800dcd4dc9289f0d0724aba; regressions preserved in main CI | PASS; recommend closure. [Real observations](M1_INTEROPERABILITY.md) cover three registries and amd64/arm64 children; labels remain index claims, not runtime compatibility or cryptographic verification |

## Keep pending issues separate

- TF-003 #3: source integration and independent verifier preparation exist, but approved roots/source/identity, protected publisher and authorized real operational/reproducibility/rollback evidence remain pending. Mocks do not establish crypto interoperability. Keep open.
- TF-005 #5: CI integrated, but main is unprotected in both repos, no rulesets/environments exist and owner controls are unapplied. Keep open; use [the runbook](GITHUB_GOVERNANCE.md).
- TF-102 #7: GET/HEAD integrated and tested, including real public HEAD observations. Leave open for specific owner acceptance/follow-up; this review does not automatically close it.
- TF-104 #9: one-page discovery/standard fallback integrated. Bounded pagination is proposed in a new draft, not main; real paginated interoperability remains NOT VERIFIED. Keep open.
- TF-105 #10: CLI JSON/Rich and public metadata tests exist; temporary-local-registry integration has not run and requires its own authorized infrastructure scope. Keep open.

M0 and M1 as whole milestones remain incomplete. Recommending five scoped closures does not close them, merge the pagination draft, apply GitHub configuration or authorize OCI building/publishing/signing/execution.
