"""Offline referrers protocol/negative tests; no sockets, payloads or crypto tools."""

import json
from pathlib import Path
from typing import Any

import httpx
import pytest
from rich.text import Text
from typer.testing import CliRunner

from trustforge.cli import app
from trustforge.oci.digest import digest_bytes
from trustforge.oci.errors import OciError
from trustforge.oci.models import MAX_MANIFEST_BYTES, OCI_INDEX, OCI_MANIFEST
from trustforge.oci.referrers import list_referrers

DIGEST = "sha256:" + "a" * 64
REF = "registry.example/team/image@" + DIGEST
API = "/v2/team/image/referrers/" + DIGEST
FALLBACK = "/v2/team/image/manifests/sha256-" + "a" * 64
ARTIFACT = "application/vnd.example.sbom.v1+json"
TOKEN = "fixture-token.NEVER-PRINT"


def descriptor(**overrides: Any) -> dict[str, Any]:
    return {
        "mediaType": OCI_MANIFEST,
        "digest": "sha256:" + "b" * 64,
        "size": 123,
        "artifactType": ARTIFACT,
        "annotations": {"org.example.kind": "sbom"},
        **overrides,
    }


def raw_index(items: list[dict[str, Any]]) -> bytes:
    return json.dumps({"schemaVersion": 2, "mediaType": OCI_INDEX, "manifests": items}).encode()


def reply(items: list[dict[str, Any]], **headers: str) -> httpx.Response:
    raw = raw_index(items)
    return httpx.Response(
        200,
        stream=httpx.ByteStream(raw),
        headers={
            "Content-Type": OCI_INDEX,
            "Docker-Content-Digest": digest_bytes(raw),
            **headers,
        },
    )


@pytest.mark.parametrize("empty", [False, True])
def test_api_claims_and_empty_are_not_authenticated_evidence(empty: bool) -> None:
    calls: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        assert request.method == "GET" and request.url.path == API
        assert request.headers["accept"] == OCI_INDEX and not request.url.query
        return reply(
            [] if empty else [descriptor(urls=["https://evil.invalid/blobs/x"], data="bad")]
        )

    result = list_referrers(REF, transport=httpx.MockTransport(handle))
    assert len(calls) == 1 and result.source == "referrers_api" and result.api_status == "available"
    assert result.subject_digest == DIGEST and result.subject_resolution == "supplied_digest"
    assert result.status == ("empty" if empty else "listed")
    assert not result.association_verified and not result.authenticity_verified
    assert result.digest_header_verified and result.list_digest != DIGEST
    if not empty:
        item = result.referrers[0]
        assert item.artifact_type == ARTIFACT and item.annotations == {"org.example.kind": "sbom"}
        assert "urls" not in item.model_dump() and "data" not in item.model_dump()


def test_tag_is_resolved_once_with_verified_manifest_get() -> None:
    raw = (Path(__file__).parent / "fixtures/oci/manifest.json").read_bytes()
    calls: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if len(calls) == 1:
            assert request.url.path == "/v2/team/image/manifests/tag"
            return httpx.Response(200, content=raw, headers={"Content-Type": OCI_MANIFEST})
        assert len(calls) == 2 and request.url.path == "/v2/team/image/referrers/" + digest_bytes(
            raw
        )
        return reply([])

    result = list_referrers(
        "registry.example/team/image:tag", transport=httpx.MockTransport(handle)
    )
    assert result.subject_resolution == "manifest_get" and result.subject_digest == digest_bytes(
        raw
    )


@pytest.mark.parametrize("missing", [False, True])
def test_only_standard_oci_tag_fallback_and_no_false_empty(missing: bool) -> None:
    paths: list[str] = []

    def handle(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        assert request.method == "GET" and not request.url.query
        if len(paths) == 1:
            assert request.url.path == API
            return httpx.Response(404, content=TOKEN)
        assert len(paths) == 2 and request.url.path == FALLBACK
        return httpx.Response(404, content=TOKEN) if missing else reply([descriptor()])

    if missing:
        with pytest.raises(OciError) as error:
            list_referrers(REF, transport=httpx.MockTransport(handle))
        assert error.value.code == "REFERRERS_UNAVAILABLE" and error.value.exit_code == 6
        assert TOKEN not in str(error.value)
    else:
        result = list_referrers(REF, transport=httpx.MockTransport(handle))
        assert result.source == "oci_tag_schema" and result.api_status == "not_found"
        assert result.status == "listed"
    assert len(paths) == 2


@pytest.mark.parametrize("server_applied", [False, True])
def test_filter_enforced_locally_and_server_claim_validated(server_applied: bool) -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        assert dict(request.url.params) == {"artifactType": ARTIFACT}
        entries = [descriptor()]
        if not server_applied:
            entries.append(
                descriptor(digest="sha256:" + "c" * 64, artifactType="application/other")
            )
        return reply(entries, **({"OCI-Filters-Applied": "artifactType"} if server_applied else {}))

    result = list_referrers(REF, artifact_type=ARTIFACT, transport=httpx.MockTransport(handle))
    assert len(result.referrers) == 1 and result.referrers[0].artifact_type == ARTIFACT


@pytest.mark.parametrize(
    "items,headers,code",
    [
        ([descriptor(), descriptor()], {}, "DUPLICATE_REFERRER"),
        ([descriptor(digest="sha256:bad")], {}, "MALFORMED_MANIFEST"),
        ([descriptor(size=-1)], {}, "MALFORMED_MANIFEST"),
        ([descriptor(size=True)], {}, "MALFORMED_MANIFEST"),
        ([descriptor(artifactType=123)], {}, "MALFORMED_REFERRERS"),
        ([descriptor(artifactType="not-a-media-type")], {}, "MALFORMED_REFERRERS"),
        ([descriptor(annotations={"key": 123})], {}, "MALFORMED_REFERRERS"),
        ([descriptor(annotations=None)], {}, "MALFORMED_REFERRERS"),
        (
            [descriptor(artifactType="application/other")],
            {"OCI-Filters-Applied": "artifactType"},
            "FILTER_MISMATCH",
        ),
        ([], {"OCI-Filters-Applied": "unsupported"}, "UNEXPECTED_FILTER"),
        ([], {"OCI-Filters-Applied": "artifactType, artifactType"}, "UNEXPECTED_FILTER"),
        ([], {"Link": '<https://evil.invalid/?token=secret>; rel="next"'}, "INVALID_PAGE_LINK"),
        ([], {"Docker-Content-Digest": "sha256:" + "f" * 64}, "DIGEST_MISMATCH"),
        ([], {"Content-Encoding": "gzip"}, "ENCODING_REJECTED"),
        ([], {"Content-Length": str(MAX_MANIFEST_BYTES + 1)}, "RESPONSE_TOO_LARGE"),
    ],
)
def test_malformed_or_inconsistent_list_is_not_empty_success(
    items: list[dict[str, Any]], headers: dict[str, str], code: str
) -> None:
    calls: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return reply(items, **headers)

    with pytest.raises(OciError) as error:
        list_referrers(REF, artifact_type=ARTIFACT, transport=httpx.MockTransport(handle))
    assert error.value.code == code and len(calls) == 1
    assert "secret" not in str(error.value)


@pytest.mark.parametrize(
    "raw,media",
    [
        (b"", OCI_INDEX),
        (b"[]", OCI_INDEX),
        (b'{"schemaVersion":2,"schemaVersion":2}', OCI_INDEX),
        (b"<html>private</html>", "text/html"),
        (raw_index([descriptor()] * 1025), OCI_INDEX),
    ],
)
def test_bad_index_and_limits(raw: bytes, media: str) -> None:
    with pytest.raises(OciError):
        list_referrers(
            REF,
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, content=raw, headers={"Content-Type": media})
            ),
        )


@pytest.mark.parametrize("status", [301, 307, 400, 403, 405, 429, 500, 501])
def test_errors_other_than_404_never_trigger_fallback(status: int) -> None:
    calls: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(status, content=TOKEN, headers={"Location": "https://evil.invalid"})

    with pytest.raises(OciError) as error:
        list_referrers(REF, transport=httpx.MockTransport(handle))
    assert len(calls) == 1 and TOKEN not in str(error.value)


def test_api_and_fallback_auth_have_independent_same_repo_scope() -> None:
    calls: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        n = len(calls)
        assert request.method == "GET" and "cookie" not in request.headers
        if n in (1, 4):
            assert request.url.path == (API if n == 1 else FALLBACK)
            assert "authorization" not in request.headers
            return httpx.Response(
                401,
                headers={
                    "WWW-Authenticate": 'Bearer realm="https://registry.example/token"',
                    "Set-Cookie": "x=never-forward",
                },
            )
        if n in (2, 5):
            assert request.url.path == "/token" and "authorization" not in request.headers
            assert request.url.params["scope"] == "repository:team/image:pull"
            return httpx.Response(200, json={"token": TOKEN})
        assert n in (3, 6) and request.headers["authorization"] == "Bearer " + TOKEN
        assert request.url.path == (API if n == 3 else FALLBACK)
        return httpx.Response(404) if n == 3 else reply([])

    result = list_referrers(REF, transport=httpx.MockTransport(handle))
    assert result.source == "oci_tag_schema" and result.status == "empty" and len(calls) == 6
    assert TOKEN not in result.model_dump_json()


@pytest.mark.parametrize(
    "filter_value", ["bad", "application/x?secret=1", "text/plain; charset=x", ""]
)
def test_invalid_filter_never_uses_network(filter_value: str) -> None:
    def forbidden(request: httpx.Request) -> httpx.Response:
        pytest.fail("invalid filter attempted network")

    with pytest.raises(OciError) as error:
        list_referrers(REF, artifact_type=filter_value, transport=httpx.MockTransport(forbidden))
    assert error.value.code == "INVALID_ARTIFACT_TYPE" and error.value.exit_code == 2


@pytest.mark.parametrize("machine", [False, True])
def test_referrers_cli_json_and_rich(monkeypatch: pytest.MonkeyPatch, machine: bool) -> None:
    def inspect(value: str, *, artifact_type: str | None = None) -> Any:
        return list_referrers(
            value,
            artifact_type=artifact_type,
            transport=httpx.MockTransport(lambda request: reply([descriptor()])),
        )

    monkeypatch.setattr("trustforge.oci_cli.list_referrers", inspect)
    result = CliRunner().invoke(app, ["oci", "referrers", REF] + (["--json"] if machine else []))
    assert result.exit_code == 0 and result.stderr == ""
    if machine:
        data = json.loads(result.stdout)
        assert data["operation"] == "referrers" and data["status"] == "listed"
        assert data["referrers"][0]["artifactType"] == ARTIFACT
        assert data["association_verified"] is False and data["authenticity_verified"] is False
    else:
        text = " ".join(Text.from_ansi(result.stdout).plain.split())
        assert "subject associations and authenticity are not verified" in text


def test_referrers_cli_errors_and_help(monkeypatch: pytest.MonkeyPatch) -> None:
    def unavailable(value: str, *, artifact_type: str | None = None) -> Any:
        return list_referrers(
            value, transport=httpx.MockTransport(lambda request: httpx.Response(404))
        )

    monkeypatch.setattr("trustforge.oci_cli.list_referrers", unavailable)
    result = CliRunner().invoke(app, ["oci", "referrers", REF, "--json"])
    assert result.exit_code == 6 and result.stdout == ""
    assert json.loads(result.stderr)["error"]["code"] == "REFERRERS_UNAVAILABLE"
    help_result = CliRunner().invoke(app, ["oci", "referrers", "--help"])
    assert (
        help_result.exit_code == 0 and "--artifact-type" in Text.from_ansi(help_result.stdout).plain
    )


def test_fallback_malformed_index_never_means_no_referrers() -> None:
    calls = 0

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(404)
        return httpx.Response(200, content=b"[]", headers={"Content-Type": OCI_INDEX})

    with pytest.raises(OciError) as error:
        list_referrers(REF, transport=httpx.MockTransport(handle))
    assert error.value.code == "MALFORMED_MANIFEST" and calls == 2


def test_fallback_filter_is_local_not_an_untrusted_query() -> None:
    calls = 0

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            assert request.url.params["artifactType"] == ARTIFACT
            return httpx.Response(404)
        assert not request.url.query and request.url.path == FALLBACK
        return reply([descriptor(artifactType="application/other")])

    result = list_referrers(REF, artifact_type=ARTIFACT, transport=httpx.MockTransport(handle))
    assert result.source == "oci_tag_schema" and result.status == "empty" and not result.referrers


def test_optional_fields_unknown_types_and_wire_aliases() -> None:
    item = descriptor(mediaType=OCI_INDEX)
    item.pop("artifactType")
    item["artifact_type"] = "application/not-a-wire-field"
    result = list_referrers(REF, transport=httpx.MockTransport(lambda request: reply([item])))
    assert result.referrers[0].artifact_type is None
    assert result.referrers[0].media_type == OCI_INDEX


@pytest.mark.parametrize("stage", ["unsafe", "token-denied", "retry-denied"])
def test_referrer_auth_failure_is_bounded(stage: str) -> None:
    calls = 0

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            realm = (
                "https://evil.invalid/token"
                if stage == "unsafe"
                else "https://registry.example/token"
            )
            return httpx.Response(401, headers={"WWW-Authenticate": f'Bearer realm="{realm}"'})
        if calls == 2 and stage != "token-denied":
            return httpx.Response(200, json={"token": TOKEN})
        return httpx.Response(401, content=TOKEN)

    with pytest.raises(OciError) as error:
        list_referrers(REF, transport=httpx.MockTransport(handle))
    assert calls == {"unsafe": 1, "token-denied": 2, "retry-denied": 3}[stage]
    assert error.value.exit_code == 4 and TOKEN not in str(error.value)


def test_referrers_share_budget_across_api_and_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("trustforge.oci.referrers.monotonic", lambda: 0.0)
    clock = iter([0.0, 31.0])
    monkeypatch.setattr("trustforge.oci.client.monotonic", lambda: next(clock))
    calls = 0

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(404)

    with pytest.raises(OciError) as error:
        list_referrers(REF, transport=httpx.MockTransport(handle))
    assert calls == 1 and error.value.code == "TIMEOUT"
