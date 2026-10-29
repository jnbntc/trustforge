# GitHub bootstrap reconciliation

## Current state — 2026-10-28
Inspected main: 297d3290e32e3f0aea56a91abaa6037d9174c250. License/package/CI, OCI inspect/platform/HEAD/Referrers and pagination #40 are integrated. [Post-merge CI](https://github.com/jnbntc/trustforge/actions/runs/40809965768) passed 372 tests. The owner closed TF-001/002/004/101/103 as completed; use the [acceptance matrix](M0_ACCEPTANCE.md). TF-003/005 and M1 as a whole remain pending.

TF-001/TF-002/TF-004 are accepted and closed. Their license/scaffolding/package work must not be duplicated. TF-005 minimal CI is integrated, but main/environment protections remain unapplied. TF-003 has only preparatory source and still needs its separately authorized operational evidence.

## Historical bootstrap
The initial documentation catalogue matched 28 live issues and six milestones at the 2026-10-27 bootstrap inspection (835347569b01c169c9c2fbca9cda4b7f1266d643). docs/issues.json is the original catalogue, not a live acceptance report; use GitHub and project-status for subsequent work.

Do not rerun scripts/bootstrap_github.sh. It is a historical public-write creation script that refuses an existing repository. Reconcile focused changes through issues/PRs; never delete/recreate the repository, milestones or issues.

## Boundary
Source integration and green CI do not approve roots/identities, build, publication/signing or deployment. No host or GitHub setting is changed by this reconciliation. M0 is not complete while TF-003 and effective protections remain pending. Read [owner runbook](GITHUB_GOVERNANCE.md), [project status](project-status.md) and [consumer contract](DEVELOPMENT_ENVIRONMENT.md).
