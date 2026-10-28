"""Registry-header observations only: HEAD cannot verify manifest content bytes."""

from time import monotonic
from typing import Literal

import httpx

from trustforge.oci.client import BUDGET_SECONDS, anonymous_token, get_bounded
from trustforge.oci.digest import validate_digest
from trustforge.oci.errors import OciError
from trustforge.oci.models import MAX_MANIFEST_BYTES, MEDIA_TYPES, Digest, MediaType, Metadata
from trustforge.oci.reference import parse_reference


class HeadObservation(Metadata):
    schema_version: Literal[1] = 1
    operation: Literal["head"] = "head"
    reference: str
    resolved_reference: str
    digest: Digest
    digest_source: Literal["registry_header"] = "registry_header"
    media_type: MediaType
    size_bytes: int
    requested_digest_matches: bool | None
    content_integrity_verified: Literal[False] = False


def head_reference(value: str, *, transport: httpx.BaseTransport | None = None) -> HeadObservation:
    ref = parse_reference(value)
    deadline = monotonic() + BUDGET_SECONDS
    headers = {"Accept": ", ".join(MEDIA_TYPES), "Accept-Encoding": "identity"}
    with httpx.Client(
        transport=transport,
        trust_env=False,
        follow_redirects=False,
        auth=None,
        timeout=httpx.Timeout(10.0, connect=5.0),
        limits=httpx.Limits(max_connections=1, max_keepalive_connections=1),
    ) as client:
        reply = get_bounded(
            client,
            ref.manifest_url,
            method="HEAD",
            deadline=deadline,
            limit=MAX_MANIFEST_BYTES,
            headers=headers,
        )
        if reply.status == 401:
            token = anonymous_token(client, reply, ref, deadline)
            reply = get_bounded(
                client,
                ref.manifest_url,
                method="HEAD",
                deadline=deadline,
                limit=MAX_MANIFEST_BYTES,
                headers={**headers, "Authorization": "Bearer " + token},
            )
            if reply.status == 401:
                raise OciError("AUTH_REQUIRED", "Anonymous registry access was denied.", 4)
    digest = reply.headers.get("docker-content-digest")
    if digest is None:
        raise OciError("MISSING_DIGEST", "HEAD response has no registry digest header.")
    validate_digest(digest)
    if ref.digest is not None and digest != ref.digest:
        raise OciError("DIGEST_MISMATCH", "HEAD digest claim differs from the requested digest.")
    length = reply.headers.get("content-length")
    if length is None:
        raise OciError("MISSING_LENGTH", "HEAD response has no Content-Length header.")
    media_type = reply.headers.get("content-type", "").partition(";")[0].strip().lower()
    if media_type not in MEDIA_TYPES:
        raise OciError("UNSUPPORTED_MEDIA_TYPE", "Unsupported or missing manifest Content-Type.")
    return HeadObservation(
        reference=ref.canonical,
        resolved_reference=ref.name + "@" + digest,
        digest=digest,
        media_type=media_type,
        size_bytes=int(length),
        requested_digest_matches=True if ref.digest is not None else None,
    )
