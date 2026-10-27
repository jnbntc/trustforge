# Initial backlog — TrustForge
M0–M5 and all 28 issues have been created on GitHub. Identifiers TF-* remain stable planning IDs, distinct from GitHub numbers; see the [verified mapping](ISSUE_MAP.md). `docs/issues.json` preserves the original bootstrap catalogue; live GitHub issues carry subsequent scope refinements.

First operational task: [TF-003 / #3](https://github.com/jnbntc/trustforge/issues/3), read-only preflight first. TF-001 and TF-002 remain open for bootstrap gaps and review; publication alone does not complete M0.

## M0 — Foundation (Gate: lint/type/tests green; documentation and reproducible bootstrap)
- TF-001: Initialize public Apache-2.0 repo, README, CODEOWNERS optional, CONTRIBUTING, .gitignore, security reporting guidance. Acceptance: clean clone documented; no secrets.
- TF-002: `AGENTS.md`, issue/PR templates, ADR framework, project-status and roadmap. Acceptance: Codex has explicit scope and delivery contract.
- TF-003: Dedicated Distrobox bootstrap and host preflight read-only checks. Acceptance: reproducible on Fedora Atomic; versions recorded; no host mutation without approval.
- TF-004: Python src-layout with uv, Typer, pytest, Ruff, mypy. Acceptance: CLI `--help`, tests, lint, type-check in local environment and CI.
- TF-005: Hardened minimal CI and branch protection instructions. Acceptance: minimal permissions; untrusted PRs do not receive publish/sign privileges.

## M1 — OCI Explorer (Gate: protocol + negative tests)
- TF-101: OCI conceptual fixtures: image manifest, index, descriptor/blob; verify hash raw bytes.
- TF-102: HTTPX registry transport: GET/HEAD, Accept headers, bearer auth challenge, timeouts, bounds and error taxonomy.
- TF-103: Resolve tag to digest; verify expected manifest digest; inspect media types, platform descriptors, index vs manifest.
- TF-104: OCI 1.1 referrers API; handle unsupported API and registry differences without silently trusting fallback.
- TF-105: CLI `inspect` JSON + human output; integration tests against temporary local registry.

## M2 — Signed Build (Gate: third-party crypto verification of a published immutable digest)
- TF-201: Small harmless sample app with pinned build dependencies and rootless image build.
- TF-202: Minimal GitHub Actions publishing workflow; isolated publish privileges, immutable pinning, GHCR digest capture.
- TF-203: Cosign keyless signing with exact authorized OIDC identity/issuer documented.
- TF-204: Generate SPDX SBOM (Syft); connect to artifact and verify its authenticity as configured.
- TF-205: Emit provenance using trustworthy supported builder mechanism; verify subject digest/source/builder and document assurance limits.

## M3 — TrustForge Gate / v0.1.0 (Gate: ALLOW positive + default DENY negative cases)
- TF-301: Trusted Cosign verification adapter, strict errors and parsed authenticated claims.
- TF-302: Provenance normalization and subject/source/workflow/builder matching.
- TF-303: OPA development/production rules with explicit DENY and policy fixture tests.
- TF-304: CLI verify/explain with canonical JSON decision report, diagnostic reason codes, tool/policy versions.
- TF-305: End-to-end release tests (wrong signer, altered digest, missing evidence, broken attestation); publish v0.1.0 after review.

## M4 — Adversarial Lab / v0.2.0 (Gate: >=10 reproducible isolated scenarios)
- TF-401: Scenario harness with expected decision matrix and fixture fixtures.
- TF-402: Tag substitution, artifact mismatch, unsigned image, unauthorized signer/workflow, unauthenticated claims, missing SBOM/provenance.
- TF-403: Malformed registry metadata, oversized responses, bogus media types, revoked/denied digest by policy, TOCTOU test.
- TF-404: Evidence report and documented false confidence / residual risks; publish v0.2.0.

## M5 — bootc Verified Updates / v0.3.0 (Gate: verified update, denied unauthorized update, rollback)
- TF-501: KVM/libvirt Fedora preflight and disposable bootc VM setup; storage and SELinux assessment.
- TF-502: Build and stage verified bootc OCI image; configure explicit image trust policy.
- TF-503: Enforce digest-locked update and validation by OS pull mechanism, not CLI-only precheck.
- TF-504: Controlled failed upgrade, rollback, audit and published reproducible demo; publish v0.3.0.

## Definition of Done (every issue)
- Scoped PR and linked issue; all acceptance tests automated where possible.
- Ruff, mypy, pytest, security-negative tests appropriate to feature.
- Reports of actual commands/results, not invented evidence.
- Docs/ADRs/status updated when affected.
- No unauthorized new dependency, host mutation, secret, policy bypass or scope expansion.

## Release criteria
M3: `v0.1.0`; M4: `v0.2.0`; M5: `v0.3.0`. Versions are milestones, not dates.
