"""Explicit descriptor selection, without host detection or runtime compatibility claims."""

import re

from trustforge.oci.errors import OciError
from trustforge.oci.models import (
    DOCKER_MANIFEST,
    MAX_MANIFEST_BYTES,
    OCI_MANIFEST,
    Descriptor,
    Digest,
    ImageIndex,
    Metadata,
    ParsedManifest,
    Platform,
)

SELECTOR = re.compile(r"[a-z0-9][a-z0-9._-]{0,63}(?:/[a-z0-9][a-z0-9._-]{0,63}){1,2}")


class PlatformSelection(Metadata):
    requested_platform: str
    index_digest: Digest
    manifest_digest: Digest
    resolved_reference: str
    descriptor: Descriptor
    manifest: ParsedManifest


def parse_platform(value: str) -> Platform:
    """Accept only explicit os/architecture[/variant], with no implicit aliases."""
    if SELECTOR.fullmatch(value) is None:
        raise OciError(
            "INVALID_PLATFORM", "Use lowercase os/architecture[/variant] for --platform.", 2
        )
    parts = value.split("/")
    return Platform(
        os=parts[0], architecture=parts[1], variant=parts[2] if len(parts) == 3 else None
    )


def select_descriptor(index: ImageIndex, requested: Platform) -> Descriptor:
    """A missing variant may select one candidate; ambiguity never picks the first."""
    matches = [
        item
        for item in index.manifests
        if item.platform is not None
        and item.platform.os == requested.os
        and item.platform.architecture == requested.architecture
        and (requested.variant is None or item.platform.variant == requested.variant)
    ]
    if not matches:
        raise OciError("PLATFORM_NOT_FOUND", "No descriptor matches the requested platform.")
    if len(matches) != 1:
        raise OciError(
            "AMBIGUOUS_PLATFORM", "Multiple descriptors match; specify a unique variant."
        )
    descriptor = matches[0]
    if descriptor.media_type not in (OCI_MANIFEST, DOCKER_MANIFEST):
        raise OciError(
            "UNSUPPORTED_PLATFORM_MANIFEST", "Selection supports direct image manifests only."
        )
    if not 0 < descriptor.size <= MAX_MANIFEST_BYTES:
        raise OciError("INVALID_PLATFORM_DESCRIPTOR", "Selected manifest size is outside bounds.")
    return descriptor
