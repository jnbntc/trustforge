# OCI Referrers discovery — TF-104

```bash
trustforge oci referrers quay.io/fedora/fedora-toolbox:44 --json
trustforge oci referrers ghcr.io/sigstore/cosign/cosign@sha256:0f06154836d2de34f887a5c273506d52ca43edaa1d9e53e6510fa78a48f69c2d --artifact-type application/vnd.dev.sigstore.bundle.v0.3+json --json
```

These public HTTPS commands are intentional opt-in network operations. CI is offline. No engine, blob/config/layer/referrer payload, signature tool, private credential or registry write is used. HEAD #38, Referrers #39 and bounded pagination #40 are integrated on main 297d3290e32e3f0aea56a91abaa6037d9174c250 after authorized review and squash integration. Real pagination remains unverified.

## Subject and list contract

A tag is resolved once through the existing manifest GET/parser, hashing exact bytes and checking the registry digest header when supplied. A supplied SHA-256 digest is used directly; this does not check that the subject exists. Query exactly /v2/REPOSITORY/referrers/DIGEST on the original HTTPS registry. Subject resolution is reported as manifest_get or supplied_digest.

Successful JSON has schema_version=1, operation=referrers, reference, subject_reference/digest/resolution, source, api_status, status (listed/empty), artifact_type_filter, referrers, list_digest/list_size_bytes and digest_header_verified. Each descriptor preserves mediaType, digest, size and optional artifactType, annotations/platform. Unknown extension URLs/data are ignored and never followed. The existing inspect JSON is unchanged.

The list hash describes only the response bytes, not the subject or referrer contents. association_verified=false and authenticity_verified=false always. A registry listing a signature, SBOM, attestation or bundle does not authenticate it; no child/payload is fetched to corroborate its subject. Empty means only that the returned, possibly filtered list contained no matches. No cryptographic/deployment decision is issued.

## Standard fallback and uncertainty

On API 404 only, query the same repository's standard OCI tag sha256-HEX, as required by [Distribution v1.1.1 unavailable referrers API](https://github.com/opencontainers/distribution-spec/blob/v1.1.1/spec.md#unavailable-referrers-api). No .sig/.att or third-party tag convention is tried. api_status=not_found with source=oci_tag_schema distinguishes a successful fallback from the API. A 404 alone does not prove the entire provider lacks support.

If that standard tag is also 404, fail REFERRERS_UNAVAILABLE (exit 6, empty stdout, error JSON on stderr). Do not call it an empty list or confirmed absence: unsupported/missing repository/list cannot be distinguished. Invalid fallback bodies fail validation rather than the specification's suggested assumption of no referrers; this conservative choice preserves uncertainty. Other HTTP errors, including 405/501, never trigger a fallback or an empty success.

## Filtering, bounds and limitations

--artifact-type accepts an exact valid media type, passed as artifactType to the API. Registry-side filtering is optional, so every result is also filtered locally. If OCI-Filters-Applied claims artifactType, every descriptor must match; unexpected/duplicate filters fail. Fallback filtering is local only. A valid empty filtered list says nothing about other artifact types.

Reuse inspect's bounded HTTPS request/auth helpers, TLS/origin/port/service/pull-scope checks, redirect refusal, cookie clearing, token limits and no ambient credentials. Each subject/API/fallback operation has at most one anonymous challenge/token/retry. At most five API pages, 4 MiB combined raw referrers-index bytes, 1024 combined observed descriptors, and one shared cooperative 30 s budget. Subject resolution remains separately capped at 4 MiB and each token response at 64 KiB. Including independent token exchanges/retries, a tag plus five pages uses at most 18 requests; the first-404 standard fallback path uses at most nine. Error/404 bodies are not consumed. Requested realm/descriptor URLs cannot redirect requests elsewhere.

Only OCI image-index responses are accepted; their raw digest must match a digest header when provided. Malformed/duplicate/non-finite JSON, invalid digests/sizes/annotations/artifact types, duplicate descriptor digests and inconsistent filtering are errors. Missing optional digest headers are reported, not invented. Descriptor media types/extensions can be observed without fetching them.

Pagination #40 is integrated as bounded traversal of one immutable API endpoint, not a general crawler. A single unambiguous rel=next Link is parsed according to the RFC Link syntax. Query-relative, absolute-path and absolute HTTPS targets are validated against the same scheme, effective port, host and exact repository/referrers/subject-digest path. Only cursor query names n, last, cursor, next and the original artifactType are supported. Unknown cursor schemes fail explicitly; their spelling is not standardized by OCI. Values are bounded ASCII; n is 1..1024. Duplicate params, userinfo, fragments, protocol-relative URLs, path escapes/dot segments, anchors, multiple Link values, changed filters and normalized cycles fail before another request. An omitted filter is restored locally; a different or newly introduced filter is rejected.

Only validated query values are sent to the original constructed endpoint. Each page uses the existing TLS/auth/redirect policy independently, hashes its exact bytes and validates index/descriptors/filter claims. Global bounds cover all pages before success; repeated digest entries (even identical) and inconsistent entries fail. A subsequent 404 never switches to fallback. Standard fallback tags are one bounded index and cannot supply pagination links. HTTP/validation/limit failures return no partial successful report.

Single-page schema_version=1 JSON remains unchanged. Multi-page schema_version=1 adds list_digest_scope=first_page and pagination: pages_queried, observed_descriptors (before local filtering), returned_descriptors, total_size_bytes and per-page digest/size_bytes/digest_header_verified. Existing list_digest/list_size_bytes/digest_header_verified describe the first page only, explicitly not an aggregate digest. The referrers array contains the fully collected and locally filtered descriptors. No synthetic hash of merged JSON is invented. Rich shows page and descriptor counts.

This is a conservative Link subset: only one next relation is accepted; anchors, ambiguous link sets, unknown cursor names and non-ASCII cursors fail closed. No complete Distribution/provider conformance or authenticity is claimed. Sources: [Distribution 1.1.1 pagination](https://github.com/opencontainers/distribution-spec/blob/v1.1.1/spec.md#listing-referrers), [RFC 8288 Link serialization](https://www.rfc-editor.org/rfc/rfc8288.html#section-3), [ORAS notes on implementation-specific pagination sizing](https://github.com/oras-project/oras-go/blob/main/registry/remote/repository.go).

Protocol source: [Distribution v1.1.1 listing referrers](https://github.com/opencontainers/distribution-spec/blob/v1.1.1/spec.md#listing-referrers). The optional artifactType for an index referrer may be omitted. A required wire field cannot be substituted with its internal Python alias.

## Validation

Integrated pagination main 297d3290e32e3f0aea56a91abaa6037d9174c250 passed [post-merge CI](https://github.com/jnbntc/trustforge/actions/runs/40809965768) on Python 3.13.17 with 372 offline tests and quality/lock/distribution/install checks. Local Python 3.14.8 also passed 372 offline tests, including all main inspect/platform/HEAD/Referrers regressions; Ruff check/format, strict mypy and lock consistency PASS. Mocks cover API/fallback, tag binding, auth scopes/failures, malformed/oversized/duplicate lists, digest headers, filtering, unsafe links, aliases, CLI exits and shared deadlines. Python 3.13 and final distribution results are recorded in the PR. CI and offline pagination fixtures do not demonstrate live pagination interoperability.

Real CLI observations on 2026-10-28, separate from mocks:

| Public reference / scope | API and standard fallback | Actual result |
|---|---|---|
| registry-1.docker.io/library/alpine:latest, immutable root and amd64 child | API 200 with anonymous Bearer | Empty lists, exit 0 |
| quay.io/fedora/fedora-toolbox:44, immutable root and amd64 child | API 200 directly | Empty lists, exit 0 |
| ghcr.io/astral-sh/uv:0.13.6, immutable root and amd64 child | API 404, standard OCI tag 404 after anonymous Bearer | REFERRERS_UNAVAILABLE, exit 6; no empty-success claim |
| ghcr.io/sigstore/cosign/cosign:v3.1.4 | Subject GET resolved sha256:0f06154836d2de34f887a5c273506d52ca43edaa1d9e53e6510fa78a48f69c2d; API 404, standard tag 200 | Two descriptors declaring application/vnd.dev.sigstore.bundle.v0.3+json, exit 0 |

The Sigstore reference is an observed public registry name, not cryptographic proof of publisher identity. Bundles/keys/certificates were not fetched or verified, and no Cosign command ran. No real incompatible response required weakening the client. Raw public metadata/traces stay local; only this allowlisted summary is published. Provider behavior and tags can change.

Three additional real filtered queries by immutable subject digest also passed (exit 0): Docker Hub and Quay returned empty matching lists; GHCR standard fallback retained both declared Sigstore bundle descriptors. Filtering used application/vnd.dev.sigstore.bundle.v0.3+json; the fallback GET carried no artifactType query and filtering occurred locally.

## Repeated interoperability after integration

On 2026-10-29 the installed CLI from actual merged main 297d3290e32e3f0aea56a91abaa6037d9174c250 repeated the same 17 public commands below: 16 exits 0 and the expected GHCR/uv REFERRERS_UNAVAILABLE/exit 6. Digests were unchanged, HEAD matched independent GET and amd64 child checks passed. Docker/Quay returned empty API lists; Sigstore/GHCR standard fallback returned two declared bundles. No Link was observed. These real requests used the unmodified main transport, not the header-hardening draft or MockTransport. No payloads or crypto tools were used.

On 2026-10-28 the then-proposed installed CLI repeated 17 public metadata commands: three GET tag inspections, six HEAD tag/digest observations, three immutable amd64 child selections, three immutable Referrers queries and two Sigstore fallback/filter queries. Sixteen exited 0; GHCR/uv Referrers again exited 6 with REFERRERS_UNAVAILABLE rather than an invented empty list. HEAD digest/media/size matched independent GET; child size/digest/media matched its index descriptor. No response in these cases contained Link. No real paginated public reference was safely identified in a bounded primary-source search; live pagination is NOT VERIFIED, while multi-page positive/security-negative paths are covered offline. No artifacts were created to manufacture a test. Bundle associations/authenticity remain unverified and no payload was fetched.
