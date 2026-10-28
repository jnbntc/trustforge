"""OCI primitives tested against deterministic metadata, without network or blobs."""

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from trustforge.oci.digest import digest_bytes
from trustforge.oci.errors import OciError
from trustforge.oci.models import (
    DOCKER_INDEX,
    DOCKER_MANIFEST,
    MAX_MANIFEST_BYTES,
    OCI_INDEX,
    OCI_MANIFEST,
    ImageIndex,
    ImageManifest,
    parse_manifest,
)
from trustforge.oci.reference import parse_reference

FIXTURES = Path(__file__).parent / "fixtures" / "oci"


def test_opaque_blob_fixture_digest_is_byte_exact() -> None:
    raw = (FIXTURES / "blob.txt").read_bytes()
    expected = "sha256:53162e868880f54e83888a26ab6f9870f8db98fda360b15e65e584688979ed47"
    assert digest_bytes(raw) == expected
    assert digest_bytes(raw.rstrip()) != expected


@pytest.mark.parametrize(
    ("value", "canonical"),
    [
        ("alpine", "registry-1.docker.io/library/alpine:latest"),
        ("docker.io/alpine:3.22", "registry-1.docker.io/library/alpine:3.22"),
        ("index.docker.io/library/alpine", "registry-1.docker.io/library/alpine:latest"),
        ("user/image:Tag_1", "registry-1.docker.io/user/image:Tag_1"),
        (
            "registry-1.docker.io/library/alpine:latest",
            "registry-1.docker.io/library/alpine:latest",
        ),
        ("quay.io/fedora/fedora-toolbox:44", "quay.io/fedora/fedora-toolbox:44"),
        ("ghcr.io/astral-sh/uv:0.13.6", "ghcr.io/astral-sh/uv:0.13.6"),
        ("registry.example:5443/team/image:v1", "registry.example:5443/team/image:v1"),
        ("localhost:5443/team/a__b--c.d", "localhost:5443/team/a__b--c.d:latest"),
        ("REGISTRY.EXAMPLE/image", "registry.example/image:latest"),
        ("ghcr.io/team/image@sha256:" + "a" * 64, "ghcr.io/team/image@sha256:" + "a" * 64),
        ("ghcr.io/team/image:tag@sha256:" + "b" * 64, "ghcr.io/team/image@sha256:" + "b" * 64),
    ],
)
def test_reference_normalization(value: str, canonical: str) -> None:
    ref = parse_reference(value)
    assert ref.canonical == canonical
    assert (
        ref.manifest_url == f"https://{ref.registry}/v2/{ref.repository}/manifests/{ref.selector}"
    )


@pytest.mark.parametrize(
    "value",
    [
        "",
        " alpine",
        "alpine\n",
        "http://registry.io/a",
        "https://registry.io/a",
        "registry.io/a?secret=x",
        "registry.io/a#fragment",
        "registry.io/a%2fother",
        "user:password@registry.io/a",
        "registry.io//a",
        "registry.io/../a",
        "registry.io/Upper",
        "registry.io/a:",
        "registry.io/a:bad tag",
        "registry.io/a@" + "a" * 64,
        "registry.io/a@sha512:" + "a" * 128,
        "registry.io/a@sha256:" + "A" * 64,
        "registry.io/a@sha256:" + "a" * 63,
        "registry.io/a@sha256:" + "a" * 64 + "@bad",
        "registry.io:0/a",
        "registry.io:65536/a",
        "registry.io:bad/a",
        "registry.io./a",
        "-registry.io/a",
        "[::1]:5443/a",
        "regístro.io/a",
        "registry.io/a\\b",
        "registry.io/" + "a" * 256,
        "registry.io/a:" + "t" * 129,
    ],
)
def test_bad_reference_before_transport(value: str) -> None:
    with pytest.raises(OciError) as error:
        parse_reference(value)
    assert error.value.code == "INVALID_REFERENCE"
    assert error.value.exit_code == 2
    assert value not in str(error.value) or not value


@pytest.mark.parametrize(
    "fixture,media", [("manifest.json", OCI_MANIFEST), ("index.json", OCI_INDEX)]
)
def test_metadata_and_exact_bytes(fixture: str, media: str) -> None:
    raw = (FIXTURES / fixture).read_bytes()
    digest = "sha256:" + hashlib.sha256(raw).hexdigest()
    parsed = parse_manifest(
        raw, media + "; charset=utf-8", expected_digest=digest, advertised_digest=digest
    )
    assert parsed.digest == digest
    assert parsed.size_bytes == len(raw)
    assert parsed.digest_header_verified
    if fixture == "index.json":
        assert parsed.kind == "index" and isinstance(parsed.document, ImageIndex)
        assert [d.platform.architecture for d in parsed.document.manifests if d.platform] == [
            "amd64",
            "arm64",
        ]
        assert all(d.digest != parsed.digest for d in parsed.document.manifests)
    else:
        assert parsed.kind == "manifest" and isinstance(parsed.document, ImageManifest)
        assert len(parsed.document.layers) == 1
        assert parsed.document.config.digest != parsed.digest


def test_reserialization_is_not_the_wire_digest() -> None:
    raw = (FIXTURES / "manifest.json").read_bytes()
    reserialized = json.dumps(json.loads(raw), separators=(",", ":")).encode()
    assert raw != reserialized
    with pytest.raises(OciError, match="bytes"):
        parse_manifest(
            raw, OCI_MANIFEST, expected_digest="sha256:" + hashlib.sha256(reserialized).hexdigest()
        )


@pytest.mark.parametrize("claim", ["expected", "header", "both"])
def test_digest_substitution_denied(claim: str) -> None:
    raw = (FIXTURES / "index.json").read_bytes()
    with pytest.raises(OciError) as error:
        parse_manifest(
            raw,
            OCI_INDEX,
            expected_digest="sha256:" + "f" * 64 if claim in ("expected", "both") else None,
            advertised_digest="sha256:" + "e" * 64 if claim in ("header", "both") else None,
        )
    assert error.value.code == "DIGEST_MISMATCH"


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"[]",
        b"null",
        b"not json",
        b"\xff",
        b'{"schemaVersion":2,"schemaVersion":2}',
        b'{"schemaVersion":NaN}',
        b"{" * 1500,
    ],
)
def test_malformed_or_ambiguous_json(raw: bytes) -> None:
    with pytest.raises(OciError) as error:
        parse_manifest(raw, OCI_MANIFEST)
    assert error.value.code == "MALFORMED_MANIFEST"


@pytest.mark.parametrize(
    "mode",
    [
        "missing-config",
        "missing-layers",
        "size-bool",
        "size-string",
        "size-negative",
        "bad-digest",
        "bad-schema",
        "float-schema",
        "missing-platform-arch",
    ],
)
def test_descriptor_and_schema_validation(mode: str) -> None:
    data: dict[str, Any] = json.loads((FIXTURES / "manifest.json").read_bytes())
    if mode == "missing-config":
        del data["config"]
    if mode == "missing-layers":
        del data["layers"]
    if mode == "size-bool":
        data["config"]["size"] = True
    if mode == "size-string":
        data["config"]["size"] = "2"
    if mode == "size-negative":
        data["config"]["size"] = -1
    if mode == "bad-digest":
        data["layers"][0]["digest"] = "tag"
    if mode == "bad-schema":
        data["schemaVersion"] = 1
    if mode == "float-schema":
        data["schemaVersion"] = 2.0
    if mode == "missing-platform-arch":
        data["config"]["platform"] = {"os": "linux"}
    with pytest.raises(OciError) as error:
        parse_manifest(json.dumps(data).encode(), OCI_MANIFEST)
    assert error.value.code == "MALFORMED_MANIFEST"


@pytest.mark.parametrize(
    "media", ["", "application/json", "text/html", "application/vnd.unknown+json"]
)
def test_unknown_top_media_type_denied(media: str) -> None:
    with pytest.raises(OciError) as error:
        parse_manifest((FIXTURES / "index.json").read_bytes(), media)
    assert error.value.code == "UNSUPPORTED_MEDIA_TYPE"


def test_header_body_disagreement_denied() -> None:
    with pytest.raises(OciError) as error:
        parse_manifest((FIXTURES / "index.json").read_bytes(), OCI_MANIFEST)
    assert error.value.code == "MEDIA_TYPE_MISMATCH"


@pytest.mark.parametrize(
    "media,fixture", [(DOCKER_MANIFEST, "manifest.json"), (DOCKER_INDEX, "index.json")]
)
def test_docker_schema2_and_missing_optional_media_field(media: str, fixture: str) -> None:
    data = json.loads((FIXTURES / fixture).read_bytes())
    data["mediaType"] = media
    assert parse_manifest(json.dumps(data).encode(), media).media_type == media
    del data["mediaType"]
    parsed = parse_manifest(json.dumps(data).encode(), media)
    assert parsed.media_type == media
    assert not parsed.digest_header_verified


def test_extensions_and_unknown_index_descriptor_type_are_not_followed() -> None:
    data = json.loads((FIXTURES / "index.json").read_bytes())
    data["extension"] = {"not-interpreted": True}
    data["manifests"][0]["mediaType"] = "application/vnd.future.manifest"
    data["manifests"][0]["urls"] = ["https://untrusted.invalid/must-not-follow"]
    parsed = parse_manifest(json.dumps(data).encode(), OCI_INDEX)
    assert isinstance(parsed.document, ImageIndex)
    assert "urls" not in parsed.document.manifests[0].model_dump()
    assert parsed.document.manifests[0].media_type == "application/vnd.future.manifest"


def test_manifest_limit() -> None:
    with pytest.raises(OciError) as error:
        parse_manifest(b" " * (MAX_MANIFEST_BYTES + 1), OCI_MANIFEST)
    assert error.value.code == "RESPONSE_TOO_LARGE"
