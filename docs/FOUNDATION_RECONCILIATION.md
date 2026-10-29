# Foundation reconciliation — TF-001 / TF-002

Historical inspection date: 2026-10-28. Source main: da596a15dfc107b358b662b02a8ac228396ac69e. Open/draft statements below describe that earlier observation; the owner-acceptance update at the end supersedes them.

## TF-001
README, CONTRIBUTING, SECURITY and .gitignore already exist. PR #32 added the missing Apache-2.0 LICENSE from https://www.apache.org/licenses/LICENSE-2.0.txt and this reconciliation record. Apache-2.0 was already selected in the accepted README/backlog; no new licensing decision is made. No NOTICE or third-party attribution claims are invented. Integrated TF-004 package metadata uses the same SPDX identifier.

A clean anonymous HTTPS clone was actually performed into an isolated workspace directory. HEAD matched the source above and git status --porcelain was empty. No historical bootstrap script was run. Repeat from a disposable working directory:
```bash
git clone https://github.com/jnbntc/trustforge.git
cd trustforge
git rev-parse HEAD
git status --porcelain
```
The integrated LICENSE was rechecked against the complete standard text on current main. Review repository content for accidental credentials before accepting TF-001; the supplied ignore/security guidance does not certify the absence of secrets across all history. CODEOWNERS remains optional and is not added with an invented reviewer.

## TF-002
The working contract, issue template, PR template, roadmap/backlog, workflow protocol, project-status, accepted ADR index and ADR-013 exist and were read. The issue template covers goal/scope/acceptance/security/evidence/out of scope; the PR template covers exact verification, negatives, risks and unresolved assumptions.

No missing framework requires creating more scaffolding. Expanded ADR-001–012 documents were not required by their accepted index. Stale draft/integration wording is reconciled separately in the governance draft, after the owner's squash merges of stack #18 and TrustForge #30. Review that status update before deciding TF-002 is complete.

Both issues remain open. Preparing files and recording a clean clone do not replace human acceptance or authorize merging, host setup or publication.

## Historical acceptance update
At main 722d24e99e534196f17eb6eda0c91b325315b5e6, the owner has merged #32/#33/#34 and post-merge CI passed. A fresh anonymous clone matched this head with clean git status. See [M0 acceptance](M0_ACCEPTANCE.md) for current recommendations; preceding observations about the earlier clone/source are historical. No issues were closed and no operational authorization follows from these merges.

## Owner acceptance — 2026-10-29
TF-001 and TF-002 are now closed by the owner with reason completed and acceptance comments, as is TF-004. Earlier open/draft observations above are historical. Current status and the scoped acceptance matrix supersede them; do not reopen or duplicate this work. No operational authorization follows.
