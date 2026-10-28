"""Anonymous Bearer challenges with explicit realm, service and pull-scope boundaries."""

import re
from dataclasses import dataclass

import httpx

from trustforge.oci.errors import OciError
from trustforge.oci.models import strict_object
from trustforge.oci.reference import ImageReference

PARAMETER = re.compile(r'\s*([A-Za-z][A-Za-z0-9_-]*)="([^"\\\r\n]*)"\s*(?:,|$)')
TOKEN = re.compile(r"[A-Za-z0-9._~+/-]+=*")


def auth_error() -> OciError:
    return OciError(
        "AUTH_CHALLENGE_REJECTED", "Unsupported or unsafe anonymous Bearer challenge.", 4
    )


@dataclass(frozen=True)
class BearerChallenge:
    realm: str
    service: str
    scope: str


def parse_challenge(header: str, reference: ImageReference) -> BearerChallenge:
    """Never request a challenge's broader scope or arbitrary external realm."""
    if len(header) > 4096 or not header.isascii():
        raise auth_error()
    prefix = re.match(r"Bearer\s+", header, flags=re.IGNORECASE)
    if prefix is None:
        raise auth_error()
    text = header[prefix.end() :]
    if not text or text.rstrip().endswith(","):
        raise auth_error()
    parameters: dict[str, str] = {}
    position = 0
    while position < len(text):
        match = PARAMETER.match(text, position)
        if match is None:
            raise auth_error()
        key, value = match.groups()
        key = key.lower()
        if key in parameters or key not in {"realm", "service", "scope"}:
            raise auth_error()
        parameters[key] = value
        position = match.end()
    realm = parameters.get("realm", "")
    try:
        url = httpx.URL(realm)
        registry = httpx.URL("https://" + reference.registry)
    except httpx.InvalidURL:
        raise auth_error() from None
    if (
        url.scheme != "https"
        or not url.host
        or url.userinfo
        or url.query
        or url.fragment
        or (url.port is not None and not 1 <= url.port <= 65535)
        or "%" in realm
        or re.search(r"/\.{1,2}(?:/|$)", realm)
        or not re.fullmatch(r"/[A-Za-z0-9/_.~-]+", url.path)
        or any(part in (".", "..", "blobs", "manifests") for part in url.path.split("/"))
    ):
        raise auth_error()
    port = 443 if url.port is None else url.port
    registry_port = 443 if registry.port is None else registry.port
    same_origin = url.host == registry.host and port == registry_port
    docker_realm = (
        reference.registry == "registry-1.docker.io"
        and url.host == "auth.docker.io"
        and port == 443
        and url.path == "/token"
    )
    if not same_origin and not docker_realm:
        raise auth_error()
    service = (
        "registry.docker.io" if reference.registry == "registry-1.docker.io" else reference.registry
    )
    scope = f"repository:{reference.repository}:pull"
    if parameters.get("service", service) != service or parameters.get("scope", scope) != scope:
        raise auth_error()
    return BearerChallenge(str(url), service, scope)


def parse_token(raw: bytes) -> str:
    """Keep the token in memory only; never include server JSON in an error."""
    try:
        payload = strict_object(raw)
    except (ValueError, UnicodeError, RecursionError):
        raise OciError("AUTH_FAILED", "Token endpoint returned invalid JSON.", 4) from None
    token = payload.get("token", payload.get("access_token"))
    if (
        not isinstance(token, str)
        or not 1 <= len(token) <= 8192
        or TOKEN.fullmatch(token) is None
        or ("token" in payload and "access_token" in payload and payload["access_token"] != token)
    ):
        raise OciError("AUTH_FAILED", "Token endpoint did not return one valid Bearer token.", 4)
    return token
