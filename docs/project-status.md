# Project status — 2026-10-27

Phase: Architecture Baseline v1.0 accepted; M0 Foundation in progress.
Repository: public jnbntc/trustforge. PR #29 merged; bootstrap documentation reconciliation integrated.
Current task: TF-003 / #3, draft integration with distrobox-stack. Issue remains open.

## Proposed environment
Canonical definition: [distrobox-stack PR #18](https://github.com/jnbntc/distrobox-stack/pull/18), source commit `44851ec911ebc0eabba88eb18c53cb4849229754`.
See [consumer contract and acceptance criteria](DEVELOPMENT_ENVIRONMENT.md).
Environment, Containerfile, manifest template and tool lock live only in distrobox-stack. TrustForge has no duplicate definition.
[ADR-013](adr/013-distrobox-stack-workspace.md) is proposed for review; the 12 baseline decisions remain accepted design decisions.

## Evidence and boundaries
- Host preflight facts were provided by the user; this executor did not re-audit the real host or publish raw host evidence.
- Verified public source index/manifest digests for Fedora Toolbox 44 and uv; checked Python source metadata and resolved a hashed tool lock. No layers/interpreter/tool installation.
- Six offline workspace tests passed, plus static syntax/link/trigger/permission/consistency checks. No build, runtime, publication, deployment or reproducibility result.
- Distrobox 1.8.2.5 implicit privileged/label=disable and shared HOME/runtime require architectural review before deployment.
- Final image digest, authenticated SBOM/signature/provenance, RPM snapshot and predeployment verification gate remain pending.
- Existing workspace source definitions/orchestration/workflows were preserved. No host configurations or containers changed.

## Next steps and remaining gates
Review the two draft PRs and ADR-013. No automatic merge or deployment; separately authorize build/publication/testing and resolve the Distrobox integration boundary.
TF-001 / #1: planned LICENSE and clean-clone completion review pending.
TF-002 / #2: bootstrap reconciliation PR merged; issue completion review independent.
TF-003 / #3: implementation proposal prepared; real environment creation, verification and reproducibility remain pending.
TF-004 / #4: application src layout, dependency lock, lint/type/tests pending; workspace tools are not application dependencies.
TF-005 / #5: application CI and protection work pending. No repository permissions changed.
Application code: NOT STARTED. CI in TrustForge: NOT CONFIGURED. KVM/libvirt/bootc remain deferred to M5.
