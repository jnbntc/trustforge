# GitHub bootstrap reconciliation

## Verified public state — 2026-10-27
Repository: https://github.com/jnbntc/trustforge
Inspected main commit: `835347569b01c169c9c2fbca9cda4b7f1266d643`.

The initial documentation commit is published. All 28 entries in `docs/issues.json` match one live GitHub issue each, including their original title, body and milestone assignment. Six milestones exist (M0–M5); all 28 issues were open at inspection. See [issue mapping](ISSUE_MAP.md).

Do not rerun `scripts/bootstrap_github.sh`. It is a historical creation script, includes public writes, and refuses an existing repository. Reconcile an incomplete bootstrap by inspecting GitHub and making focused changes via an issue and PR; do not delete/recreate the repository, milestones or issues.

## Remaining foundation work
- [TF-001 / #1](https://github.com/jnbntc/trustforge/issues/1): README, CONTRIBUTING, SECURITY and .gitignore exist. The planned Apache-2.0 `LICENSE` file is absent. Clean-clone verification and completion review remain pending. CODEOWNERS was optional.
- [TF-002 / #2](https://github.com/jnbntc/trustforge/issues/2): working contract, templates, roadmap and ADR index exist. Reconcile stale publication status and review the audit handoff. The 12 ADR entries form the accepted design baseline; individual expanded ADR documents have not been written.
- [TF-003 / #3](https://github.com/jnbntc/trustforge/issues/3): first operational task. Begin with [read-only host preflight](FEDORA_ATOMIC_PREFLIGHT.md); host audit and Distrobox creation have not been performed by this reconciliation.
- [TF-004 / #4](https://github.com/jnbntc/trustforge/issues/4): no Python package, dependency lock or application tests yet.
- [TF-005 / #5](https://github.com/jnbntc/trustforge/issues/5): no CI workflow exists. The branch API reported `protected: false` for main. Full ruleset/private vulnerability reporting configuration was not inspected. GitHub permissions and protection changes require explicit human approval.

## Acceptance boundary
This is documentation reconciliation, not acceptance of M0. Keep foundation issues open until their own criteria and review are complete. No host configuration, signing identity, trust root, security policy, release workflow or GitHub permission is changed by this documentation proposal.
