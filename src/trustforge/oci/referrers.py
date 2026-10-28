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
    ParsedManifest,
    parse_manifest,
    strict_object,
)
from trustforge.oci.pagination import MAX_DESCRIPTORS, MAX_PAGES, next_parameters
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


class ReferrersPage(Metadata):
    digest: Digest
    size_bytes: int
    digest_header_verified: bool


class PaginationSummary(Metadata):
    pages_queried: int
    observed_descriptors: int
    returned_descriptors: int
    total_size_bytes: int
    pages: list[ReferrersPage]


class PaginatedReferrersReport(ReferrersReport):
    list_digest_scope: Literal["first_page"] = "first_page"
    pagination: PaginationSummary


def request_list(
    client: httpx.Client,
    url: str,
    ref: ImageReference,
    deadline: float,
    params: dict[str, str] | None = None,
    *,
    limit: int = MAX_MANIFEST_BYTES,
) -> Reply:
    """Reuse the existing transport/auth, including one retry of this exact URL."""
    headers = {"Accept": OCI_INDEX, "Accept-Encoding": "identity"}
    reply = get_bounded(
        client,
        url,
        deadline=deadline,
        limit=limit,
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
            limit=limit,
            headers={**headers, "Authorization": "Bearer " + token},
            params=params,
            allow_not_found=True,
        )
        if reply.status == 401:
            raise OciError("AUTH_REQUIRED", "Anonymous referrers access was denied.", 4)
    return reply


def parse_page(
    reply: Reply,
    artifact_type: str | None,
    source: str,
) -> tuple[ParsedManifest, list[ReferrerDescriptor]]:
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
    return parsed, items


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
        pages: list[ReferrersPage] = []
        seen: dict[str, ReferrerDescriptor] = {}
        visited = {tuple(sorted((params or {}).items()))}
        total_bytes = 0
        while True:
            if source == "oci_tag_schema" and reply.headers.get_list("link"):
                raise OciError("INVALID_PAGE_LINK", "Standard fallback tags cannot paginate.")
            parsed, items = parse_page(reply, artifact_type, source)
            total_bytes += parsed.size_bytes
            if total_bytes > MAX_MANIFEST_BYTES:
                raise OciError("RESPONSE_TOO_LARGE", "Combined referrers pages exceed 4 MiB.")
            for item in items:
                previous = seen.get(item.digest)
                if previous is not None:
                    code = "DUPLICATE_REFERRER" if previous == item else "INCONSISTENT_REFERRER"
                    raise OciError(code, "Referrer digest was repeated or changed across the list.")
                seen[item.digest] = item
            if len(seen) > MAX_DESCRIPTORS:
                raise OciError("REFERRERS_DESCRIPTOR_LIMIT", "Combined descriptor limit exceeded.")
            pages.append(
                ReferrersPage(
                    digest=parsed.digest,
                    size_bytes=parsed.size_bytes,
                    digest_header_verified=parsed.digest_header_verified,
                )
            )
            following = next_parameters(reply.headers, url, artifact_type)
            if following is None:
                break
            if len(pages) >= MAX_PAGES:
                raise OciError("REFERRERS_PAGE_LIMIT", "Referrers page limit exceeded.")
            key = tuple(sorted(following.items()))
            if key in visited:
                raise OciError("REFERRERS_PAGE_CYCLE", "Referrers next link revisits a page.")
            visited.add(key)
            remaining = MAX_MANIFEST_BYTES - total_bytes
            if remaining <= 0:
                raise OciError("RESPONSE_TOO_LARGE", "Combined referrers pages exceed 4 MiB.")
            # Reconstruct the original endpoint; only validated query values are carried.
            reply = request_list(client, url, ref, deadline, following, limit=remaining)
            if reply.status == 404:
                raise OciError(
                    "REFERRERS_PAGE_ERROR", "A subsequent referrers page returned 404.", 6
                )
    selected = [
        item
        for item in seen.values()
        if artifact_type is None or item.artifact_type == artifact_type
    ]
    first = pages[0]
    report = ReferrersReport(
        reference=ref.canonical,
        subject_reference=ref.name + "@" + digest,
        subject_digest=digest,
        subject_resolution="supplied_digest" if ref.digest else "manifest_get",
        source=source,
        api_status=api_status,
        status="listed" if selected else "empty",
        artifact_type_filter=artifact_type,
        referrers=selected,
        list_digest=first.digest,
        list_size_bytes=first.size_bytes,
        digest_header_verified=first.digest_header_verified,
    )
    if len(pages) == 1:
        return report
    return PaginatedReferrersReport(
        **report.model_dump(),
        pagination=PaginationSummary(
            pages_queried=len(pages),
            observed_descriptors=len(seen),
            returned_descriptors=len(selected),
            total_size_bytes=total_bytes,
            pages=pages,
        ),
    )
