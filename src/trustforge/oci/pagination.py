"""A bounded next-link parser for one immutable OCI referrers endpoint."""

import re
from urllib.parse import parse_qsl

import httpx

from trustforge.oci.errors import OciError

MAX_PAGES = 5
MAX_DESCRIPTORS = 1024
TOKEN = r"[!#$%&'*+.^_`|~0-9A-Za-z-]+"
PARAMETER = re.compile(
    rf'[ \t]*;[ \t]*({TOKEN})[ \t]*=[ \t]*(?:"((?:[^"\\\r\n]|\\[ -~])*)"|({TOKEN}))'
)


def invalid_link() -> OciError:
    return OciError("INVALID_PAGE_LINK", "Unsafe, malformed or ambiguous referrers next link.")


def next_parameters(
    headers: httpx.Headers,
    endpoint: str,
    artifact_type: str | None,
) -> dict[str, str] | None:
    """Resolve a single rel=next without permitting an origin/path/filter change."""
    links = headers.get_list("link")
    if not links:
        return None
    if len(links) != 1 or len(links[0]) > 4096 or not links[0].isascii():
        raise invalid_link()
    text = links[0]
    if any(ord(c) < 32 and c != "\t" for c in text) or "\x7f" in text:
        raise invalid_link()
    target_match = re.match(r"[ \t]*<([^<>]+)>", text)
    if target_match is None:
        raise invalid_link()
    target = target_match[1]
    parameters: dict[str, str] = {}
    position = target_match.end()
    while text[position:].strip():
        match = PARAMETER.match(text, position)
        if match is None:
            raise invalid_link()
        key = match[1].lower()
        value = match[2] if match[2] is not None else match[3]
        if key in parameters:
            raise invalid_link()
        parameters[key] = re.sub(r"\\(.)", r"\1", value)
        position = match.end()
    if parameters.get("rel", "").lower() != "next" or "anchor" in parameters:
        raise invalid_link()
    if (
        not target
        or any(ord(c) < 33 or ord(c) > 126 or c in '#\\"<>{}|^`' for c in target)
        or target.startswith("//")
        or "%" in target.partition("?")[0]
        or re.search(r"/\.{1,2}(?:/|\?|$)", target)
        or re.search(r"%(?![0-9a-fA-F]{2})", target)
    ):
        raise invalid_link()
    try:
        base = httpx.URL(endpoint)
        url = base.join(target)
        if (
            url.scheme != "https"
            or url.host != base.host
            or url.port != base.port
            or url.userinfo
            or url.fragment
            or url.path != base.path
        ):
            raise invalid_link()
        pairs = parse_qsl(
            url.query.decode("ascii"),
            keep_blank_values=True,
            strict_parsing=True,
            encoding="ascii",
            errors="strict",
        )
    except (httpx.InvalidURL, ValueError, UnicodeError):
        raise invalid_link() from None
    result: dict[str, str] = {}
    # Cursor names are intentionally bounded, not an arbitrary crawling interface.
    for key, value in pairs:
        if key in result or key not in {"n", "last", "cursor", "next", "artifactType"}:
            raise invalid_link()
        if not 1 <= len(value) <= 1024 or any(not 33 <= ord(c) <= 126 for c in value):
            raise invalid_link()
        if key == "n":
            if not value.isdecimal() or not 1 <= int(value) <= MAX_DESCRIPTORS:
                raise invalid_link()
            value = str(int(value))
        result[key] = value
    if "artifactType" in result and result["artifactType"] != artifact_type:
        raise invalid_link()
    if artifact_type is not None:
        result["artifactType"] = artifact_type
    return result
