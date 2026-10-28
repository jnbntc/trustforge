# OCI primitives — TF-101 / start of TF-103

Pure parsing/models only, without network, runtime or Gate M3. TF-101 (#35) and its companion TF-102 transport/CLI (#36) are integrated; neither completes all of M1.

## Supported references
Names follow the Distribution path/tag grammar with Docker Hub normalization:
- alpine -> registry-1.docker.io/library/alpine:latest
- docker.io/library/alpine:latest -> registry-1.docker.io/library/alpine:latest
- quay.io/fedora/fedora-toolbox:44
- ghcr.io/astral-sh/uv:0.13.6
- registry.example:5443/team/image@sha256:<64 lowercase hex>

Schemes, userinfo, whitespace/control characters, queries/fragments, percent escapes and ambiguous paths are rejected. Repository paths are lowercase; tags may contain uppercase. Explicit ports must be 1..65535. IPv6/IDNA and digest algorithms other than SHA-256 are deliberately unsupported. A supplied digest takes precedence over a tag; no claim is made that the tag currently points there.

## Metadata and integrity
parse_manifest accepts OCI image manifests/indices and Docker schema-2 manifests/lists. It requires schemaVersion=2 and typed required descriptors, nonnegative integer sizes and supported SHA-256 descriptor syntax. Content-Type parameters are ignored; body mediaType, when present, must agree with the header. OCI extension fields and unknown child-descriptor media types are tolerated, but not interpreted or followed. This is not a full OCI conformance validator.

The digest is computed over exact received UTF-8 JSON bytes, before parsing; it is compared independently with the requested digest and Docker-Content-Digest when supplied. An absent header is recorded, not replaced by invented server evidence. Duplicate JSON keys, non-finite values, malformed structures and mismatches deny. Pure parsing also caps metadata at 4 MiB, layers at 4096 and index entries at 1024.

An index digest identifies the index bytes, not a child architecture manifest. Platform data comes from index descriptors; a standalone manifest's platform remains unknown. This parser fetches nothing. The [inspector](OCI_EXPLORER.md) may explicitly fetch one selected child manifest; config/layers/subject/external descriptor URLs remain untouched.

Integrity is not authenticity: no signature, source/builder approval, vulnerability assessment or deployment permission is implied.

## Fixtures and tests
Small manifest/index JSON files use illustrative descriptor digests and sizes, not real authenticated images. blob.txt is an opaque local fixture with an independently recorded SHA-256; no image layer is downloaded or executed. Tests check raw-byte hashing, changes caused by reserialization, digest substitution, malformed/duplicate JSON, schema coercion, media negotiation, typed descriptors and reference grammar. No test uses internet.

## Primary references
- [Distribution reference grammar](https://github.com/distribution/reference/blob/main/reference.go) and [normalization](https://github.com/distribution/reference/blob/main/normalize.go).
- [OCI Distribution: manifests and digest/header rules](https://github.com/opencontainers/distribution-spec/blob/v1.1.1/spec.md#pulling-manifests).
- [OCI index and platform descriptors](https://specs.opencontainers.org/image-spec/image-index/?v=v1.1.1), [descriptors](https://specs.opencontainers.org/image-spec/descriptor/).

TF-101 fixtures/primitives and initial TF-103 digest handling are integrated. [Separate manual real-registry observations](M1_INTEROPERABILITY.md) do not turn fixtures into authenticated images. TF-104 and local-registry integration remain pending.
