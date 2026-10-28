"""Bounded, typed metadata models; descriptors are observations, not downloaded blobs."""

import json
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, ValidationError

from trustforge.oci.digest import digest_bytes, validate_digest
from trustforge.oci.errors import OciError

OCI_MANIFEST = "application/vnd.oci.image.manifest.v1+json"
OCI_INDEX = "application/vnd.oci.image.index.v1+json"
DOCKER_MANIFEST = "application/vnd.docker.distribution.manifest.v2+json"
DOCKER_INDEX = "application/vnd.docker.distribution.manifest.list.v2+json"
MEDIA_TYPES = (OCI_INDEX, OCI_MANIFEST, DOCKER_INDEX, DOCKER_MANIFEST)
MAX_MANIFEST_BYTES = 4 * 1024 * 1024

Digest = Annotated[str, StringConstraints(pattern=r"^sha256:[0-9a-f]{64}$")]
MediaType = Annotated[
    str,
    StringConstraints(pattern=r"^[A-Za-z0-9!#$&^_.+-]+/[A-Za-z0-9!#$&^_.+-]+$", max_length=255),
]
PlatformName = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")]


class Metadata(BaseModel):
    # OCI permits extension properties. Retain only fields understood here.
    model_config = ConfigDict(extra="ignore", strict=True, frozen=True, populate_by_name=True)


class Platform(Metadata):
    architecture: PlatformName
    os: PlatformName
    variant: PlatformName | None = None


class Descriptor(Metadata):
    media_type: MediaType = Field(alias="mediaType")
    digest: Digest
    size: int = Field(ge=0)
    platform: Platform | None = None


class ImageManifest(Metadata):
    schema_version: Literal[2] = Field(alias="schemaVersion")
    media_type: Literal[
        "application/vnd.oci.image.manifest.v1+json",
        "application/vnd.docker.distribution.manifest.v2+json",
    ] = Field(alias="mediaType")
    config: Descriptor
    layers: list[Descriptor] = Field(max_length=4096)
    subject: Descriptor | None = None
    artifact_type: MediaType | None = Field(default=None, alias="artifactType")


class ImageIndex(Metadata):
    schema_version: Literal[2] = Field(alias="schemaVersion")
    media_type: Literal[
        "application/vnd.oci.image.index.v1+json",
        "application/vnd.docker.distribution.manifest.list.v2+json",
    ] = Field(alias="mediaType")
    manifests: list[Descriptor] = Field(max_length=1024)
    subject: Descriptor | None = None
    artifact_type: MediaType | None = Field(default=None, alias="artifactType")


class ParsedManifest(Metadata):
    kind: Literal["manifest", "index"]
    digest: Digest
    media_type: MediaType
    size_bytes: int
    digest_header_verified: bool
    document: ImageManifest | ImageIndex


def strict_object(raw: bytes) -> dict[str, Any]:
    """Reject duplicate keys, non-finite values and non-object JSON."""

    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    def nonfinite(value: str) -> None:
        raise ValueError("non-finite JSON")

    value = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=nonfinite)
    if not isinstance(value, dict):
        raise ValueError("expected JSON object")
    return value


def parse_manifest(
    raw: bytes,
    content_type: str,
    *,
    expected_digest: str | None = None,
    advertised_digest: str | None = None,
) -> ParsedManifest:
    """Hash the exact response bytes before interpreting metadata."""
    if len(raw) > MAX_MANIFEST_BYTES:
        raise OciError("RESPONSE_TOO_LARGE", "Manifest exceeds the 4 MiB limit.")
    media_type = content_type.partition(";")[0].strip().lower()
    if media_type not in MEDIA_TYPES:
        raise OciError("UNSUPPORTED_MEDIA_TYPE", "Unsupported or missing manifest Content-Type.")
    digest = digest_bytes(raw)
    for claimed in (expected_digest, advertised_digest):
        if claimed is not None:
            validate_digest(claimed)
            if claimed != digest:
                raise OciError(
                    "DIGEST_MISMATCH", "Manifest bytes do not match the expected digest."
                )
    try:
        data = strict_object(raw)
        if type(data.get("schemaVersion")) is not int or data["schemaVersion"] != 2:
            raise ValueError("schema version")
        if data.get("mediaType", media_type) != media_type:
            raise OciError("MEDIA_TYPE_MISMATCH", "Content-Type and manifest mediaType differ.")
        data["mediaType"] = media_type
        if media_type in (OCI_INDEX, DOCKER_INDEX):
            document: ImageManifest | ImageIndex = ImageIndex.model_validate(data)
            kind: Literal["manifest", "index"] = "index"
        else:
            document = ImageManifest.model_validate(data)
            kind = "manifest"
    except (ValueError, UnicodeError, ValidationError, RecursionError):
        raise OciError(
            "MALFORMED_MANIFEST", "Manifest JSON or required descriptor fields are invalid."
        ) from None
    return ParsedManifest(
        kind=kind,
        digest=digest,
        media_type=media_type,
        size_bytes=len(raw),
        digest_header_verified=advertised_digest is not None,
        document=document,
    )
