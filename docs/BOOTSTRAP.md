# GitHub bootstrap reconciliation

## Current state — 2026-10-28
Inspected main: 722d24e99e534196f17eb6eda0c91b325315b5e6. License #32, Python package #33 and CI #34 are merged. [Post-merge CI](https://github.com/jnbntc/trustforge/actions/runs/40682933075) passed. All M0 issues remain open for explicit acceptance; use [per-issue recommendations](M0_ACCEPTANCE.md).

TF-001 license and clean-clone criteria are technically satisfied; TF-002 scaffolding exists and stale status is corrected by #31. TF-004 package/CLI/quality checks are integrated. TF-005 minimal CI is integrated, but main/environment protections remain unapplied. TF-003 has only preparatory source and still needs its separately authorized operational evidence.

## Historical bootstrap
The initial documentation catalogue matched 28 live issues and six milestones at the 2026-10-27 bootstrap inspection (835347569b01c169c9c2fbca9cda4b7f1266d643). docs/issues.json is the original catalogue, not a live acceptance report; use GitHub and project-status for subsequent work.

Do not rerun scripts/bootstrap_github.sh. It is a historical public-write creation script that refuses an existing repository. Reconcile focused changes through issues/PRs; never delete/recreate the repository, milestones or issues.

## Boundary
Source integration and green CI do not approve roots/identities, build, publication/signing or deployment. No host or GitHub setting is changed by this reconciliation. M0 is not complete while TF-003 and effective protections remain pending. Read [owner runbook](GITHUB_GOVERNANCE.md), [project status](project-status.md) and [consumer contract](DEVELOPMENT_ENVIRONMENT.md).
