# HEAD metadata observations — TF-102

`trustforge oci head REFERENCE --json` observes manifest headers by tag or SHA-256 digest. It never reads a HEAD response body and never performs an implicit manifest GET. An anonymous Bearer challenge may cause one token GET and one HEAD retry of the original URL.

The JSON contract is separate from inspect: schema_version=1, operation=head, reference, resolved_reference, digest, digest_source=registry_header, media_type, size_bytes, requested_digest_matches and content_integrity_verified=false. Matching a requested digest compares two claims; it does not hash content. Inspect's existing JSON semantics are unchanged. No signature/authenticity/deployment claim is issued.

The adapter shares inspect's bounded request implementation and anonymous auth parser: TLS verification, same origin/port (with the existing exact Docker auth exception), bound service/pull scope, no redirects, cookies or ambient credentials, and a shared cooperative 30 s budget. Up to three requests; manifest size header <=4 MiB, token response <=64 KiB. HEAD bodies, including error bodies, are closed without iteration. Runtime rejects methods other than GET/HEAD.

This command deliberately requires valid Docker-Content-Digest, Content-Length and a supported Content-Type to produce a complete observation. OCI Distribution 1.1 recommends the digest/length headers rather than mandating them: registries omitting them receive MISSING_DIGEST/MISSING_LENGTH, not an invented value or content-verification claim. Malformed/duplicate length or digest claims, digest mismatch, unknown media and compression fail closed. Header size is an observation, not a measured body size. Exit/error JSON follows inspect's 0/2/3/4/5/6 taxonomy.

```bash
trustforge oci head quay.io/fedora/fedora-toolbox:44 --json
# Use the digest returned by an independently checked inspect operation:
trustforge oci inspect quay.io/fedora/fedora-toolbox:44 --json
trustforge oci head quay.io/fedora/fedora-toolbox@sha256:f34ce56c89da79683c4309d7a25c377d8bebaa3a5446956eb0b9b18d7fe72608 --json
```

These network commands are opt-in. CI performs only offline fixtures/MockTransport. Negative tests prove bodies are never consumed and cover malformed/missing headers, auth retry/denial/origin, cookies, HTTP errors, redirects, CLI JSON/human/help, and original inspect/platform regressions.

Source: [OCI Distribution v1.1.1, checking content existence](https://github.com/opencontainers/distribution-spec/blob/v1.1.1/spec.md#checking-if-content-exists-in-the-registry). TF-003 remains open; this draft does not authorize OCI images, blobs, builds, publication or infrastructure changes.

## Actual public observations — 2026-10-28

Installed CLI in isolated Python 3.14.8: independent verified GET plus HEAD by tag and immutable digest on Docker Hub, Quay and GHCR, nine commands exit 0. All six HEAD observations matched GET digest, media type and byte size; content_integrity_verified stayed false. Passive real-transport tracing recorded no response bodies or token values. Docker/GHCR used anonymous Bearer; Quay responded directly. No blob endpoint occurred.

| Reference | Digest from HEAD, equal to independent GET hash | Declared/measured bytes |
|---|---|---|
| registry-1.docker.io/library/alpine:latest | sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a | 9218 |
| quay.io/fedora/fedora-toolbox:44 | sha256:f34ce56c89da79683c4309d7a25c377d8bebaa3a5446956eb0b9b18d7fe72608 | 1413 |
| ghcr.io/astral-sh/uv:0.13.6 | sha256:af22a52f5eafef3d78e551599d405c02df61919d18028f0cea8eda93bc9986d0 | 2195 |

All media types were application/vnd.oci.image.index.v1+json. Tags and availability may change; this is narrow interoperability, not universal conformance. Local quality: 252 offline pytest cases, Ruff/format, strict mypy and lock check passed. Python 3.13 and distribution checks are also covered by the PR CI; see its exact final run in the PR.
