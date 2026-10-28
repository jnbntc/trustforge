# OCI Referrers discovery — TF-104

```bash
trustforge oci referrers quay.io/fedora/fedora-toolbox:44 --json
trustforge oci referrers ghcr.io/sigstore/cosign/cosign@sha256:0f06154836d2de34f887a5c273506d52ca43edaa1d9e53e6510fa78a48f69c2d --artifact-type application/vnd.dev.sigstore.bundle.v0.3+json --json
```

These public HTTPS commands are intentional opt-in network operations. CI is offline. No engine, blob/config/layer/referrer payload, signature tool, private credential or registry write is used. This is an independent draft on main after #37; HEAD #38 is separate and is not required.

## Subject and list contract

A tag is resolved once through the existing manifest GET/parser, hashing exact bytes and checking the registry digest header when supplied. A supplied SHA-256 digest is used directly; this does not check that the subject exists. Query exactly /v2/REPOSITORY/referrers/DIGEST on the original HTTPS registry. Subject resolution is reported as manifest_get or supplied_digest.

Successful JSON has schema_version=1, operation=referrers, reference, subject_reference/digest/resolution, source, api_status, status (listed/empty), artifact_type_filter, referrers, list_digest/list_size_bytes and digest_header_verified. Each descriptor preserves mediaType, digest, size and optional artifactType, annotations/platform. Unknown extension URLs/data are ignored and never followed. The existing inspect JSON is unchanged.

The list hash describes only the response bytes, not the subject or referrer contents. association_verified=false and authenticity_verified=false always. A registry listing a signature, SBOM, attestation or bundle does not authenticate it; no child/payload is fetched to corroborate its subject. Empty means only that the returned, possibly filtered list contained no matches. No cryptographic/deployment decision is issued.

## Standard fallback and uncertainty

On API 404 only, query the same repository's standard OCI tag sha256-HEX, as required by [Distribution v1.1.1 unavailable referrers API](https://github.com/opencontainers/distribution-spec/blob/v1.1.1/spec.md#unavailable-referrers-api). No .sig/.att or third-party tag convention is tried. api_status=not_found with source=oci_tag_schema distinguishes a successful fallback from the API. A 404 alone does not prove the entire provider lacks support.

If that standard tag is also 404, fail REFERRERS_UNAVAILABLE (exit 6, empty stdout, error JSON on stderr). Do not call it an empty list or confirmed absence: unsupported/missing repository/list cannot be distinguished. Invalid fallback bodies fail validation rather than the specification's suggested assumption of no referrers; this conservative choice preserves uncertainty. Other HTTP errors, including 405/501, never trigger a fallback or an empty success.

## Filtering, bounds and limitations

--artifact-type accepts an exact valid media type, passed as artifactType to the API. Registry-side filtering is optional, so every result is also filtered locally. If OCI-Filters-Applied claims artifactType, every descriptor must match; unexpected/duplicate filters fail. Fallback filtering is local only. A valid empty filtered list says nothing about other artifact types.

Reuse inspect's bounded HTTPS request/auth helpers, TLS/origin/port/service/pull-scope checks, redirect refusal, cookie clearing, token limits and no ambient credentials. Each subject/API/fallback operation has at most one anonymous challenge/token/retry. At most nine GETs and one shared cooperative 30 s budget; each metadata response <=4 MiB and each index <=1024 descriptors. Error/404 bodies are not consumed. Requested realm/descriptor URLs cannot redirect requests elsewhere.

Only OCI image-index responses are accepted; their raw digest must match a digest header when provided. Malformed/duplicate/non-finite JSON, invalid digests/sizes/annotations/artifact types, duplicate descriptor digests and inconsistent filtering are errors. Missing optional digest headers are reported, not invented. Descriptor media types/extensions can be observed without fetching them.

Pagination is an explicit remaining limit: any Link header fails REFERRERS_PAGINATED with no partial result, and no server-supplied link is followed. This draft therefore does not claim complete Distribution conformance or final TF-104 acceptance. Bounds/private auth/nested metadata are not silently relaxed for compatibility.

Protocol source: [Distribution v1.1.1 listing referrers](https://github.com/opencontainers/distribution-spec/blob/v1.1.1/spec.md#listing-referrers). The optional artifactType for an index referrer may be omitted. A required wire field cannot be substituted with its internal Python alias.

## Validation

Local Python 3.14.8: 272 offline tests PASS, including the prior 222 inspect/platform tests; Ruff check/format, strict mypy and lock consistency PASS. Mocks cover API/fallback, tag binding, auth scopes/failures, malformed/oversized/duplicate lists, digest headers, filtering, unsafe links, aliases, CLI exits and shared deadlines. Python 3.13 and distribution results are linked in the PR once complete.

Real CLI observations on 2026-10-28, separate from mocks:

| Public reference / scope | API and standard fallback | Actual result |
|---|---|---|
| registry-1.docker.io/library/alpine:latest, immutable root and amd64 child | API 200 with anonymous Bearer | Empty lists, exit 0 |
| quay.io/fedora/fedora-toolbox:44, immutable root and amd64 child | API 200 directly | Empty lists, exit 0 |
| ghcr.io/astral-sh/uv:0.13.6, immutable root and amd64 child | API 404, standard OCI tag 404 after anonymous Bearer | REFERRERS_UNAVAILABLE, exit 6; no empty-success claim |
| ghcr.io/sigstore/cosign/cosign:v3.1.4 | Subject GET resolved sha256:0f06154836d2de34f887a5c273506d52ca43edaa1d9e53e6510fa78a48f69c2d; API 404, standard tag 200 | Two descriptors declaring application/vnd.dev.sigstore.bundle.v0.3+json, exit 0 |

The Sigstore reference is an observed public registry name, not cryptographic proof of publisher identity. Bundles/keys/certificates were not fetched or verified, and no Cosign command ran. No real incompatible response required weakening the client. Raw public metadata/traces stay local; only this allowlisted summary is published. Provider behavior and tags can change.

Three additional real filtered queries by immutable subject digest also passed (exit 0): Docker Hub and Quay returned empty matching lists; GHCR standard fallback retained both declared Sigstore bundle descriptors. Filtering used application/vnd.dev.sigstore.bundle.v0.3+json; the fallback GET carried no artifactType query and filtering occurred locally.
