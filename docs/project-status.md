# Project status — 2026-10-27

Phase: M0 Foundation. TF-003 / #3 remains open.
Current work: architecture corrections on existing draft [distrobox-stack #18](https://github.com/jnbntc/distrobox-stack/pull/18) and [TrustForge #30](https://github.com/jnbntc/trustforge/pull/30). No new PRs, merges or deployment.

## Revised architecture
[ADR-013](adr/013-distrobox-stack-workspace.md): revised proposal for review. The user's architecture review accepts Distrobox only for trusted development; explicit host integration and rootless/privileged/SELinux limits remain documented.
M4 adversarial work uses a separate restricted runtime or disposable VM according to risk; not implemented here.
[Consumer contract](DEVELOPMENT_ENVIRONMENT.md) references one canonical definition in distrobox-stack commit `2998e59790416c491d65fced798554a97c3e3b02`; no duplicate environment recipe, lock or policy here.

## Prepared trust bootstrap
Independent pinned Cosign verifier outside the target workspace removes the dependency on M3 Gate. It checks exact signer/issuer/workflow/source, approved roots, image digest and authenticated SBOM/provenance subjects/parameters/materials.
Future manual build/publish/sign workflow and specific offline PR checks are prepared. Policy is unapproved and real image digest/evidence do not exist as task results.
No crypto verification or container/reproducibility result is inferred from fixture/static tests. Pins already checked for base/uv/Python/lock were preserved without needless revalidation.

## Next steps
New review of both corrected PRs, ADR-013, proposed identity/issuer/trust roots and permissions. Then explicitly authorize build, publication/signing, real independent verification and deployment as distinct steps.
Trust policy/source commit/roots must be approved externally; successful verification still requires new human approval before consuming that exact digest.
RPM repositories and Distrobox initialization remain mutable; inventory is not a snapshot.
Existing workspace definitions and pre-existing pipelines preserved. No host/storage/SELinux/service/container changes.
TF-001 license/clean-clone review, TF-002 completion review, TF-004 application layout/dependencies/tests and TF-005 application CI/protection remain separate work. Application code not started; no M4 implementation.
