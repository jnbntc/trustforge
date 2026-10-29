# Project status — 2026-10-29

Reviewed main: 07b1eafa6879c17750bbb5e8a604d67db912837e after the authorized #41 squash. M0 and M1 are NOT complete; no M2 implementation has started.

## Integrated software and acceptance

HEAD #38, Referrers #39 and bounded pagination #40 are integrated. #40 used the explicitly authorized head 7fcfab0e36f7fbf79cd283c3cb29c74cfa57c6cf and squash 297d3290e32e3f0aea56a91abaa6037d9174c250. [Post-merge CI](https://github.com/jnbntc/trustforge/actions/runs/40809965768) passed on this actual main: Python 3.13.17, 372 tests, Ruff check/format, strict mypy, lock, wheel/sdist/rebuilt wheel and clean installation. Earlier foundations #31–#37 remain integrated.

The owner closed TF-001 #1, TF-002 #2, TF-004 #4, TF-101 #6 and TF-103 #8 as completed, with acceptance comments. This sprint neither closed nor reopened issues. M0 has three closed/two open issues; M1 has two closed/three open. Both milestones remain open.

Inspect, explicit platform selection, HEAD, Referrers API/standard fallback and bounded pagination exist on main. [Acceptance matrix](M0_ACCEPTANCE.md) separates completed software criteria, partial issues, blocked operations and missing evidence. TF-102 #7 and TF-104 #9 can receive scoped software acceptance; keep them open for the owner's decision. TF-105 #10 still lacks temporary-local-registry integration.

Real metadata observations on 2026-10-28 cover Docker Hub, Quay and GHCR; see [interoperability](M1_INTEROPERABILITY.md), [HEAD](OCI_HEAD.md) and [Referrers](OCI_REFERRERS.md). They are separate from offline tests. No real paginated reference was identified; actual pagination remains NOT VERIFIED. Hashes establish metadata integrity, not publisher identity or authenticated association.

## Header correction and documentation integration

- [#41](https://github.com/jnbntc/trustforge/pull/41): duplicate singleton HTTP-header rejection. Offline reproduction on main accepted contradictory Content-Type fields when the first had parameters. The transport check is integrated as 07b1eafa6879c17750bbb5e8a604d67db912837e and rejects ambiguity before body consumption/token forwarding. The 386-test [PR CI](https://github.com/jnbntc/trustforge/actions/runs/40810395105) and [post-merge CI](https://github.com/jnbntc/trustforge/actions/runs/40906130405) passed; the latter validates the actual main source. No claim of a registry compromise or cryptographic break.
- This documentation consolidation records accepted issues, actual integration, governance and operational preparation only. The owner authorized integration of this reviewed #42 after updating the #41 references and passing fresh CI against the final head/base. This authorization does not cover operations or other PRs.

## Operational foundation and next decision

TF-003 #3 remains blocked on approved trust anchors/policy, effective publisher protection and separate build/publication/verification/deployment authorizations. [Operational checklist](TF003_OPERATIONAL_CHECKLIST.md) prepares those gates without executing them. distrobox-stack remains the only workspace source at 541115eecce9e72bd4989ad5ac1c28f14a1a0c59. ADR-013 limits trustforge-dev to trusted development; M4 has an independent boundary.

TF-005 #5 remains partial: minimal CI is integrated, effective GitHub governance is not applied. Read-only API/Settings inspection found both main branches unprotected, no rulesets and no environments, including no trustforge-bootstrap-publish in stack. Actions default to read-only tokens and cannot create/approve PRs. Collaborator eligibility was not verified because its Settings page requires reauthentication; no available independent reviewer is assumed. [Exact owner steps](GITHUB_GOVERNANCE.md).

Next owner action: accept/apply the minimum main/environment governance and approve the independent trust inputs. Only then consider a separately authorized candidate build with publish=false. That dispatch still builds an OCI image. No build, publication, signature, container, host or GitHub Settings change occurred in this consolidation.

[M2 preparation](M2_PREPARATION.md) is a learning and test brief, not implementation or permission to build/sign/publish. No milestone completion follows from this document.
