# Architecture Decision Records — TrustForge
All decisions dated 2026-10-27; status ACCEPTED AS DESIGN BASELINE, not yet implemented or environment-validated.

| ID | Decision | Rationale | Revisit when |
|---|---|---|---|
| ADR-001 | Python modular monolith + CLI first | Inspectable learning, tight test surface; no premature orchestration | Requirements demand multiuser API |
| ADR-002 | Fedora Atomic + dedicated Distrobox `trustforge-dev` | Keeps host immutable and toolchains independent | Container compatibility or rootless limitations |
| ADR-003 | Podman rootless + local OCI Registry first, GHCR for publication | Local reproducibility and realistic registry workflow | Registry feature differences block required tests |
| ADR-004 | Educational HTTPX OCI Distribution client | Learn media types, authentication, byte-level digests and referrers | Parser complexity threatens security; keep tight scope |
| ADR-005 | Delegate crypto verification to Cosign/Sigstore, keyless identity restricted | Avoid bespoke cryptography; authenticate claims | New format/tool version mandates adapter change |
| ADR-006 | Verify in-toto/SLSA subject and authorized source/builder | Provenance exists only as useful authenticated evidence | New SLSA specification or threat model |
| ADR-007 | OPA/Rego default-DENY authorization | Policies independent from crypto implementation | Embedded evaluator required for offline use |
| ADR-008 | End-to-end digest pinning, no tag-driven promotion | Avoid tag substitution and verify/use inconsistency | Explicit content promotion design established |
| ADR-009 | GitHub is source of truth; issues + PRs + AGENTS.md; human review | Durable knowledge and AI-assisted development auditability | Orchestration needs change |
| ADR-010 | KVM/libvirt/bootc deferred to M5 | Avoid coupling OCI foundation with OS virtualization | M5 hardware or policy limitations |
| ADR-011 | No Kubernetes, UI, DB, LLM, GPU in v0.1 | Security guarantees first | New user-facing need |
| ADR-012 | Python 3.13 proposed with uv; pinned external tool versions at M0 | Reproducible toolchain with dependency compatibility check | Tested toolchain suggests better supported version |

## ADR template
- Context and threat/constraint
- Decision
- Alternatives rejected
- Consequences and security impact
- Verification/evidence
- Status/date
