"""Offline platform selection regressions; no sockets or image/blob retrieval."""

import json
from pathlib import Path
from typing import Any

import httpx
import pytest
from typer.testing import CliRunner

from trustforge.cli import app
from trustforge.oci.client import PlatformInspection, inspect_reference
from trustforge.oci.digest import digest_bytes
from trustforge.oci.errors import OciError
from trustforge.oci.models import DOCKER_MANIFEST, MAX_MANIFEST_BYTES, OCI_INDEX, OCI_MANIFEST

REF = "registry.example/team/image:tag"
PREFIX = "/v2/team/image/manifests/"
CHILD = (Path(__file__).parent / "fixtures/oci/manifest.json").read_bytes()
TOKEN = "fixture-token.DO-NOT-PRINT"


def descriptor(**overrides: Any) -> dict[str, Any]:
    return {
        "mediaType": OCI_MANIFEST,
        "digest": digest_bytes(CHILD),
        "size": len(CHILD),
        "platform": {"os": "linux", "architecture": "amd64"},
        **overrides,
    }


def index(entries: list[dict[str, Any]]) -> bytes:
    return json.dumps({"schemaVersion": 2, "mediaType": OCI_INDEX, "manifests": entries}).encode()


def reply(raw: bytes, media: str) -> httpx.Response:
    return httpx.Response(
        200,
        content=raw,
        headers={"Content-Type": media, "Docker-Content-Digest": digest_bytes(raw)},
    )


def transport(
    root: bytes,
    calls: list[httpx.Request],
    *,
    child: bytes = CHILD,
    child_media: str = OCI_MANIFEST,
) -> httpx.MockTransport:
    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        assert request.method == "GET" and request.url.scheme == "https"
        assert request.url.host == "registry.example"
        assert request.url.path.startswith(PREFIX) and "/blobs/" not in request.url.path
        if len(calls) == 1:
            assert request.url.path == PREFIX + "tag"
            return reply(root, OCI_INDEX)
        assert len(calls) == 2 and request.url.path.startswith(PREFIX + "sha256:")
        return reply(child, child_media)

    return httpx.MockTransport(handle)


@pytest.mark.parametrize(
    "requested,declared",
    [
        ("linux/amd64", {"os": "linux", "architecture": "amd64"}),
        ("linux/arm64", {"os": "linux", "architecture": "arm64", "variant": "v8"}),
        ("linux/arm/v7", {"os": "linux", "architecture": "arm", "variant": "v7"}),
    ],
)
def test_exact_child_chain_and_stable_default(requested: str, declared: dict[str, str]) -> None:
    # External URLs and embedded data are ignored, not alternative download sources.
    root = index([descriptor(platform=declared, urls=["https://evil.invalid/blobs/x"], data="bad")])
    calls: list[httpx.Request] = []
    result = inspect_reference(REF, platform=requested, transport=transport(root, calls))
    assert isinstance(result, PlatformInspection) and len(calls) == 2
    assert result.digest == result.selection.index_digest == digest_bytes(root)
    assert result.selection.manifest_digest == digest_bytes(CHILD) != result.digest
    assert result.selection.manifest.kind == "manifest"
    assert result.selection.manifest.digest_header_verified
    assert result.selection.descriptor.platform is not None
    assert result.selection.requested_platform == requested
    assert calls[1].url.path == PREFIX + digest_bytes(CHILD)
    assert result.selection.resolved_reference == "registry.example/team/image@" + digest_bytes(
        CHILD
    )
    default_calls: list[httpx.Request] = []
    default = inspect_reference(REF, transport=transport(root, default_calls))
    assert len(default_calls) == 1 and "selection" not in default.model_dump()


@pytest.mark.parametrize(
    "value",
    ["", "amd64", "Linux/amd64", "linux/AMD64", "linux/arm/", "linux/a/b/c", "a/../x", "a/á"],
)
def test_invalid_selector_never_uses_network(value: str) -> None:
    def forbidden(request: httpx.Request) -> httpx.Response:
        pytest.fail("invalid platform attempted network")

    with pytest.raises(OciError) as error:
        inspect_reference(REF, platform=value, transport=httpx.MockTransport(forbidden))
    assert error.value.code == "INVALID_PLATFORM" and error.value.exit_code == 2


@pytest.mark.parametrize(
    "entries,code",
    [
        ([], "PLATFORM_NOT_FOUND"),
        ([descriptor(platform=None)], "PLATFORM_NOT_FOUND"),
        ([descriptor(platform={"os": "linux", "architecture": "arm64"})], "PLATFORM_NOT_FOUND"),
        ([descriptor(), descriptor()], "AMBIGUOUS_PLATFORM"),
        ([descriptor(mediaType=OCI_INDEX)], "UNSUPPORTED_PLATFORM_MANIFEST"),
        ([descriptor(mediaType="application/vnd.future+json")], "UNSUPPORTED_PLATFORM_MANIFEST"),
        ([descriptor(size=0)], "INVALID_PLATFORM_DESCRIPTOR"),
        ([descriptor(size=MAX_MANIFEST_BYTES + 1)], "INVALID_PLATFORM_DESCRIPTOR"),
        ([descriptor(digest="sha256:bad")], "MALFORMED_MANIFEST"),
        ([descriptor(digest="sha256:" + "A" * 64)], "MALFORMED_MANIFEST"),
        ([descriptor(size=-1)], "MALFORMED_MANIFEST"),
        ([descriptor(size=True)], "MALFORMED_MANIFEST"),
    ],
)
def test_bad_or_missing_descriptor_stops_before_child(
    entries: list[dict[str, Any]], code: str
) -> None:
    calls: list[httpx.Request] = []
    with pytest.raises(OciError) as error:
        inspect_reference(REF, platform="linux/amd64", transport=transport(index(entries), calls))
    assert error.value.code == code and len(calls) == 1


def test_variants_require_unambiguous_match() -> None:
    root = index(
        [
            descriptor(platform={"os": "linux", "architecture": "arm", "variant": variant})
            for variant in ("v6", "v7")
        ]
    )
    calls: list[httpx.Request] = []
    with pytest.raises(OciError) as error:
        inspect_reference(REF, platform="linux/arm", transport=transport(root, calls))
    assert error.value.code == "AMBIGUOUS_PLATFORM" and len(calls) == 1
    assert isinstance(
        inspect_reference(REF, platform="linux/arm/v7", transport=transport(root, [])),
        PlatformInspection,
    )
    with pytest.raises(OciError) as error:
        inspect_reference(REF, platform="linux/arm/v8", transport=transport(root, []))
    assert error.value.code == "PLATFORM_NOT_FOUND"


@pytest.mark.parametrize(
    "change,code",
    [
        ({"digest": "sha256:" + "f" * 64}, "DIGEST_MISMATCH"),
        ({"size": len(CHILD) + 1}, "DESCRIPTOR_SIZE_MISMATCH"),
        ({"size": len(CHILD) - 1}, "RESPONSE_TOO_LARGE"),
        ({"mediaType": DOCKER_MANIFEST}, "DESCRIPTOR_MEDIA_MISMATCH"),
    ],
)
def test_descriptor_must_match_received_child(change: dict[str, Any], code: str) -> None:
    calls: list[httpx.Request] = []
    with pytest.raises(OciError) as error:
        inspect_reference(
            REF, platform="linux/amd64", transport=transport(index([descriptor(**change)]), calls)
        )
    assert error.value.code == code and len(calls) == 2


@pytest.mark.parametrize("status", [401, 404, 429, 500, 307])
def test_child_failures_are_not_partial_success(status: int) -> None:
    calls: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if len(calls) == 1:
            return reply(index([descriptor()]), OCI_INDEX)
        return httpx.Response(status, headers={"Location": "https://evil.invalid/"}, content=TOKEN)

    with pytest.raises(OciError) as error:
        inspect_reference(REF, platform="linux/amd64", transport=httpx.MockTransport(handle))
    assert len(calls) == 2 and TOKEN not in str(error.value)


def test_child_auth_has_same_scope_boundaries_and_six_request_limit() -> None:
    calls: list[httpx.Request] = []
    root = index([descriptor()])

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        count = len(calls)
        assert "cookie" not in request.headers and request.url.host == "registry.example"
        if count in (1, 4):
            assert "authorization" not in request.headers
            return httpx.Response(
                401,
                headers={
                    "WWW-Authenticate": 'Bearer realm="https://registry.example/token",'
                    'scope="repository:team/image:pull"'
                },
            )
        if count in (2, 5):
            assert request.url.path == "/token" and "authorization" not in request.headers
            assert request.url.params["scope"] == "repository:team/image:pull"
            return httpx.Response(200, json={"token": TOKEN}, headers={"Set-Cookie": "x=secret"})
        assert count in (3, 6) and request.headers["authorization"] == "Bearer " + TOKEN
        assert request.url.path == PREFIX + ("tag" if count == 3 else digest_bytes(CHILD))
        return reply(root if count == 3 else CHILD, OCI_INDEX if count == 3 else OCI_MANIFEST)

    result = inspect_reference(REF, platform="linux/amd64", transport=httpx.MockTransport(handle))
    assert len(calls) == 6 and TOKEN not in result.model_dump_json()


def test_standalone_manifest_cannot_prove_platform_without_config() -> None:
    calls: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return reply(CHILD, OCI_MANIFEST)

    with pytest.raises(OciError) as error:
        inspect_reference(REF, platform="linux/amd64", transport=httpx.MockTransport(handle))
    assert error.value.code == "PLATFORM_UNVERIFIABLE" and len(calls) == 1


@pytest.mark.parametrize("machine", [False, True])
def test_platform_cli_json_and_rich(monkeypatch: pytest.MonkeyPatch, machine: bool) -> None:
    root = index([descriptor()])
    calls: list[httpx.Request] = []

    def inspect(value: str, *, platform: str | None = None) -> object:
        return inspect_reference(value, platform=platform, transport=transport(root, calls))

    monkeypatch.setattr("trustforge.oci_cli.inspect_reference", inspect)
    result = CliRunner().invoke(
        app, ["oci", "inspect", REF, "--platform", "linux/amd64"] + (["--json"] if machine else [])
    )
    assert result.exit_code == 0 and result.stderr == "" and len(calls) == 2
    if machine:
        payload = json.loads(result.stdout)
        assert payload["schema_version"] == 1
        assert payload["digest"] == payload["selection"]["index_digest"] == digest_bytes(root)
        assert payload["selection"]["manifest_digest"] == digest_bytes(CHILD)
        assert payload["selection"]["descriptor"]["mediaType"] == OCI_MANIFEST
    else:
        assert "Index digest:" in result.stdout and "Child manifest digest:" in result.stdout
        assert "Selected platform: linux/amd64" in result.stdout
        assert "authenticity and deployment are not verified" in result.stdout


def test_cli_invalid_platform_has_json_error_and_empty_stdout() -> None:
    result = CliRunner().invoke(app, ["oci", "inspect", REF, "--platform", "bad", "--json"])
    assert result.exit_code == 2 and result.stdout == ""
    assert json.loads(result.stderr)["error"]["code"] == "INVALID_PLATFORM"


def test_platform_option_requires_value() -> None:
    result = CliRunner().invoke(app, ["oci", "inspect", REF, "--platform"])
    assert result.exit_code == 2 and "requires an argument" in result.stderr


def test_subcommand_help_renders_platform_option() -> None:
    result = CliRunner().invoke(app, ["oci", "inspect", "--help"])
    assert result.exit_code == 0 and "--platform" in result.stdout
    assert "Traceback" not in result.output


@pytest.mark.parametrize(
    "mode,code",
    [
        ("header-digest", "DIGEST_MISMATCH"),
        ("malformed", "MALFORMED_MANIFEST"),
        ("compressed", "ENCODING_REJECTED"),
        ("unsafe-auth", "AUTH_CHALLENGE_REJECTED"),
    ],
)
def test_child_has_same_parser_and_transport_guards(mode: str, code: str) -> None:
    child = b"[" + b" " * (len(CHILD) - 1) if mode == "malformed" else CHILD
    root = index([descriptor(digest=digest_bytes(child))])
    calls: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if len(calls) == 1:
            return reply(root, OCI_INDEX)
        assert len(calls) == 2
        if mode == "unsafe-auth":
            return httpx.Response(
                401, headers={"WWW-Authenticate": 'Bearer realm="https://evil.invalid/token"'}
            )
        response = reply(child, OCI_MANIFEST)
        if mode == "header-digest":
            response.headers["Docker-Content-Digest"] = "sha256:" + "e" * 64
        if mode == "compressed":
            response.headers["Content-Encoding"] = "gzip"
        return response

    with pytest.raises(OciError) as error:
        inspect_reference(REF, platform="linux/amd64", transport=httpx.MockTransport(handle))
    assert error.value.code == code and len(calls) == 2


def test_parent_and_child_share_one_time_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    clock = iter([0.0, 0.0, 0.0, 0.0, 31.0])
    monkeypatch.setattr("trustforge.oci.client.monotonic", lambda: next(clock))
    calls: list[httpx.Request] = []
    with pytest.raises(OciError) as error:
        inspect_reference(
            REF, platform="linux/amd64", transport=transport(index([descriptor()]), calls)
        )
    assert error.value.code == "TIMEOUT" and len(calls) == 1
