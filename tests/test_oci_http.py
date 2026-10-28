"""Deterministic HTTP security tests; no real sockets, registries or credentials."""

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import httpx
import pytest

from trustforge.oci.auth import parse_token
from trustforge.oci.client import MAX_TOKEN_BYTES, inspect_reference
from trustforge.oci.digest import digest_bytes
from trustforge.oci.errors import OciError
from trustforge.oci.models import MAX_MANIFEST_BYTES, MEDIA_TYPES, OCI_INDEX, OCI_MANIFEST

FIXTURES = Path(__file__).parent / "fixtures" / "oci"
TOKEN = "fixture-token.NEVER-PRINT"
REF = "registry.example/team/image:tag"
PATH = "/v2/team/image/manifests/tag"
CHALLENGE = (
    'Bearer realm="https://registry.example/token",'
    'service="registry.example",scope="repository:team/image:pull"'
)


class Chunks(httpx.SyncByteStream):
    def __init__(self, chunks: list[bytes]) -> None:
        self.chunks = chunks
        self.read_count = 0
        self.closed = False

    def __iter__(self) -> Iterator[bytes]:
        for chunk in self.chunks:
            self.read_count += 1
            yield chunk

    def close(self) -> None:
        self.closed = True


def response(fixture: str = "manifest.json", media: str = OCI_MANIFEST) -> httpx.Response:
    raw = (FIXTURES / fixture).read_bytes()
    return httpx.Response(
        200,
        content=raw,
        headers={
            "Content-Type": media,
            "Docker-Content-Digest": digest_bytes(raw),
        },
    )


@pytest.mark.parametrize(
    "fixture,media", [("manifest.json", OCI_MANIFEST), ("index.json", OCI_INDEX)]
)
def test_anonymous_manifest_request_only(fixture: str, media: str) -> None:
    requests: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.method == "GET" and request.url.scheme == "https"
        assert request.url.path == PATH
        assert "authorization" not in request.headers and "cookie" not in request.headers
        assert set(request.headers["accept"].split(", ")) == set(MEDIA_TYPES)
        assert request.headers["accept-encoding"] == "identity"
        return response(fixture, media)

    result = inspect_reference(REF, transport=httpx.MockTransport(handle))
    assert len(requests) == 1
    assert result.schema_version == 1
    assert result.digest_header_verified
    assert result.resolved_reference == "registry.example/team/image@" + result.digest


def test_bearer_retry_is_bound_and_does_not_carry_cookies() -> None:
    requests: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.method == "GET"
        assert "cookie" not in request.headers
        if len(requests) == 1:
            assert request.url.path == PATH and "authorization" not in request.headers
            return httpx.Response(
                401,
                headers={
                    "WWW-Authenticate": CHALLENGE,
                    "Set-Cookie": "registry-secret=do-not-forward; Path=/",
                },
            )
        if len(requests) == 2:
            assert request.url.path == "/token"
            assert "authorization" not in request.headers
            assert dict(request.url.params) == {
                "service": "registry.example",
                "scope": "repository:team/image:pull",
            }
            return httpx.Response(
                200,
                json={"token": TOKEN},
                headers={
                    "Set-Cookie": "auth-secret=do-not-forward; Path=/",
                },
            )
        assert len(requests) == 3
        assert request.url.path == PATH
        assert request.headers["authorization"] == "Bearer " + TOKEN
        return response()

    result = inspect_reference(REF, transport=httpx.MockTransport(handle))
    assert len(requests) == 3
    assert TOKEN not in result.model_dump_json()


def test_docker_hub_explicit_cross_origin_token_exception() -> None:
    calls: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if len(calls) == 1:
            assert request.url.host == "registry-1.docker.io"
            return httpx.Response(
                401,
                headers={
                    "WWW-Authenticate": 'Bearer realm="https://auth.docker.io/token",service="registry.docker.io",'
                    'scope="repository:library/alpine:pull"'
                },
            )
        if len(calls) == 2:
            assert request.url.host == "auth.docker.io" and request.url.path == "/token"
            assert request.url.params["scope"] == "repository:library/alpine:pull"
            assert "authorization" not in request.headers
            return httpx.Response(200, json={"access_token": TOKEN})
        assert request.url.host == "registry-1.docker.io"
        assert request.headers["authorization"] == "Bearer " + TOKEN
        return response()

    assert inspect_reference("docker.io/alpine", transport=httpx.MockTransport(handle)).digest
    assert len(calls) == 3


@pytest.mark.parametrize(
    "challenge",
    [
        "",
        'Basic realm="credentials-not-allowed"',
        "Bearer",
        'Bearer realm="http://registry.example/token"',
        'Bearer realm="https://evil.example/token"',
        'Bearer realm="https://auth.docker.io/token"',
        'Bearer realm="https://registry.example.evil/token"',
        'Bearer realm="https://registry.example:8443/token"',
        'Bearer realm="https://registry.example:0/token"',
        'Bearer realm="https://registry.example/../token"',
        'Bearer realm="https://user:password@registry.example/token"',
        'Bearer realm="https://registry.example/token?scope=repository:other:push"',
        'Bearer realm="https://registry.example/token#fragment"',
        'Bearer realm="https://registry.example/%74oken"',
        'Bearer realm="https://registry.example/v2/x/blobs/sha256:bad"',
        'Bearer realm="https://registry.example/token",realm="https://registry.example/other"',
        'Bearer realm="https://registry.example/token",service="wrong"',
        'Bearer realm="https://registry.example/token",scope="repository:other:pull"',
        'Bearer realm="https://registry.example/token",scope="repository:team/image:pull,push"',
        'Bearer realm="https://registry.example/token",scope="repository:team/image:push"',
        'Bearer realm="https://registry.example/token",unknown="ignored?"',
        'Bearer realm="https://registry.example/token",',
        'Bearer realm="https://registry.example/token", service=registry.example',
        'Bearer realm="https://registry.example/token", Basic realm="bad"',
    ],
)
def test_unsafe_challenge_stops_before_token_request(challenge: str) -> None:
    handler = Mock(return_value=httpx.Response(401, headers={"WWW-Authenticate": challenge}))
    with pytest.raises(OciError) as error:
        inspect_reference(REF, transport=httpx.MockTransport(handler))
    assert error.value.exit_code == 4
    assert handler.call_count == 1
    assert "password" not in str(error.value) and "wrong" not in str(error.value)


@pytest.mark.parametrize(
    "headers",
    [
        {},
        [("WWW-Authenticate", CHALLENGE), ("WWW-Authenticate", CHALLENGE)],
    ],
)
def test_missing_or_multiple_challenges_denied(headers: Any) -> None:
    handler = Mock(return_value=httpx.Response(401, headers=headers))
    with pytest.raises(OciError, match="One anonymous"):
        inspect_reference(REF, transport=httpx.MockTransport(handler))
    assert handler.call_count == 1


@pytest.mark.parametrize("stage", ["manifest", "token", "authenticated"])
def test_all_redirects_rejected_without_follow_or_token_leak(stage: str) -> None:
    count = 0

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal count
        count += 1
        if (
            stage == "manifest"
            or (stage == "token" and count == 2)
            or (stage == "authenticated" and count == 3)
        ):
            return httpx.Response(307, headers={"Location": "http://evil.invalid/" + TOKEN})
        if count == 1:
            return httpx.Response(401, headers={"WWW-Authenticate": CHALLENGE})
        assert count == 2
        return httpx.Response(200, json={"token": TOKEN})

    with pytest.raises(OciError) as error:
        inspect_reference(REF, transport=httpx.MockTransport(handle))
    assert error.value.code == "REDIRECT_REJECTED"
    assert TOKEN not in str(error.value)
    assert count == {"manifest": 1, "token": 2, "authenticated": 3}[stage]


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"token": ""},
        {"token": 123},
        {"token": "a b"},
        {"token": "bad\r\nheader"},
        {"token": "x" * 8193},
        {"token": "á"},
        {"token": "a", "access_token": "b"},
    ],
)
def test_bad_tokens_are_sanitized(payload: dict[str, Any]) -> None:
    with pytest.raises(OciError) as error:
        parse_token(json.dumps(payload).encode())
    assert error.value.code == "AUTH_FAILED"
    assert "header" not in str(error.value)


@pytest.mark.parametrize("raw", [b'{"token":"secret","token":"other"}', b"[]", b"not-json"])
def test_ambiguous_token_json_denied(raw: bytes) -> None:
    with pytest.raises(OciError) as error:
        parse_token(raw)
    assert "secret" not in str(error.value)


def test_token_optional_service_scope_are_derived_locally() -> None:
    calls = 0

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(
                401, headers={"WWW-Authenticate": 'Bearer realm="https://registry.example/token"'}
            )
        if calls == 2:
            assert dict(request.url.params) == {
                "service": "registry.example",
                "scope": "repository:team/image:pull",
            }
            return httpx.Response(200, json={"token": TOKEN})
        return response()

    inspect_reference(REF, transport=httpx.MockTransport(handle))
    assert calls == 3


@pytest.mark.parametrize("status", [403, 404, 429, 500])
def test_http_errors_do_not_expose_response_bodies(status: int) -> None:
    handler = Mock(return_value=httpx.Response(status, content=TOKEN))
    with pytest.raises(OciError) as error:
        inspect_reference(REF, transport=httpx.MockTransport(handler))
    assert error.value.code == ("RATE_LIMITED" if status == 429 else "HTTP_ERROR")
    assert str(status) in str(error.value) and TOKEN not in str(error.value)
    assert handler.call_count == 1


@pytest.mark.parametrize("stage", ["token", "retry"])
def test_auth_denial_has_no_loop(stage: str) -> None:
    calls = 0

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1 or stage == "token" or calls == 3:
            return httpx.Response(401, headers={"WWW-Authenticate": CHALLENGE}, content=TOKEN)
        return httpx.Response(200, json={"token": TOKEN})

    with pytest.raises(OciError) as error:
        inspect_reference(REF, transport=httpx.MockTransport(handle))
    assert error.value.code == "AUTH_REQUIRED"
    assert calls == (2 if stage == "token" else 3)


@pytest.mark.parametrize(
    "error_type,code", [(httpx.ReadTimeout, "TIMEOUT"), (httpx.ConnectError, "NETWORK_ERROR")]
)
def test_network_failures_are_sanitized(error_type: type[httpx.RequestError], code: str) -> None:
    handler = Mock(side_effect=error_type("do-not-print-" + TOKEN))
    with pytest.raises(OciError) as error:
        inspect_reference(REF, transport=httpx.MockTransport(handler))
    assert error.value.code == code and TOKEN not in str(error.value)


def test_cooperative_deadline(monkeypatch: pytest.MonkeyPatch) -> None:
    clock = iter([0.0, 0.0, 31.0])
    monkeypatch.setattr("trustforge.oci.client.monotonic", lambda: next(clock))
    with pytest.raises(OciError) as error:
        inspect_reference(REF, transport=httpx.MockTransport(lambda request: response()))
    assert error.value.code == "TIMEOUT"


@pytest.mark.parametrize(
    "mode", ["declared-large", "stream-large", "compressed", "length-invalid", "length-short"]
)
def test_manifest_size_and_encoding_bounds(mode: str) -> None:
    headers = {"Content-Type": OCI_MANIFEST}
    stream = Chunks([b"x" * 65536] * 70)
    if mode == "declared-large":
        headers["Content-Length"] = str(MAX_MANIFEST_BYTES + 1)
    if mode == "compressed":
        headers["Content-Encoding"] = "gzip"
    if mode == "length-invalid":
        headers["Content-Length"] = "-1"
    if mode == "length-short":
        headers["Content-Length"] = "5"
        stream = Chunks([b"xx"])
    with pytest.raises(OciError) as error:
        inspect_reference(
            REF,
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, headers=headers, stream=stream)
            ),
        )
    assert error.value.code in {"RESPONSE_TOO_LARGE", "ENCODING_REJECTED", "INVALID_LENGTH"}
    if mode in ("declared-large", "compressed", "length-invalid"):
        assert stream.read_count == 0
    assert stream.read_count < 70 and stream.closed


def test_token_response_has_its_own_smaller_limit() -> None:
    calls = 0
    stream = Chunks([b"x" * (MAX_TOKEN_BYTES + 1)])

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(401, headers={"WWW-Authenticate": CHALLENGE})
        return httpx.Response(200, headers={"Content-Type": "application/json"}, stream=stream)

    with pytest.raises(OciError) as error:
        inspect_reference(REF, transport=httpx.MockTransport(handle))
    assert error.value.code == "RESPONSE_TOO_LARGE" and calls == 2
    assert stream.closed


@pytest.mark.parametrize("which", ["requested", "header"])
def test_received_manifest_digest_is_checked(which: str) -> None:
    value = REF if which == "header" else "registry.example/team/image@sha256:" + "f" * 64

    def handle(request: httpx.Request) -> httpx.Response:
        r = response()
        if which == "header":
            r.headers["Docker-Content-Digest"] = "sha256:" + "f" * 64
        return r

    with pytest.raises(OciError) as error:
        inspect_reference(value, transport=httpx.MockTransport(handle))
    assert error.value.code == "DIGEST_MISMATCH"


def test_absent_digest_header_is_reported_without_inventing_verification() -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        r = response()
        del r.headers["Docker-Content-Digest"]
        return r

    result = inspect_reference(REF, transport=httpx.MockTransport(handle))
    assert not result.digest_header_verified
    assert result.digest.startswith("sha256:")


@pytest.mark.parametrize(
    "raw,media,code",
    [
        (b"", OCI_MANIFEST, "MALFORMED_MANIFEST"),
        (b"[]", OCI_MANIFEST, "MALFORMED_MANIFEST"),
        (b'{"schemaVersion":2,"schemaVersion":2}', OCI_MANIFEST, "MALFORMED_MANIFEST"),
        (b"<html>private-body</html>", "text/html", "UNSUPPORTED_MEDIA_TYPE"),
    ],
)
def test_bad_manifest_response_is_sanitized(raw: bytes, media: str, code: str) -> None:
    with pytest.raises(OciError) as error:
        inspect_reference(
            REF,
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, content=raw, headers={"Content-Type": media})
            ),
        )
    assert error.value.code == code
    assert "private-body" not in str(error.value)


def test_inspection_does_not_read_local_credentials_or_write_files(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    secret = tmp_path / ".docker" / "config.json"
    secret.parent.mkdir()
    secret.write_text('{"auths":{"registry.example":{"auth":"fixture-only"}}}')
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    before = secret.read_bytes()
    original_open = Path.open

    def guarded_open(path: Path, *args: Any, **kwargs: Any) -> Any:
        assert path != secret, "local credential access attempted"
        return original_open(path, *args, **kwargs)

    with monkeypatch.context() as guard:
        guard.setattr(Path, "open", guarded_open)
        inspect_reference(REF, transport=httpx.MockTransport(lambda request: response()))
    assert secret.read_bytes() == before
    assert sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*")) == [
        ".docker",
        ".docker/config.json",
    ]


def test_ambient_proxy_and_auth_are_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    original = httpx.Client
    factory = Mock(wraps=original)
    monkeypatch.setattr("trustforge.oci.client.httpx.Client", factory)
    monkeypatch.setenv("HTTPS_PROXY", "http://user:password@evil.invalid")
    monkeypatch.setenv("SSL_CERT_FILE", "/not-read/untrusted-ca")
    inspect_reference(REF, transport=httpx.MockTransport(lambda request: response()))
    assert factory.call_args.kwargs["trust_env"] is False
    assert factory.call_args.kwargs["follow_redirects"] is False
    assert factory.call_args.kwargs["auth"] is None
