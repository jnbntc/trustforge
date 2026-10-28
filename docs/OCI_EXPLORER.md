# OCI Explorer — first read-only implementation (TF-102/103/105)

The TF-101 primitives (#35) and TF-102 HTTPS/CLI (#36) are integrated. Explicit platform selection is the next TF-103 draft, independent of the Distrobox workspace/bootstrap and TrustForge Gate M3. M1 acceptance remains partial.

## Run from an installed reviewed checkout
```bash
uv sync --locked
uv run --no-sync trustforge oci inspect --help
uv run --no-sync trustforge oci inspect registry-1.docker.io/library/alpine:latest
uv run --no-sync trustforge oci inspect quay.io/fedora/fedora-toolbox:44 --json
uv run --no-sync trustforge oci inspect ghcr.io/astral-sh/uv:0.13.6 --json
```
Anonymous tag and immutable-digest queries against all three references passed on 2026-10-28; see [recorded interoperability](M1_INTEROPERABILITY.md). Tags are mutable observations. Pin the returned resolved_reference to request the same digest later; this is integrity, not authenticity.

## What is requested
Only HTTPS GET /v2/<repository>/manifests/<selector> and, per manifest if challenged, one anonymous token GET plus one retry. Accept negotiates OCI manifests/indices and Docker schema-2 manifests/lists. Default inspection reads only the root. Explicit --platform may additionally read one child manifest by digest from the same registry/repository. No blob/config/layer, referrers, pagination, engine or registry write occurs.

The reported digest hashes the exact response bytes; requested sha256 and Docker-Content-Digest are checked independently. Missing digest header is reported as digest_header_verified=false; local hashing still occurs. A mismatched/malformed header never becomes a silent fallback.

An index's digest identifies its index bytes; architecture descriptor digests identify different children. Platforms shown are descriptor claims only. A single manifest's platform is unknown because its config is not downloaded. Unknown extension fields/child media types are not followed. This is partial metadata inspection, not full OCI conformance or image verification.

## JSON and exit contract
Successful --json writes one schema_version=1 object to stdout with reference, resolved_reference, kind, media_type, digest, size_bytes, digest_header_verified and typed document. The document preserves OCI field names (mediaType, schemaVersion); operational report fields use snake_case.

With --platform, these root fields remain unchanged and a selection object is added: requested_platform, index_digest, manifest_digest, resolved_reference (child), descriptor and manifest (parsed child metadata). Without --platform no selection key is emitted. Root resolved_reference always identifies the index; selection.resolved_reference identifies its checked child.

Expected operation failures leave stdout empty and write schema_version=1/error/code/message to stderr. Messages omit raw registry/token bodies and exception URLs. Framework syntax errors (missing arguments/unknown options) retain Typer's usage output.
- 0: metadata inspected.
- 2: invalid reference/CLI input.
- 3: transport, redirect or timeout failure.
- 4: anonymous authentication unavailable/rejected.
- 5: metadata/digest/media/size/encoding failure.
- 6: HTTP errors, including RATE_LIMITED for 429.

No VERIFIED/ALLOW/deployment authorization is issued.

## Transport limits and trust boundaries
TLS validation stays enabled. No HTTP mode, insecure override, local Docker/Podman/netrc credentials, interactive login, client certificate or credential flag exists. trust_env=false disables ambient proxy/CA environment configuration. This also means custom enterprise proxies/CAs are unsupported here.

All redirects are rejected, including same-origin redirects; Location is never followed or printed. Cookies are discarded after each response. Bearer tokens remain in memory for one original manifest retry and are never placed in query parameters or reports.

Realm must be HTTPS with no userinfo/query/fragment/percent-encoded or ambiguous path. Default: same registry origin/port. The sole cross-origin exception is registry-1.docker.io -> https://auth.docker.io/token on port 443, service registry.docker.io. Other external auth providers are unsupported. Service must match the registry authority (or Docker's known service); requested scope is exactly repository:<requested-repository>:pull. Advertised broader/different scopes, duplicate/unknown challenge parameters, Basic/multiple challenges and malformed tokens fail closed. Conservative restrictions may reject otherwise legitimate registries; no permissive fallback is provided.

Manifest bytes: max 4 MiB each; selected child additionally bounded by its descriptor size. Token JSON: max 64 KiB, token value max 8192 characters. Streaming enforces actual bytes and validates declared size; compressed metadata is rejected. Error/401 bodies are not consumed. Default: at most three requests. Explicit selection: at most six, with independent authentication for each manifest and one shared 30 s budget. No automatic retry/backoff; rate limits require operator-controlled retry.

Connect/pool timeout is at most 5 s; network inactivity timeout at most 10 s; a cooperative 30 s budget is checked between responses/chunks. This is not hard process preemption or a guarantee about OS DNS timing. Reference parsing/model limits are described in OCI_MODELS.md.

A user-selected registry can resolve to a private address: this CLI is not an SSRF-isolation service or a public-network firewall. Only run reviewed references, especially if embedding the library behind a service later. No untrusted realm can select an arbitrary other origin.

## Validation and remaining scope
All automated tests are offline HTTPX MockTransport plus tiny local fixtures. They exercise actual adapter/parser/CLI code, not the internet. Tests cover Bearer origin/port/scope, token redaction, redirects at every stage, cookies/ambient auth, HTTP/429, timeouts/deadline, streamed/declared sizes, encodings, raw digests, schemas and JSON/CLI exits. A detected port-zero comparison ambiguity was removed before publishing; a regression rejects it.

Separate manual real-HTTPS CLI runs passed for the three named public artifacts (tag and digest), with raw-byte digests equal to registry headers. This is a narrow observation, not universal registry conformance or a real TLS-failure corpus. Automated CI remains offline. Local-registry integration, HEAD, nested-index traversal, referrers TF-104, private auth, SHA-512 and IPv6/IDNA remain pending.

Primary sources: [Distribution manifest endpoint](https://github.com/opencontainers/distribution-spec/blob/v1.1.1/spec.md#pulling-manifests), [Docker Bearer protocol](https://docs.docker.com/reference/api/registry/auth/), [HTTPX streaming](https://www.python-httpx.org/quickstart/#streaming-responses), [timeouts](https://www.python-httpx.org/advanced/timeouts/), [ambient environment](https://www.python-httpx.org/environment_variables/).

## Explicit platform selection (TF-103 draft)
```bash
uv run --no-sync trustforge oci inspect registry-1.docker.io/library/alpine:latest --platform linux/amd64 --json
uv run --no-sync trustforge oci inspect quay.io/fedora/fedora-toolbox:44 --platform linux/arm64
```
Selectors are lowercase os/architecture with an optional /variant, without aliases or host autodetection. An omitted variant may match one descriptor (for example arm64/v8); zero matches fails PLATFORM_NOT_FOUND and multiple matches fail AMBIGUOUS_PLATFORM, including duplicates. Specify the variant when it disambiguates. This inspector deliberately rejects ambiguity instead of applying the OCI index's suggested first-match behavior.

Only a direct OCI/Docker image-manifest descriptor with positive size <=4 MiB can be selected. Nested indices/unknown media types remain observable but are not traversed. The child URL is constructed from the original repository and descriptor SHA-256; descriptor urls/data/subject/config/layers are never followed. Exact bytes must match descriptor size, digest, media type and any registry digest header. A failure yields no partial successful report.

Standalone manifests fail PLATFORM_UNVERIFIABLE when selection is requested: determining their platform would require config access. Index platform labels, including os.version/features not evaluated here, are untrusted metadata claims, not proof of runtime compatibility. Matching metadata integrity does not authenticate the publisher or platform claim.

Sources: [OCI image-index platforms](https://github.com/opencontainers/image-spec/blob/v1.1.1/image-index.md), [descriptor digest/size verification](https://github.com/opencontainers/image-spec/blob/v1.1.1/descriptor.md#verification). The new platform draft requires human review; tests do not close issues or authorize image build/sign/publish/deploy.
