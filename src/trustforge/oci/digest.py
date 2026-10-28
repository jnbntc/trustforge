"""Content digests identify exact bytes, not authenticity or image safety."""

import hashlib
import re

from trustforge.oci.errors import OciError

SHA256 = re.compile(r"sha256:[0-9a-f]{64}")


def validate_digest(value: str) -> str:
    if not SHA256.fullmatch(value):
        raise OciError("INVALID_DIGEST", "Expected a lowercase sha256 digest with 64 hex digits.")
    return value


def digest_bytes(raw: bytes) -> str:
    """Hash bytes as received; never reserialize JSON before hashing."""
    return "sha256:" + hashlib.sha256(raw).hexdigest()
