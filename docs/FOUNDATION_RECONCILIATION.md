# Foundation reconciliation — TF-001 / TF-002

Inspection date: 2026-10-28. Source main: da596a15dfc107b358b662b02a8ac228396ac69e.

## TF-001
README, CONTRIBUTING, SECURITY and .gitignore already exist. This draft adds only the missing Apache-2.0 LICENSE from https://www.apache.org/licenses/LICENSE-2.0.txt and this reconciliation record. Apache-2.0 was already selected in the accepted README/backlog; no new licensing decision is made. No NOTICE or third-party attribution claims are invented. Package metadata in the separate TF-004 draft uses the same SPDX identifier.

A clean anonymous HTTPS clone was actually performed into an isolated workspace directory. HEAD matched the source above and git status --porcelain was empty. No historical bootstrap script was run. Repeat from a disposable working directory:
```bash
git clone https://github.com/jnbntc/trustforge.git
cd trustforge
git rev-parse HEAD
git status --porcelain
```
After this draft is merged, confirm LICENSE contains the complete standard text. Review repository content for accidental credentials before accepting TF-001; the supplied ignore/security guidance does not certify the absence of secrets across all history. CODEOWNERS remains optional and is not added with an invented reviewer.

## TF-002
The working contract, issue template, PR template, roadmap/backlog, workflow protocol, project-status, accepted ADR index and ADR-013 exist and were read. The issue template covers goal/scope/acceptance/security/evidence/out of scope; the PR template covers exact verification, negatives, risks and unresolved assumptions.

No missing framework requires creating more scaffolding. Expanded ADR-001–012 documents were not required by their accepted index. Stale draft/integration wording is reconciled separately in the governance draft, after the owner's squash merges of stack #18 and TrustForge #30. Review that status update before deciding TF-002 is complete.

Both issues remain open. Preparing files and recording a clean clone do not replace human acceptance or authorize merging, host setup or publication.
