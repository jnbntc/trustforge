"""Offline HEAD contract: no response body is consumed, and no byte hash is claimed."""

import json
from collections.abc import Iterator
from typing import Any

import httpx
import pytest
from rich.text import Text
from typer.testing import CliRunner

from trustforge.cli import app
from trustforge.oci.errors import OciError
from trustforge.oci.head import head_reference
from trustforge.oci.models import MAX_MANIFEST_BYTES, MEDIA_TYPES, OCI_INDEX

REF = "registry.example/team/image:tag"
DIGEST = "sha256:" + "a" * 64
PATH = "/v2/team/image/manifests/"
HEADERS = {"Content-Type": OCI_INDEX, "Content-Length": "123", "Docker-Content-Digest": DIGEST}
TOKEN = "fixture-token.NO-LOG"


class UnreadBody(httpx.SyncByteStream):
    closed = False

    def __iter__(self) -> Iterator[bytes]:
        raise AssertionError("HEAD or error body must never be consumed")
        yield b""  # pragma: no cover

    def close(self) -> None:
        self.closed = True


@pytest.mark.parametrize("by_digest", [False, True])
def test_head_is_header_observation_not_get_verification(by_digest: bool) -> None:
    stream = UnreadBody()
    calls: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        assert request.method == "HEAD" and request.url.scheme == "https"
        assert request.url.path == PATH + (DIGEST if by_digest else "tag")
        assert set(request.headers["accept"].split(", ")) == set(MEDIA_TYPES)
        assert "authorization" not in request.headers
        return httpx.Response(200, headers=HEADERS, stream=stream)

    ref = "registry.example/team/image@" + DIGEST if by_digest else REF
    result = head_reference(ref, transport=httpx.MockTransport(handle))
    assert len(calls) == 1 and stream.closed
    assert result.digest == DIGEST and result.size_bytes == 123
    assert result.operation == "head" and result.digest_source == "registry_header"
    assert result.requested_digest_matches == (True if by_digest else None)
    assert not result.content_integrity_verified
    assert "digest_header_verified" not in result.model_dump()


@pytest.mark.parametrize(
    "header,value,code",
    [
        ("Docker-Content-Digest", None, "MISSING_DIGEST"),
        ("Docker-Content-Digest", "sha256:bad", "INVALID_DIGEST"),
        ("Docker-Content-Digest", "sha256:" + "A" * 64, "INVALID_DIGEST"),
        ("Docker-Content-Digest", DIGEST + ", " + DIGEST, "INVALID_DIGEST"),
        ("Content-Length", None, "MISSING_LENGTH"),
        ("Content-Length", "-1", "INVALID_LENGTH"),
        ("Content-Length", "1.0", "INVALID_LENGTH"),
        ("Content-Length", "１", "INVALID_LENGTH"),
        ("Content-Length", "123, 123", "INVALID_LENGTH"),
        ("Content-Length", str(MAX_MANIFEST_BYTES + 1), "RESPONSE_TOO_LARGE"),
        ("Content-Length", "9" * 11, "INVALID_LENGTH"),
        ("Content-Type", None, "UNSUPPORTED_MEDIA_TYPE"),
        ("Content-Type", "text/html", "UNSUPPORTED_MEDIA_TYPE"),
        ("Content-Encoding", "gzip", "ENCODING_REJECTED"),
    ],
)
def test_bad_head_headers_fail_without_reading(header: str, value: str | None, code: str) -> None:
    headers = dict(HEADERS)
    if value is None:
        headers.pop(header)
    else:
        headers[header] = value
    with pytest.raises(OciError) as error:
        head_reference(
            REF,
            transport=httpx.MockTransport(
                lambda request: httpx.Response(
                    200,
                    headers=[(k.encode("ascii"), v.encode("utf-8")) for k, v in headers.items()],
                    stream=UnreadBody(),
                )
            ),
        )
    assert error.value.code == code


def test_requested_digest_mismatch_is_not_content_verification() -> None:
    with pytest.raises(OciError) as error:
        head_reference(
            "registry.example/team/image@sha256:" + "b" * 64,
            transport=httpx.MockTransport(lambda request: httpx.Response(200, headers=HEADERS)),
        )
    assert error.value.code == "DIGEST_MISMATCH"


@pytest.mark.parametrize("denied", [False, True])
def test_anonymous_bearer_retries_head_not_get(denied: bool) -> None:
    calls: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        assert "cookie" not in request.headers
        if len(calls) == 1:
            assert request.method == "HEAD"
            return httpx.Response(
                401,
                stream=UnreadBody(),
                headers={
                    "WWW-Authenticate": 'Bearer realm="https://registry.example/token"',
                    "Set-Cookie": "never=forward",
                },
            )
        if len(calls) == 2:
            assert request.method == "GET" and request.url.path == "/token"
            assert "authorization" not in request.headers
            assert request.url.params["scope"] == "repository:team/image:pull"
            return httpx.Response(200, json={"token": TOKEN})
        assert len(calls) == 3 and request.method == "HEAD"
        assert (
            request.url.path == PATH + "tag"
            and request.headers["authorization"] == "Bearer " + TOKEN
        )
        return httpx.Response(401 if denied else 200, headers=HEADERS, stream=UnreadBody())

    if denied:
        with pytest.raises(OciError) as error:
            head_reference(REF, transport=httpx.MockTransport(handle))
        assert error.value.code == "AUTH_REQUIRED" and TOKEN not in str(error.value)
    else:
        result = head_reference(REF, transport=httpx.MockTransport(handle))
        assert TOKEN not in result.model_dump_json() and not result.content_integrity_verified
    assert len(calls) == 3


@pytest.mark.parametrize("status", [301, 307, 400, 403, 404, 429, 500])
def test_head_errors_never_read_bodies_or_follow_redirects(status: int) -> None:
    calls: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(
            status, stream=UnreadBody(), headers={"Location": "https://evil.invalid/"}
        )

    with pytest.raises(OciError):
        head_reference(REF, transport=httpx.MockTransport(handle))
    assert len(calls) == 1


def test_unsafe_head_challenge_stops_before_token() -> None:
    calls: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(
            401, headers={"WWW-Authenticate": 'Bearer realm="https://evil.invalid/token"'}
        )

    with pytest.raises(OciError) as error:
        head_reference(REF, transport=httpx.MockTransport(handle))
    assert error.value.code == "AUTH_CHALLENGE_REJECTED" and len(calls) == 1


@pytest.mark.parametrize("machine", [False, True])
def test_head_cli_observation_contract(monkeypatch: pytest.MonkeyPatch, machine: bool) -> None:
    def inspect(value: str) -> Any:
        return head_reference(
            value,
            transport=httpx.MockTransport(lambda request: httpx.Response(200, headers=HEADERS)),
        )

    monkeypatch.setattr("trustforge.oci_cli.head_reference", inspect)
    result = CliRunner().invoke(app, ["oci", "head", REF] + (["--json"] if machine else []))
    assert result.exit_code == 0 and result.stderr == ""
    if machine:
        data = json.loads(result.stdout)
        assert data["operation"] == "head" and data["content_integrity_verified"] is False
        assert data["digest"] == DIGEST and "document" not in data
    else:
        assert "Registry digest claim:" in result.stdout
        assert "content integrity, authenticity and deployment are not verified" in " ".join(
            Text.from_ansi(result.stdout).plain.split()
        )


def test_head_cli_invalid_reference_and_help() -> None:
    result = CliRunner().invoke(app, ["oci", "head", "https://secret@host/image", "--json"])
    assert result.exit_code == 2 and result.stdout == "" and "secret" not in result.stderr
    assert json.loads(result.stderr)["error"]["code"] == "INVALID_REFERENCE"
    help_result = CliRunner().invoke(app, ["oci", "head", "--help"])
    assert help_result.exit_code == 0 and "--json" in Text.from_ansi(help_result.stdout).plain
