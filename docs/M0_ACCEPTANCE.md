# M0 acceptance reconciliation — 2026-10-28

Evidence snapshot: main 722d24e99e534196f17eb6eda0c91b325315b5e6. This is a recommendation for human acceptance, not automatic closure. M0 remains incomplete while TF-003 and operational protection criteria are pending.

## Integrated evidence
- #32 Apache-2.0: squash 7cde9a63ee7fe9b90d79545f6dd2b79613832969.
- #33 Python package: squash af83598dceef0ee7660f73eb199071bf9fa3196f.
- #34 Python CI: squash 722d24e99e534196f17eb6eda0c91b325315b5e6.
- [Post-merge CI PASS](https://github.com/jnbntc/trustforge/actions/runs/40682933075): existing Python 3.13 checks covers tests, Ruff check/format, strict mypy, lock consistency, wheel/sdist, rebuild from sdist and installed-wheel CLI/negative smoke.
- Current anonymous HTTPS clone actually matched this main and git status --porcelain was empty. LICENSE matches the complete standard file (SHA-256 cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30).
- A limited current-tree scan for private-key headers, GitHub token signatures and AWS access-key signatures found no matches. This is not an exhaustive secret/history audit or a guarantee that every possible secret format is absent.

| Issue | Implementation / evidence | Pending criteria | Residual risk / recommendation |
|---|---|---|---|
| TF-001 #1 | LICENSE, README, CONTRIBUTING, SECURITY, ignore rules; documented and repeated clean clone; license hash checked | Owner content/acceptance review | Limited scan is not full-history certification; CODEOWNERS was optional. Recommend closure after human review |
| TF-002 #2 | AGENTS, issue/PR templates, ADR index/013, backlog/roadmap/workflow protocol exist; #31 reconciles stale integration statements | Review/accept updated tracking docs | Design acceptance is not runtime proof. Recommend closure after #31 review/integration |
| TF-003 #3 | Opt-in canonical workspace and independent Cosign adapter/negative tests integrated in stack; trusted-development scope accepted | Approved roots/source/identity and protected publication environment; authorized build/signing/real verification/runtime/persistence/reproducibility/rollback | Mock bootstrap tests are not crypto interoperability. Continue open |
| TF-004 #4 | src-layout, uv lock, Typer/Rich/Pydantic CLI, strict typing, pytest/Ruff/mypy and installed distributions; real post-merge CI | Owner acceptance | doctor checks Python/PATH only. Recommend closure; no need to wait for OCI/runtime operations |
| TF-005 #5 | Read-only, pinned-action CI integrated and green; exact check exists; #31 gives concrete protection/environment instructions | Owner policy choice, application and read-only verification of effective protections | Unprotected main and missing environment allow an unreviewed publisher change/dispatch. Continue open until controls meet chosen acceptance |

## Effective control observations
Read-only API reports main protected=false and empty rulesets in both repositories. Authenticated Settings shows no publication environment in stack. Actions default token is read-only, Actions PR approval disabled; all actions allowed and global pinning not enforced. These are observations, not proposed desired values. No settings were changed.

The exact paid/legacy plan and actual enforcement of future rules are NOT VERIFIED. Public-personal-repository eligibility and sole-maintainer reviewer limitations are explained in GITHUB_GOVERNANCE.md; no organization-only capabilities are promised.

## Boundary
A technical recommendation to close TF-001/004 does not close them. TF-002 depends on reviewing these tracking corrections; TF-003/005 keep the overall M0 gate open. The user separately authorized the initial read-only M1 code while those operational tasks remain pending. That work neither consumes trustforge-dev nor authorizes infrastructure execution.
