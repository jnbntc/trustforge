# M1 public metadata interoperability — 2026-10-28

These are actual manual installed-CLI HTTPS observations, separate from offline tests. Only public manifests/indices and anonymous token endpoints were queried. No configs, layer blobs, OCI images, credentials or runtime were used. Responses are observations of mutable tags, not publisher authenticity or deployment authorization.

## Integrated inspector

Reviewed merges used squash with expected head SHA:

| PR | Scope | Squash commit |
|---|---|---|
| #31 | Governance documentation | 39b92af9d429d4116b2006683ff7b93360c17e5f |
| #35 | OCI primitives | 3ac0b6cfe5966ed6f0ba9fcbd1b15f2daf55c7da |
| #36 | HTTPS/Bearer and CLI | 51e46f9d8fce61218abdcf4841453660bfd051dd |

#36 was reduced to its ten own files and one commit on #35's actual squash, with governance retained. [Fresh PR CI](https://github.com/jnbntc/trustforge/actions/runs/40692588943) checked head f3d78a08c8886a5be069dd0ff571235138fde352 merged into base 3ac0b6cfe5966ed6f0ba9fcbd1b15f2daf55c7da: 177 tests and all quality/distribution checks passed on Python 3.13.16. [Final main CI](https://github.com/jnbntc/trustforge/actions/runs/40692755282) also passed on 51e46f9d8fce61218abdcf4841453660bfd051dd, Python 3.13.17, 177 tests.

## Real root/index observations

CLI installed in an isolated Python 3.14.8 environment from integrated main. A passive HTTPTransport observer recorded method, host/path, status, content type, registry digest and presence of Bearer (boolean only). It delegated unchanged to the real TLS transport; no MockTransport, response substitution or token/body logging occurred. The observer and raw public metadata records remain local; this document publishes only the allowlisted summary.

Each tag query and its second query by the returned immutable digest exited 0. All six returned OCI image indices, media type `application/vnd.oci.image.index.v1+json`. Raw-byte SHA-256 equalled the independently observed Docker-Content-Digest on every query. Fourteen total GETs included the anonymous token exchanges; no blob endpoint was requested. No incompatibility or permissive fallback was needed.

| Reference | Computed and registry-header digest (both queries) | Connection/authentication | Declared platforms |
|---|---|---|---|
| registry-1.docker.io/library/alpine:latest | sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a | TLS; 401, anonymous auth.docker.io token 200, manifest 200 | linux/amd64, linux/arm/v6, linux/arm/v7, linux/arm64/v8, linux/386, linux/ppc64le, linux/riscv64, linux/s390x; 8 unknown/unknown descriptors |
| quay.io/fedora/fedora-toolbox:44 | sha256:f34ce56c89da79683c4309d7a25c377d8bebaa3a5446956eb0b9b18d7fe72608 | TLS; direct anonymous 200 | linux/arm64, linux/ppc64le, linux/s390x, linux/amd64 |
| ghcr.io/astral-sh/uv:0.13.6 | sha256:af22a52f5eafef3d78e551599d405c02df61919d18028f0cea8eda93bc9986d0 | TLS; 401, same-origin anonymous token 200, manifest 200 | linux/amd64, linux/arm64; 2 unknown/unknown descriptors |

`unknown/unknown` entries are reported as supplied, without inferring runnable platforms or authentic attestations. All listed platforms are index claims. A successful metadata digest check does not verify signatures, provenance, layer/config content or compatibility with a host.

## Reproduce intentionally

From a reviewed installation (network access is intentional; this is not a CI test):

```bash
trustforge oci inspect registry-1.docker.io/library/alpine:latest --json
trustforge oci inspect registry-1.docker.io/library/alpine@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a --json
trustforge oci inspect quay.io/fedora/fedora-toolbox:44 --json
trustforge oci inspect quay.io/fedora/fedora-toolbox@sha256:f34ce56c89da79683c4309d7a25c377d8bebaa3a5446956eb0b9b18d7fe72608 --json
trustforge oci inspect ghcr.io/astral-sh/uv:0.13.6 --json
trustforge oci inspect ghcr.io/astral-sh/uv@sha256:af22a52f5eafef3d78e551599d405c02df61919d18028f0cea8eda93bc9986d0 --json
```

This snapshot does not promise that tags, availability, authentication behavior or rate limits will stay unchanged. HEAD, local-registry integration, negative live TLS/auth corpora, referrers, private access and crypto interoperability remain unverified/outside this sprint. TF-003 remains open and independent.

## New TF-103 platform draft: real installed-wheel observations

These six additional runs used the wheel rebuilt from sdist and installed into a fresh isolated environment, outside the source checkout. Every command requested an immutable index with --platform linux/amd64 or linux/arm64. Each exited 0; the child raw-byte digest matched its index descriptor and observed registry header, with exact descriptor size and media type. These results apply to the proposed code, not yet main.

| Provider | Requested platform | Declared selected platform | Child manifest SHA-256 (also registry header) |
|---|---|---|---|
| docker | linux/amd64 | linux/amd64 | sha256:c26612752c78b18faacd63c7d50f4592c2e7b0f25e0e20e82bd74e465c57ab0d |
| docker | linux/arm64 | linux/arm64/v8 | sha256:e311ae748be7f56ae5cba304bc488f0786df68ee507513f654a5cc8597cffb42 |
| quay | linux/amd64 | linux/amd64 | sha256:501a91dae4c81bff2ac2b3a97f45bcb7e42a720b2c06f2b2ae7d592229d11b5c |
| quay | linux/arm64 | linux/arm64 | sha256:ac733daa29ed64982d65600a12ed81b9b9a7d940db546a8ed0d699e45c55fd68 |
| ghcr | linux/amd64 | linux/amd64 | sha256:8b7774a14bb3abde914fda03efcb83f1f7e9163124e5c13e7fb4cc825293f5fa |
| ghcr | linux/arm64 | linux/arm64 | sha256:d17f32b62c2666c5d60e114bc797ce232753aa8b6b44b35dd7a3d979ab27dc89 |

Each child was an application/vnd.oci.image.manifest.v1+json. Docker Hub/GHCR performed independent anonymous token exchanges for root and child; Quay needed none. Twenty-eight additional GETs fetched only the six root indices, six children and necessary anonymous tokens/retries. No platform/config authenticity is inferred.

Local proposed-code validation: Python 3.14.8, 221 pytest cases, Ruff check/format, strict mypy (18 source/test modules), uv lock check, wheel/sdist/rebuilt wheel and clean installed CLI help all PASS. CI uses Python 3.13; its exact PR result is reported in the PR. A newly introduced Rich help markup error was caught by the installed-wheel smoke check, fixed, and covered by test_subcommand_help_renders_platform_option. No real-registry incompatibility required loosening security controls.
