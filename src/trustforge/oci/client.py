"""Read-only HTTPS manifest retrieval; no blob, filesystem credential or runtime APIs."""

from dataclasses import dataclass
from time import monotonic
from typing import Literal

import httpx
from pydantic import ConfigDict

from trustforge.oci.auth import parse_challenge, parse_token
from trustforge.oci.errors import OciError
from trustforge.oci.models import (
    MAX_MANIFEST_BYTES,
    MEDIA_TYPES,
    Descriptor,
    ImageIndex,
    ParsedManifest,
    parse_manifest,
)
from trustforge.oci.platforms import PlatformSelection, parse_platform, select_descriptor
from trustforge.oci.reference import ImageReference, parse_reference

MAX_TOKEN_BYTES = 64 * 1024
BUDGET_SECONDS = 30.0


class Inspection(ParsedManifest):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    schema_version: Literal[1] = 1
    reference: str
    resolved_reference: str


class PlatformInspection(Inspection):
    selection: PlatformSelection


@dataclass(frozen=True)
class Reply:
    status: int
    headers: httpx.Headers
    body: bytes


def remaining_time(deadline: float) -> float:
    remaining = deadline - monotonic()
    if remaining <= 0:
        raise OciError("TIMEOUT", "Registry inspection exceeded its time budget.", 3)
    return remaining


def get_bounded(
    client: httpx.Client,
    url: str,
    *,
    deadline: float,
    limit: int,
    headers: dict[str, str],
    params: dict[str, str] | None = None,
    method: Literal["GET", "HEAD"] = "GET",
    allow_not_found: bool = False,
) -> Reply:
    """Read-only GET/HEAD; HEAD and error bodies are never consumed."""
    if method not in ("GET", "HEAD"):
        raise OciError("INVALID_METHOD", "Only metadata GET and HEAD are supported.", 2)
    timeout = min(10.0, remaining_time(deadline))
    try:
        with client.stream(
            method,
            url,
            headers=headers,
            params=params,
            timeout=httpx.Timeout(timeout, connect=min(5.0, timeout), pool=min(5.0, timeout)),
        ) as response:
            response_headers = httpx.Headers(response.headers)
            status = response.status_code
            if 300 <= status < 400:
                raise OciError("REDIRECT_REJECTED", "Registry/token redirects are not followed.", 3)
            if status == 429:
                raise OciError("RATE_LIMITED", "Registry/token rate limit reached (HTTP 429).", 6)
            if status == 401 or (status == 404 and allow_not_found):
                return Reply(status, response_headers, b"")
            if status != 200:
                raise OciError("HTTP_ERROR", f"Registry/token endpoint returned HTTP {status}.", 6)
            if response.headers.get("content-encoding", "identity").strip().lower() != "identity":
                raise OciError(
                    "ENCODING_REJECTED", "Compressed metadata responses are not accepted."
                )
            declared = response.headers.get("content-length")
            expected_size: int | None = None
            if declared is not None:
                if len(declared) > 10 or not declared.isascii() or not declared.isdecimal():
                    raise OciError("INVALID_LENGTH", "Invalid Content-Length for metadata.")
                expected_size = int(declared)
                if expected_size > limit:
                    raise OciError(
                        "RESPONSE_TOO_LARGE", "Metadata exceeds its response size limit."
                    )
            if method == "HEAD":
                remaining_time(deadline)
                return Reply(status, response_headers, b"")
            body = bytearray()
            for chunk in response.iter_bytes():
                remaining_time(deadline)
                if len(body) + len(chunk) > limit:
                    raise OciError(
                        "RESPONSE_TOO_LARGE", "Metadata exceeds its response size limit."
                    )
                body.extend(chunk)
            remaining_time(deadline)
            if expected_size is not None and len(body) != expected_size:
                raise OciError("INVALID_LENGTH", "Metadata size differs from Content-Length.")
            return Reply(status, response_headers, bytes(body))
    except httpx.TimeoutException:
        raise OciError("TIMEOUT", "Registry/token request timed out.", 3) from None
    except httpx.HTTPError:
        raise OciError("NETWORK_ERROR", "Registry/token HTTPS request failed.", 3) from None
    finally:
        # Never carry registry or token-endpoint cookies into another request.
        client.cookies.clear()


def anonymous_token(
    client: httpx.Client, reply: Reply, ref: ImageReference, deadline: float
) -> str:
    challenges = reply.headers.get_list("www-authenticate")
    if len(challenges) != 1:
        raise OciError("AUTH_REQUIRED", "One anonymous Bearer challenge is required.", 4)
    challenge = parse_challenge(challenges[0], ref)
    token_reply = get_bounded(
        client,
        challenge.realm,
        deadline=deadline,
        limit=MAX_TOKEN_BYTES,
        headers={"Accept": "application/json", "Accept-Encoding": "identity"},
        params={"service": challenge.service, "scope": challenge.scope},
    )
    if token_reply.status == 401:
        raise OciError("AUTH_REQUIRED", "Anonymous token access was denied.", 4)
    if (
        token_reply.headers.get("content-type", "").partition(";")[0].strip().lower()
        != "application/json"
    ):
        raise OciError("AUTH_FAILED", "Token endpoint did not return application/json.", 4)
    return parse_token(token_reply.body)


def fetch_manifest(
    client: httpx.Client,
    ref: ImageReference,
    deadline: float,
    *,
    descriptor: Descriptor | None = None,
) -> ParsedManifest:
    """Bound each metadata GET and its independent anonymous auth retry."""
    headers = {"Accept": ", ".join(MEDIA_TYPES), "Accept-Encoding": "identity"}
    limit = min(MAX_MANIFEST_BYTES, descriptor.size) if descriptor else MAX_MANIFEST_BYTES
    reply = get_bounded(client, ref.manifest_url, deadline=deadline, limit=limit, headers=headers)
    if reply.status == 401:
        token = anonymous_token(client, reply, ref, deadline)
        # Never share a token with a realm or a descriptor-provided URL.
        reply = get_bounded(
            client,
            ref.manifest_url,
            deadline=deadline,
            limit=limit,
            headers={**headers, "Authorization": "Bearer " + token},
        )
        if reply.status == 401:
            raise OciError("AUTH_REQUIRED", "Anonymous registry access was denied.", 4)
    if descriptor is not None and len(reply.body) != descriptor.size:
        raise OciError("DESCRIPTOR_SIZE_MISMATCH", "Child size differs from its index descriptor.")
    parsed = parse_manifest(
        reply.body,
        reply.headers.get("content-type", ""),
        expected_digest=ref.digest,
        advertised_digest=reply.headers.get("docker-content-digest"),
    )
    if descriptor is not None and parsed.media_type != descriptor.media_type:
        raise OciError("DESCRIPTOR_MEDIA_MISMATCH", "Child media type differs from its descriptor.")
    return parsed


def inspect_reference(
    value: str,
    *,
    platform: str | None = None,
    transport: httpx.BaseTransport | None = None,
) -> Inspection:
    """Read a root manifest and optionally one selected child; never configs/layers."""
    ref = parse_reference(value)
    requested = parse_platform(platform) if platform is not None else None
    deadline = monotonic() + BUDGET_SECONDS
    with httpx.Client(
        transport=transport,
        trust_env=False,
        follow_redirects=False,
        timeout=httpx.Timeout(10.0, connect=5.0),
        auth=None,
        limits=httpx.Limits(max_connections=1, max_keepalive_connections=1),
    ) as client:
        parsed = fetch_manifest(client, ref, deadline)
        result = Inspection(
            **parsed.model_dump(),
            reference=ref.canonical,
            resolved_reference=ref.name + "@" + parsed.digest,
        )
        if requested is None:
            return result
        if not isinstance(parsed.document, ImageIndex):
            raise OciError(
                "PLATFORM_UNVERIFIABLE", "A standalone manifest has no index platform descriptor."
            )
        descriptor = select_descriptor(parsed.document, requested)
        child_ref = parse_reference(ref.name + "@" + descriptor.digest)
        child = fetch_manifest(client, child_ref, deadline, descriptor=descriptor)
        return PlatformInspection(
            **result.model_dump(),
            selection=PlatformSelection(
                requested_platform=f"{requested.os}/{requested.architecture}"
                + (f"/{requested.variant}" if requested.variant else ""),
                index_digest=parsed.digest,
                manifest_digest=child.digest,
                resolved_reference=child_ref.canonical,
                descriptor=descriptor,
                manifest=child,
            ),
        )
