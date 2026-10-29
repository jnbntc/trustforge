# Scoped M0/M1 acceptance — 2026-10-29

Reviewed actual main 07b1eafa6879c17750bbb5e8a604d67db912837e after #41; [post-merge CI](https://github.com/jnbntc/trustforge/actions/runs/40906130405) passed 386 tests on Python 3.13 plus quality/lock/distribution/installation checks. Local Python is 3.14.8; no local 3.13 execution is claimed. The owner already closed five issues with reason completed and acceptance comments. No issue state is changed by this review.

## Matrix

COMPLETED means the named criterion is implemented and verified. PARTIAL means the issue still has pending criteria. BLOCKED identifies a required authorization/infrastructure dependency. NOT VERIFIED identifies missing evidence; it is not an invented failure.

| Issue / criterion | Category | Evidence or remaining gate |
|---|---|---|
| TF-001 #1 | COMPLETED, owner closed | Apache-2.0/license metadata and bootstrap/security/contribution files; #32 squash 7cde9a63ee7fe9b90d79545f6dd2b79613832969; documented clean clone and bounded current-tree scan |
| TF-002 #2 | COMPLETED, owner closed | AGENTS contract/templates/ADRs/backlog/roadmap; #31 squash 39b92af9d429d4116b2006683ff7b93360c17e5f |
| TF-004 #4 | COMPLETED, owner closed | src/uv/Typer/Rich/typing/doctor/package; #33 squash af83598dceef0ee7660f73eb199071bf9fa3196f; Python 3.13 main CI |
| TF-003 #3 preparation | PARTIAL | Canonical source #18/#30 and independent default-deny bootstrap exist; operational evidence absent |
| TF-003 operations | BLOCKED | Human approval of roots/policy/source/environment, build, publication/signing, verification, creation and rollback gates |
| TF-005 #5 CI | COMPLETED criterion, issue PARTIAL | Minimal permissions, all-PR check Python 3.13 checks, no publish/sign privileges in this CI; #34 integrated |
| TF-005 effective governance | BLOCKED | Both main unprotected, no rulesets/environment; owner application required |
| TF-101 #6 | COMPLETED, owner closed | Typed conceptual fixtures and raw-byte digest/negative tests; #35 squash 3ac0b6cfe5966ed6f0ba9fcbd1b15f2daf55c7da |
| TF-102 #7 implemented transport | COMPLETED criterion, issue PARTIAL | GET/HEAD, anonymous Bearer, origin/scope/redirect/deadline/size/error tests; #36/#38 integrated; real public GET/HEAD observations |
| TF-102 header correction | COMPLETED criterion, issue PARTIAL | #41 integrated as 07b1eafa6879c17750bbb5e8a604d67db912837e; duplicate singleton headers fail before consumption/token forwarding, with 14 new regression cases. Issue acceptance remains a separate owner decision |
| TF-103 #8 | COMPLETED, owner closed | Tag/digest/media/platform and child size/digest binding; #37 squash 89f3fd817659b2aef800dcd4dc9289f0d0724aba; public amd64/arm64 observations |
| TF-104 #9 bounded discovery | COMPLETED criterion, issue PARTIAL | #39/#40 integrated; API/fallback distinctions, filtering, five-page/1024-descriptor/4-MiB/shared-time limits, cycles/duplicates/no partial success; offline tests on main |
| TF-104 live pagination | NOT VERIFIED | No public paginated example was safely identified; no artifacts manufactured. Does not disprove the bounded offline-tested implementation |
| TF-105 #10 CLI | COMPLETED criterion, issue PARTIAL | Stable JSON/Rich/exit contracts and installed CLI smoke; live public metadata and offline HTTP tests |
| TF-105 local registry | BLOCKED / NOT VERIFIED | Temporary local registry requires separate infrastructure authorization; never created/tested here |

M0: three closed/two open; M1: two closed/three open. Both milestones remain open. Keep #3/#5/#7/#9/#10 open; no automatic closure. M2–M5 stay outside implementation scope.

## Evidence limits

The complete Apache-2.0 text has SHA-256 cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30. A fresh anonymous clone and bounded current-tree scan were recorded on predecessor main a1e74c922697cbcb6d46b87c71dc1607f9ea4733. These are historical checks, not an exhaustive full-history secret certification on this new main.

Public registry evidence and deterministic MockTransport fixtures are different. HEAD observes headers with content_integrity_verified=false. Inspect hashes metadata bytes. Referrers reports unauthenticated associations; no bundle/payload/signature was verified. Crypto interoperability is required for TF-003 operations, not for accepting a metadata discoverer. A compromised authorized builder remains a separate risk.

The new header regression is an offline parser finding, not proof of a live registry exploit. Main now includes the 14 new #41 cases: 386 tests passed on the actual post-merge source 07b1eafa6879c17750bbb5e8a604d67db912837e. Earlier 372-test results remain historical evidence for #40.
