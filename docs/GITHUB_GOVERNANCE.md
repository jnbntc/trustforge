# GitHub governance — owner runbook (TF-005)

Proposal for human application, not settings already enabled. Inspected 2026-10-28.

## Observed state and eligibility
Both repositories are public and owned by the personal account jnbntc (owner type User). Current main: TrustForge a1e74c922697cbcb6d46b87c71dc1607f9ea4733; stack 541115eecce9e72bd4989ad5ac1c28f14a1a0c59. Both report protected=false and no rulesets.

Authenticated Settings was refreshed in this sprint and shows no environments in either repository, including no trustforge-bootstrap-publish in stack; both repositories allow all actions, do not enforce global SHA pinning, require fork-workflow approval for first-time contributors, default GITHUB_TOKEN to read contents/packages, and disallow Actions creating/approving PRs.

Public repositories on current Free/Pro plans support branch protection and environment reviewers. The exact billing/legacy plan and availability of every proposed UI control are NOT VERIFIED; stop if a required option is absent. This is a personal account: do not promise organization teams or organization-only push allowlists. No paid feature or plan upgrade is assumed.
Sources: [protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches), [environment eligibility](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments).

## 1. Protect main in each repository
Owner: Settings → Branches → Add classic branch protection rule; branch pattern main.
- Enable Require a pull request before merging and Require conversation resolution.
- Require status checks to pass; select actual GitHub Actions results from the table below. Require the branch to be up to date.
- Keep Allow force pushes and Allow deletions off.
- Apply enforcement to administrators/bypass actors; do not add routine bypasses.
- With a second authorized reviewer, require one approval, dismiss stale approvals and require review of the most recent push. Authors cannot approve their own PRs. In a sole-maintainer repository, choose explicitly between adding a reviewer and a documented PR/checks-only policy; do not configure an impossible self-approval requirement.

Save, reopen the rule, and verify main reports protected plus the intended checks and review settings. Verify on a harmless documentation PR; never test by forcing a push or deleting main.
[Rule configuration](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/managing-a-branch-protection-rule), [review limitations](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/approving-a-pull-request-with-required-reviews).

| Repository | Check name | When to require |
|---|---|---|
| distrobox-stack | ShellCheck (Bash Scripts) | Exists and passed on current main; runs on all PRs |
| distrobox-stack | Hadolint (Containerfiles) | Exists and passed on current main; runs on all PRs |
| distrobox-stack | static | Exists, but path-filtered to trustforge workspace/workflows: do NOT require globally |
| TrustForge | Python 3.13 checks | Integrated on main; post-merge run 40743034646 passed. Select this exact existing name |

A globally required path-filtered workflow can leave unrelated PRs pending forever. Review static for relevant stack PRs without pretending it covers all paths. Do not require build/publication/deployment as merge checks. TrustForge now runs this check on every PR and pushes to main: [post-merge PASS](https://github.com/jnbntc/trustforge/actions/runs/40743034646). Registering it as required is still an unapplied owner action.

## 2. Review elevated workflows and token use
Before accepting edits to .github/workflows, inspect events, checkout ref, shell interpolation, action pins, permissions, target digest and environment. Changes affecting trusted publishing source require fresh human review; a green Python check is not approval of release authority.

The existing stack manual publisher declares contents:read globally; packages:write/id-token:write only in publish. It is main-only, publish defaults false, and every signature/SBOM/provenance uses the final pushed digest. The independent policy remains unapproved. No new code defect was identified requiring a publisher PR; missing protection is a remote configuration gap, not proof of a protected job.

Other existing stack workflows include scheduled publication and maintenance with elevated permissions and mutable action references. They remain unchanged and can still run independently of TrustForge. Review them separately before tightening global action restrictions; do not break existing workspaces as part of this setup.

Settings → Actions → General: preserve read-only default token and disabled Actions PR approval. The integrated Python CI explicitly uses contents:read, immutable action SHAs, no secrets/custom token, no environment, no publishing and no OCI operations. Require approval for all external fork contributors if desired. A default read token is not a ceiling: workflow permissions can request write.

Global SHA enforcement/allowlisted actions are optional follow-up after inventorying existing stack actions. Enabling SHA enforcement now would reject its unchanged tag/master references. The Python CI and manual workspace workflow already pin their actions.
[Actions settings](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository).

## 3. Configure publication environment before any dispatch publish=true
In distrobox-stack: Settings → Environments → New environment → trustforge-bootstrap-publish.
1. Configure Required reviewers with an authorized person; enable Prevent self-review. A distinct reviewer is needed if the initiator would otherwise be the only reviewer.
2. Disable Allow administrators to bypass configured protection rules.
3. Deployment branches and tags → Selected branches and tags → Branch → main. Add no tag rule. Avoid Protected branches only while no effective protection exists.
4. Save and reopen; verify reviewer, self-review prevention, bypass policy and exact branch rule. Do not dispatch merely to test settings. No new secrets/custom PATs are needed.

If that separation cannot be staffed or the controls are unavailable, publication remains BLOCKED pending an explicit owner decision. TrustForge needs no matching environment. A missing environment can be created unprotected when referenced by a workflow; the YAML name alone provides no approval gate.
[Environment configuration](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments).

These controls constrain jobs that reference the reviewed environment; a writer who can replace a workflow could omit it or request write permissions elsewhere, including on a working branch. Default read-only permissions are not a maximum permission ceiling. An environment alone does not enforce approval for every possible publisher, so review trusted workflow edits and restrict write access to trusted maintainers. Existing unrelated scheduled stack publishers are not gated by this environment and were not modified. Protect main and inspect workflow edits together. Required reviewers are a human gate, not cryptographic proof of the builder.

## 4. Verification and operational boundaries
After configuration, record a sanitized screenshot/settings summary and verify with read-only main/rules/environment views. Do not publish host inventories or secrets.

PASS: integrated license/package/CI, opt-in workspace, manual publish=false, existing lint and the real Python check. M0 still has operational blockers; see [acceptance reconciliation](M0_ACCEPTANCE.md).
BLOCKED: effective main/environment controls and operational trust approval until the owner configures/accepts them.
NOT VERIFIED: enforcement after configuration, exact paid plan, real signing/GHCR/runtime.

Merge preparation, build, publication/signing, external verification and deployment are separate approvals. publish=false still builds; publish=true rebuilds and publishes in that run. Future policy source_commit must be the actual reviewed main SHA used by the run, including a squash SHA. No instruction here authorizes dispatch, host/container changes or TF-003 closure.
