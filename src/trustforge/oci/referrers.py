"""Bounded OCI referrers discovery; registry descriptors are unauthenticated claims."""

from time import monotonic
from typing import Literal

import httpx
from pydantic import Field, TypeAdapter, ValidationError

from trustforge.oci.client import (
    BUDGET_SECONDS,
    Reply,
    anonymous_token,
    fetch_manifest,
    get_bounded,
)
from trustforge.oci.errors import OciError
from trustforge.oci.models import (
    MAX_MANIFEST_BYTES,
    OCI_INDEX,
    Descriptor,
    Digest,
    ImageIndex,
    MediaType,
    Metadata,
    parse_manifest,
    strict_object,
)
from trustforge.oci.reference import ImageReference, parse_reference


class ReferrerDescriptor(Descriptor):
    artifact_type: MediaType | None = Field(default=None, alias="artifactType")
    annotations: dict[str, str] = Field(default_factory=dict)


class ReferrersReport(Metadata):
    schema_version: Literal[1] = 1
    operation: Literal["referrers"] = "referrers"
    reference: str
    subject_reference: str
    subject_digest: Digest
    subject_resolution: Literal["manifest_get", "supplied_digest"]
    source: Literal["referrers_api", "oci_tag_schema"]
    api_status: Literal["available", "not_found"]
    status: Literal["listed", "empty"]
    artifact_type_filter: MediaType | None
    referrers: list[ReferrerDescriptor]
    list_digest: Digest
    list_size_bytes: int
    digest_header_verified: bool
    association_verified: Literal[False] = False
    authenticity_verified: Literal[False] = False


def request_list(
    client: httpx.Client,
    url: str,
    ref: ImageReference,
    deadline: float,
    params: dict[str, str] | None = None,
) -> Reply:
    """Reuse the existing transport/auth, including one retry of this exact URL."""
    headers = {"Accept": OCI_INDEX, "Accept-Encoding": "identity"}
    reply = get_bounded(
        client,
        url,
        deadline=deadline,
        limit=MAX_MANIFEST_BYTES,
        headers=headers,
        params=params,
        allow_not_found=True,
    )
    if reply.status == 401:
        token = anonymous_token(client, reply, ref, deadline)
        reply = get_bounded(
            client,
            url,
            deadline=deadline,
            limit=MAX_MANIFEST_BYTES,
            headers={**headers, "Authorization": "Bearer " + token},
            params=params,
            allow_not_found=True,
        )
        if reply.status == 401:
            raise OciError("AUTH_REQUIRED", "Anonymous referrers access was denied.", 4)
    return reply


def list_referrers(
    value: str,
    *,
    artifact_type: str | None = None,
    transport: httpx.BaseTransport | None = None,
) -> ReferrersReport:
    ref = parse_reference(value)
    if artifact_type is not None:
        try:
            TypeAdapter(MediaType).validate_python(artifact_type, strict=True)
        except ValidationError:
            raise OciError(
                "INVALID_ARTIFACT_TYPE", "Use a valid artifact media type filter.", 2
            ) from None
    deadline = monotonic() + BUDGET_SECONDS
    with httpx.Client(
        transport=transport,
        trust_env=False,
        follow_redirects=False,
        auth=None,
        timeout=httpx.Timeout(10.0, connect=5.0),
        limits=httpx.Limits(max_connections=1, max_keepalive_connections=1),
    ) as client:
        digest = ref.digest or fetch_manifest(client, ref, deadline).digest
        url = f"https://{ref.registry}/v2/{ref.repository}/referrers/{digest}"
        params = {"artifactType": artifact_type} if artifact_type is not None else None
        reply = request_list(client, url, ref, deadline, params)
        source: Literal["referrers_api", "oci_tag_schema"] = "referrers_api"
        api_status: Literal["available", "not_found"] = "available"
        if reply.status == 404:
            # Distribution 1.1 standard only: <algorithm>-<hex>, never .sig/.att tags.
            source, api_status = "oci_tag_schema", "not_found"
            fallback = parse_reference(ref.name + ":" + digest.replace(":", "-", 1))
            reply = request_list(client, fallback.manifest_url, ref, deadline)
            if reply.status == 404:
                raise OciError(
                    "REFERRERS_UNAVAILABLE",
                    "API and standard OCI tag are unavailable; absence cannot be determined.",
                    6,
                )
    if reply.headers.get_list("link"):
        # Never truncate a paginated list or follow an arbitrary server URL.
        raise OciError(
            "REFERRERS_PAGINATED",
            "Paginated referrers are not supported; no partial list is returned.",
        )
    parsed = parse_manifest(
        reply.body,
        reply.headers.get("content-type", ""),
        advertised_digest=reply.headers.get("docker-content-digest"),
    )
    if parsed.media_type != OCI_INDEX or not isinstance(parsed.document, ImageIndex):
        raise OciError("INVALID_REFERRERS_INDEX", "Referrers must be an OCI image index.")
    try:
        items = [
            ReferrerDescriptor.model_validate(item, by_name=False)
            for item in strict_object(reply.body)["manifests"]
        ]
    except (ValidationError, ValueError):
        raise OciError(
            "MALFORMED_REFERRERS", "Invalid referrer artifact type or annotations."
        ) from None
    if len({item.digest for item in items}) != len(items):
        raise OciError("DUPLICATE_REFERRER", "Referrer digests must be unique.")
    filters = reply.headers.get_list("oci-filters-applied")
    if filters:
        if filters != ["artifactType"] or artifact_type is None or source != "referrers_api":
            raise OciError(
                "UNEXPECTED_FILTER", "Unsupported or unexpected referrers filtering claim."
            )
        if any(item.artifact_type != artifact_type for item in items):
            raise OciError(
                "FILTER_MISMATCH", "Registry claimed a filter but returned mismatched descriptors."
            )
    # Registry-side filtering is optional; enforce the requested filter locally too.
    selected = [
        item for item in items if artifact_type is None or item.artifact_type == artifact_type
    ]
    return ReferrersReport(
        reference=ref.canonical,
        subject_reference=ref.name + "@" + digest,
        subject_digest=digest,
        subject_resolution="supplied_digest" if ref.digest else "manifest_get",
        source=source,
        api_status=api_status,
        status="listed" if selected else "empty",
        artifact_type_filter=artifact_type,
        referrers=selected,
        list_digest=parsed.digest,
        list_size_bytes=parsed.size_bytes,
        digest_header_verified=parsed.digest_header_verified,
    )
