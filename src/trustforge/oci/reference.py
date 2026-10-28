"""A conservative Distribution reference grammar, with Docker Hub normalization."""

import re
from dataclasses import dataclass

from trustforge.oci.digest import SHA256
from trustforge.oci.errors import OciError

COMPONENT = re.compile(r"[a-z0-9]+(?:(?:[._]|__|-+)[a-z0-9]+)*")
HOST = re.compile(
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)*"
)
TAG = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}")


@dataclass(frozen=True)
class ImageReference:
    registry: str
    repository: str
    tag: str | None
    digest: str | None

    @property
    def selector(self) -> str:
        return self.digest or self.tag or "latest"

    @property
    def name(self) -> str:
        return f"{self.registry}/{self.repository}"

    @property
    def canonical(self) -> str:
        separator = "@" if self.digest else ":"
        return f"{self.name}{separator}{self.selector}"

    @property
    def manifest_url(self) -> str:
        return f"https://{self.registry}/v2/{self.repository}/manifests/{self.selector}"


def parse_reference(value: str) -> ImageReference:
    """Reject URLs, credentials and path ambiguity before any HTTP request."""

    def invalid() -> OciError:
        return OciError(
            "INVALID_REFERENCE",
            "Invalid OCI reference; use registry/repository[:tag][@sha256:digest] "
            "without a URL scheme.",
            2,
        )

    if not value or len(value) > 512 or not value.isascii():
        raise invalid()
    if any(c.isspace() or ord(c) < 33 for c in value) or any(c in value for c in "\\?#%"):
        raise invalid()
    if "://" in value or value.count("@") > 1:
        raise invalid()
    name, sep, digest = value.partition("@")
    if sep and not SHA256.fullmatch(digest):
        raise invalid()
    # A colon denotes a tag only if it follows the last repository slash.
    tag: str | None = None
    if name.rfind(":") > name.rfind("/"):
        name, _, tag = name.rpartition(":")
        if not TAG.fullmatch(tag):
            raise invalid()
    parts = name.split("/")
    first = parts[0]
    explicit = len(parts) > 1 and ("." in first or ":" in first or first.lower() == "localhost")
    registry = first.lower() if explicit else "registry-1.docker.io"
    repository = "/".join(parts[1:] if explicit else parts)
    host, colon, port = registry.partition(":")
    if not HOST.fullmatch(host) or len(host) > 253:
        raise invalid()
    if colon and (not port.isascii() or not port.isdecimal() or not 1 <= int(port) <= 65535):
        raise invalid()
    if registry in ("docker.io", "index.docker.io", "registry-1.docker.io"):
        registry = "registry-1.docker.io"
        if "/" not in repository:
            repository = "library/" + repository
    if not repository or len(repository) > 255:
        raise invalid()
    if not all(COMPONENT.fullmatch(p) for p in repository.split("/")):
        raise invalid()
    return ImageReference(registry, repository, tag or (None if sep else "latest"), digest or None)
