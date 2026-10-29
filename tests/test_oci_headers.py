"""Offline regressions for ambiguous singleton metadata and token headers."""

import json
from collections.abc import Iterator

import httpx
import pytest

from trustforge.oci.client import inspect_reference
from trustforge.oci.digest import digest_bytes
from trustforge.oci.errors import OciError
from trustforge.oci.head import head_reference
from trustforge.oci.models import OCI_INDEX
from trustforge.oci.referrers import list_referrers

REF = "registry.example/team/image:tag"
DIGEST = "sha256:" + "a" * 64
IMMUTABLE = "registry.example/team/image@" + DIGEST
RAW = json.dumps({"schemaVersion": 2, "mediaType": OCI_INDEX, "manifests": []}).encode()
TOKEN = "fixture-token.NEVER-PRINT"


class TrackedBody(httpx.SyncByteStream):
    def __init__(self, raw: bytes) -> None:
        self.raw = raw
        self.read_count = 0
        self.closed = False

    def __iter__(self) -> Iterator[bytes]:
        self.read_count += 1
        yield self.raw

    def close(self) -> None:
        self.closed = True


@pytest.mark.parametrize("stage", ["inspect", "head", "referrers", "token", "page2"])
@pytest.mark.parametrize("conflicting", [False, True])
def test_duplicate_content_type_fails_before_consumption_or_partial_success(
    stage: str, conflicting: bool
) -> None:
    calls = 0
    body = TrackedBody(json.dumps({"token": TOKEN}).encode() if stage == "token" else RAW)
    media = "application/json" if stage == "token" else OCI_INDEX

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if stage == "token" and calls == 1:
            return httpx.Response(
                401,
                headers={"WWW-Authenticate": 'Bearer realm="https://registry.example/token"'},
            )
        if stage == "token" and calls == 3:
            # Before the fix this token was accepted and forwarded to the registry.
            assert request.headers["authorization"] == "Bearer " + TOKEN
            return httpx.Response(200, headers={"Content-Type": OCI_INDEX}, content=RAW)
        if stage == "page2" and calls == 1:
            return httpx.Response(
                200,
                headers={"Content-Type": OCI_INDEX, "Link": '<?last=p2>; rel="next"'},
                content=RAW,
            )
        return httpx.Response(
            200,
            headers=[
                ("Content-Type", media + "; charset=utf-8"),
                ("content-type", "text/html" if conflicting else media + "; charset=utf-8"),
                ("Content-Length", str(len(body.raw))),
                ("Docker-Content-Digest", digest_bytes(RAW)),
            ],
            stream=body,
        )

    transport = httpx.MockTransport(handle)
    with pytest.raises(OciError) as error:
        if stage == "head":
            head_reference(REF, transport=transport)
        elif stage in {"referrers", "page2"}:
            list_referrers(IMMUTABLE, transport=transport)
        else:
            inspect_reference(REF, transport=transport)
    assert error.value.code == "AMBIGUOUS_HEADERS"
    assert calls == (2 if stage in {"token", "page2"} else 1)
    assert body.closed and body.read_count == 0
    assert TOKEN not in str(error.value) and "text/html" not in str(error.value)


@pytest.mark.parametrize(
    "name,value",
    [
        ("Content-Length", str(len(RAW))),
        ("Docker-Content-Digest", digest_bytes(RAW)),
        ("Content-Encoding", "identity"),
    ],
)
def test_other_duplicated_singletons_are_rejected_before_read(name: str, value: str) -> None:
    body = TrackedBody(RAW)
    headers = [("Content-Type", OCI_INDEX), (name, value), (name.lower(), value)]
    with pytest.raises(OciError) as error:
        inspect_reference(
            REF,
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, headers=headers, stream=body)
            ),
        )
    assert error.value.code == "AMBIGUOUS_HEADERS" and body.closed and body.read_count == 0


def test_single_content_type_with_parameters_remains_supported() -> None:
    result = inspect_reference(
        REF,
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200, headers={"Content-Type": OCI_INDEX + "; charset=utf-8"}, content=RAW
            )
        ),
    )
    assert result.kind == "index" and result.digest == digest_bytes(RAW)
