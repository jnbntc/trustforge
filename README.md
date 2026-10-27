# TrustForge — Architecture Baseline v1.0
Date: 2026-10-27. Status: accepted scope and design baseline; implementation NOT started.

## Mission
Educational, reproducible OCI software supply-chain verification and verified-update laboratory. First deliverable: a Python CLI that inspects OCI artifacts, verifies authenticated evidence, applies explicit admission policy, and exports audit reports.

## Approved user decisions
- Planned public repository: `jnbntc/trustforge` (not created).
- Dedicated Fedora Atomic Distrobox: `trustforge-dev` (not created).
- Deep educational exploration of OCI internals.
- GitHub issues + pull requests; architecture/review chat and implementation Codex chat.
- Podman rootless first; investigate KVM/libvirt only before M5.

## Core principles
1. Git repository is source of truth, not either chat.
2. Modular Python monolith, CLI first; no Kubernetes, UI, database, or long-running service in v0.1.
3. Inspection via an educational OCI HTTP client; cryptographic verification delegated to trusted Sigstore tooling.
4. Separate verification from authorization. Fail closed on missing, malformed or unverifiable evidence.
5. Pin the exact image digest throughout verification and consumption; protect against mutable tags and TOCTOU.
6. Negative security tests are required before completing milestones.
7. Do not execute unknown images during inspection.

## Logical data flow
`GitHub commit -> trusted build/push to registry -> image digest + signed evidence -> OCI inspector -> Cosign/Sigstore verifier -> normalized verified evidence -> OPA/Rego policy -> ALLOW/DENY + structured report -> optional consumer constrained to approved digest`.

## Components
- `oci`: Distribution API v1.1, manifests, indexes, blobs, media types, referrers, authentication, raw digest verification and size limits.
- `verification`: invoke trusted verifier with strict identity/issuer and capture structured verified statements.
- `provenance`: validate subject, source, workflow/builder against authenticated attestations.
- `sbom`: inspect/authenticate attached SPDX inventories; vulnerability analysis deferred.
- `policy`: OPA/Rego decisions against normalized evidence, default DENY.
- `reporting`: human-readable explanation, machine-readable JSON and stable failure reason codes.
- `cli`: Typer/Rich user-facing interface.

## Threat model (initial)
Adversary may alter tags, substitute images, publish unauthorized images, forge unauthenticated JSON, omit attestations, exploit registry API failures, or introduce vulnerable packages. Trust assumptions: configured OIDC identity, Sigstore trust roots, allowed build platform, code review/CI configuration, local verifier integrity. A compromised authorized builder remains a residual risk.

## Constraints
Rootless Podman for container tests. Distrobox isolates userland dependencies but is NOT a security boundary. Use disposable KVM guest for bootc destructive tests. Registry responses and external artifacts are untrusted input. No real secrets in repo, fixture logs, evidence samples, or CI output.

## Tool selection (baseline; version pins during M0)
Fedora Atomic, Distrobox, Podman/Buildah, Python 3.13 proposed, uv, Typer, Rich, Pydantic 2, HTTPX, pytest, Ruff, mypy, ORAS/Skopeo reference tooling, Cosign, Syft/SPDX JSON, Grype later, OPA/Rego, GHCR, GitHub Actions, OCI Distribution local registry, KVM/libvirt/bootc later.

## Initial CLI contracts (planned)
- `trustforge inspect IMAGE[@sha256:...]`
- `trustforge verify IMAGE@sha256:... --policy policies/development.rego --json-out report.json`
- `trustforge explain report.json`
- `trustforge lab run SCENARIO` (M4)
- `trustforge gate run IMAGE@sha256:...` (future, no implicit deployment)

## Delivery protocol
User approves architectural changes; architecture chat creates scoped implementation brief; Codex implements via branch/PR; CI, evidence and review precede merge. Each PR links issue, changes, commands/results, negative tests, residual risk and doc updates. Record decisions via ADRs and progress via `docs/project-status.md`.

## Open validation before implementation
Check host Fedora edition/version, Distrobox and Podman availability, rootless networking, SELinux, storage space and availability of hardware virtualization; check registry referrers support and current compatibility for chosen tool versions. Baseline decisions are not claims that these checks passed.

## References
- https://specs.opencontainers.org/
- https://specs.opencontainers.org/distribution-spec/
- https://docs.sigstore.dev/
- https://slsa.dev/spec/v1.2/
- https://bootc.dev/
