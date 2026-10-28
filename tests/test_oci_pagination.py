"""Deterministic multi-page protocol tests; all HTTP is MockTransport, never live."""

import json
from typing import Any

import httpx
import pytest
from rich.text import Text
from typer.testing import CliRunner

from trustforge.cli import app
from trustforge.oci.digest import digest_bytes
from trustforge.oci.errors import OciError
from trustforge.oci.models import MAX_MANIFEST_BYTES, OCI_INDEX, OCI_MANIFEST
from trustforge.oci.referrers import PaginatedReferrersReport, list_referrers

DIGEST = "sha256:" + "a" * 64
REF = "registry.example/team/image@" + DIGEST
PATH = "/v2/team/image/referrers/" + DIGEST
URL = "https://registry.example" + PATH
ARTIFACT = "application/vnd.example.sbom+json"


def descriptor(number: int, **overrides: Any) -> dict[str, Any]:
    return {
        "mediaType": OCI_MANIFEST,
        "digest": "sha256:" + f"{number:064x}",
        "size": 123,
        "artifactType": ARTIFACT,
        **overrides,
    }


def raw(items: list[dict[str, Any]]) -> bytes:
    return json.dumps({"schemaVersion": 2, "mediaType": OCI_INDEX, "manifests": items}).encode()


def response(items: list[dict[str, Any]], link: str | None = None, **extra: str) -> httpx.Response:
    body = raw(items)
    headers = {
        "Content-Type": OCI_INDEX,
        "Content-Length": str(len(body)),
        "Docker-Content-Digest": digest_bytes(body),
        **extra,
    }
    if link is not None:
        headers["Link"] = link
    return httpx.Response(200, headers=headers, stream=httpx.ByteStream(body))


@pytest.mark.parametrize(
    "target",
    [
        "?last=p2",
        PATH + "?last=p2",
        URL + "?last=p2",
        "https://registry.example:443" + PATH + "?last=p2",
    ],
)
@pytest.mark.parametrize("relation", ['rel="next"', 'rel=next; title="page, two"'])
def test_next_link_and_json_separate_counts_and_hashes(target: str, relation: str) -> None:
    calls: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        assert request.method == "GET" and request.url.scheme == "https"
        assert request.url.host == "registry.example" and request.url.path == PATH
        if len(calls) == 1:
            return response([descriptor(1)], f"<{target}>; {relation}")
        assert len(calls) == 2 and dict(request.url.params) == {"last": "p2"}
        return response([descriptor(2)])

    result = list_referrers(REF, transport=httpx.MockTransport(handle))
    assert isinstance(result, PaginatedReferrersReport) and len(calls) == 2
    p = result.pagination
    assert p.pages_queried == 2 and p.observed_descriptors == p.returned_descriptors == 2
    assert p.total_size_bytes == sum(len(raw([descriptor(n)])) for n in (1, 2))
    assert [page.digest for page in p.pages] == [digest_bytes(raw([descriptor(n)])) for n in (1, 2)]
    assert all(page.digest_header_verified for page in p.pages)
    assert result.list_digest == p.pages[0].digest and result.list_digest_scope == "first_page"
    assert result.schema_version == 1 and len(result.referrers) == 2
    assert not result.association_verified and not result.authenticity_verified


def test_one_page_contract_is_unchanged() -> None:
    result = list_referrers(REF, transport=httpx.MockTransport(lambda request: response([])))
    assert (
        "pagination" not in result.model_dump() and "list_digest_scope" not in result.model_dump()
    )
    assert result.list_digest == digest_bytes(raw([])) and result.status == "empty"
    assert result.schema_version == 1


@pytest.mark.parametrize(
    "link",
    [
        "",
        '?last=p2; rel="next"',
        "<?last=p2>",
        '<?last=p2>; rel="prev"',
        '<?last=p2>; rel="next prev"',
        '<?last=p2>; rel="next"; rel="next"',
        '<?last=p2>; rel="next", <?last=p3>; rel="next"',
        '<?last=p2>; rel="next"; anchor="https://evil.invalid/"',
        "<https://evil.invalid" + PATH + '?last=p2>; rel="next"',
        "<http://registry.example" + PATH + '?last=p2>; rel="next"',
        "<https://registry.example:444" + PATH + '?last=p2>; rel="next"',
        "<https://user:secret@registry.example" + PATH + '?last=p2>; rel="next"',
        '<?last=p2#fragment>; rel="next"',
        '<?last=p2#>; rel="next"',
        "<//registry.example" + PATH + '?last=p2>; rel="next"',
        "</v2/other/image/referrers/" + DIGEST + '?last=p2>; rel="next"',
        "</v2/team/image/referrers/sha256:" + "b" * 64 + '?last=p2>; rel="next"',
        "</v2/team/image/blobs/" + DIGEST + '?last=p2>; rel="next"',
        "<" + PATH + "/../" + DIGEST + '?last=p2>; rel="next"',
        "</v2/team/image/referrers/%73ha256:" + "a" * 64 + '?last=p2>; rel="next"',
        '<?last=p\t2>; rel="next"',
        '<?last=p%xx>; rel="next"',
        '<?last=a&last=b>; rel="next"',
        '<?token=secret>; rel="next"',
        '<?n=0&last=p2>; rel="next"',
        '<?n=-1&last=p2>; rel="next"',
        '<?n=1025&last=p2>; rel="next"',
        '<?last=>; rel="next"',
        '<?last=%C3%A1>; rel="next"',
        '<?last=p2>; rel="next" trailing',
        '<?artifactType=application/other&last=p2>; rel="next"',
        "<?last=" + "x" * 4096 + '>; rel="next"',
    ],
)
def test_unsafe_or_ambiguous_link_never_requests_next(link: str) -> None:
    calls = 0

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        assert calls == 1, "unsafe Link was followed"
        return response([descriptor(1)], link)

    with pytest.raises(OciError) as error:
        list_referrers(REF, transport=httpx.MockTransport(handle))
    assert error.value.code == "INVALID_PAGE_LINK" and "secret" not in str(error.value)


def test_multiple_link_headers_are_ambiguous() -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        r = response([])
        r.headers = httpx.Headers(
            [
                *r.headers.multi_items(),
                ("Link", '<?last=a>; rel="next"'),
                ("Link", '<?last=b>; rel="next"'),
            ]
        )
        return r

    with pytest.raises(OciError, match="ambiguous"):
        list_referrers(REF, transport=httpx.MockTransport(handle))


@pytest.mark.parametrize("cycle", ["initial", "reordered"])
def test_cycles_include_normalized_query_order_and_encoding(cycle: str) -> None:
    calls = 0

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if cycle == "initial":
            assert calls == 1
            return response([], f'<{PATH}>; rel="next"')
        if calls == 1:
            return response([descriptor(1)], '<?last=a%62&n=01>; rel="next"')
        assert calls == 2 and dict(request.url.params) == {"last": "ab", "n": "1"}
        return response([descriptor(2)], '<?n=1&last=ab>; rel="next"')

    with pytest.raises(OciError) as error:
        list_referrers(REF, transport=httpx.MockTransport(handle))
    assert error.value.code == "REFERRERS_PAGE_CYCLE"


def test_page_limit_stops_before_sixth_request() -> None:
    calls = 0

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        assert calls <= 5
        return response([descriptor(calls)], f'<?last=p{calls}>; rel="next"')

    with pytest.raises(OciError) as error:
        list_referrers(REF, transport=httpx.MockTransport(handle))
    assert error.value.code == "REFERRERS_PAGE_LIMIT" and calls == 5


@pytest.mark.parametrize("changed", [False, True])
def test_repeated_or_inconsistent_digest_between_pages_fails(changed: bool) -> None:
    calls = 0

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return response(
            [descriptor(1, size=124 if changed and calls == 2 else 123)],
            '<?last=p2>; rel="next"' if calls == 1 else None,
        )

    with pytest.raises(OciError) as error:
        list_referrers(REF, transport=httpx.MockTransport(handle))
    assert calls == 2 and error.value.code == (
        "INCONSISTENT_REFERRER" if changed else "DUPLICATE_REFERRER"
    )


def test_global_descriptor_limit_applies_across_pages() -> None:
    calls = 0

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        start = calls * 600
        calls += 1
        return response(
            [descriptor(n) for n in range(start, start + 600)],
            '<?last=p2>; rel="next"' if calls == 1 else None,
        )

    with pytest.raises(OciError) as error:
        list_referrers(REF, transport=httpx.MockTransport(handle))
    assert calls == 2 and error.value.code == "REFERRERS_DESCRIPTOR_LIMIT"


def test_global_byte_budget_is_not_reset_per_page() -> None:
    calls = 0
    entries = [descriptor(1, annotations={"padding": "x" * (MAX_MANIFEST_BYTES // 2 + 1)})]

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return response(entries, '<?last=p2>; rel="next"' if calls == 1 else None)

    with pytest.raises(OciError) as error:
        list_referrers(REF, transport=httpx.MockTransport(handle))
    assert calls == 2 and error.value.code == "RESPONSE_TOO_LARGE"


@pytest.mark.parametrize("status", [301, 307, 400, 401, 403, 404, 429, 500])
def test_next_page_errors_do_not_return_partial_list_or_fallback(status: int) -> None:
    calls = 0

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        assert request.url.path == PATH and calls <= 2
        if calls == 1:
            return response([descriptor(1)], '<?last=p2>; rel="next"')
        return httpx.Response(
            status, headers={"Location": "https://evil.invalid/"}, content="private"
        )

    with pytest.raises(OciError) as error:
        list_referrers(REF, transport=httpx.MockTransport(handle))
    assert calls == 2 and "private" not in str(error.value)
    if status == 404:
        assert error.value.code == "REFERRERS_PAGE_ERROR"


@pytest.mark.parametrize("claimed", [False, True])
def test_filter_persists_and_local_filter_runs_on_every_page(claimed: bool) -> None:
    calls = 0

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        assert request.url.params["artifactType"] == ARTIFACT
        if calls == 1:
            return response([descriptor(1)], '<?last=p2>; rel="next"')
        assert calls == 2
        return response(
            [descriptor(2, artifactType="application/other")],
            **({"OCI-Filters-Applied": "artifactType"} if claimed else {}),
        )

    if claimed:
        with pytest.raises(OciError) as error:
            list_referrers(REF, artifact_type=ARTIFACT, transport=httpx.MockTransport(handle))
        assert error.value.code == "FILTER_MISMATCH"
    else:
        result = list_referrers(REF, artifact_type=ARTIFACT, transport=httpx.MockTransport(handle))
        assert isinstance(result, PaginatedReferrersReport)
        assert (
            result.pagination.observed_descriptors == 2
            and result.pagination.returned_descriptors == 1
        )


def test_filter_cannot_change_between_pages() -> None:
    calls = 0

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        assert calls == 1
        return response([], '<?last=p2&artifactType=application/other>; rel="next"')

    with pytest.raises(OciError) as error:
        list_referrers(REF, artifact_type=ARTIFACT, transport=httpx.MockTransport(handle))
    assert error.value.code == "INVALID_PAGE_LINK"


def test_auth_is_independent_and_bound_on_each_page() -> None:
    calls = 0
    token = "fixture-token.NEVER-PRINT"

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        assert request.method == "GET" and "cookie" not in request.headers
        if calls in (1, 4):
            assert request.url.path == PATH and "authorization" not in request.headers
            return httpx.Response(
                401,
                headers={
                    "WWW-Authenticate": 'Bearer realm="https://registry.example/token"',
                    "Set-Cookie": "x=never-forward",
                },
            )
        if calls in (2, 5):
            assert request.url.path == "/token" and "authorization" not in request.headers
            assert request.url.params["scope"] == "repository:team/image:pull"
            return httpx.Response(200, json={"token": token})
        assert calls in (3, 6) and request.headers["authorization"] == "Bearer " + token
        assert dict(request.url.params) == ({} if calls == 3 else {"last": "p2"})
        return response([descriptor(calls)], '<?last=p2>; rel="next"' if calls == 3 else None)

    result = list_referrers(REF, transport=httpx.MockTransport(handle))
    assert calls == 6 and token not in result.model_dump_json()


def test_deadline_is_shared_across_pages(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("trustforge.oci.referrers.monotonic", lambda: 0.0)
    clock = iter([0.0, 0.0, 0.0, 31.0])
    monkeypatch.setattr("trustforge.oci.client.monotonic", lambda: next(clock))
    calls = 0

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return response([], '<?last=p2>; rel="next"')

    with pytest.raises(OciError) as error:
        list_referrers(REF, transport=httpx.MockTransport(handle))
    assert calls == 1 and error.value.code == "TIMEOUT"


@pytest.mark.parametrize("machine", [False, True])
def test_cli_complete_multi_page_output(monkeypatch: pytest.MonkeyPatch, machine: bool) -> None:
    calls = 0

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return response([descriptor(calls)], '<?last=p2>; rel="next"' if calls == 1 else None)

    def inspect(value: str, *, artifact_type: str | None = None) -> Any:
        return list_referrers(
            value, artifact_type=artifact_type, transport=httpx.MockTransport(handle)
        )

    monkeypatch.setattr("trustforge.oci_cli.list_referrers", inspect)
    result = CliRunner().invoke(app, ["oci", "referrers", REF] + (["--json"] if machine else []))
    assert result.exit_code == 0 and result.stderr == "" and calls == 2
    if machine:
        data = json.loads(result.stdout)
        assert data["pagination"]["pages_queried"] == 2 and len(data["referrers"]) == 2
        assert data["list_digest_scope"] == "first_page"
    else:
        assert "Pages: 2; observed descriptors: 2" in " ".join(
            Text.from_ansi(result.stdout).plain.split()
        )


def test_cli_failure_after_first_page_keeps_stdout_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return (
            response([descriptor(1)], '<?last=p2>; rel="next"')
            if calls == 1
            else httpx.Response(500)
        )

    def inspect(value: str, *, artifact_type: str | None = None) -> Any:
        return list_referrers(value, transport=httpx.MockTransport(handle))

    monkeypatch.setattr("trustforge.oci_cli.list_referrers", inspect)
    result = CliRunner().invoke(app, ["oci", "referrers", REF, "--json"])
    assert result.exit_code == 6 and result.stdout == ""
    assert json.loads(result.stderr)["error"]["code"] == "HTTP_ERROR"


@pytest.mark.parametrize(
    "mode,code",
    [
        ("bad-json", "MALFORMED_MANIFEST"),
        ("wrong-hash", "DIGEST_MISMATCH"),
        ("wrong-media", "UNSUPPORTED_MEDIA_TYPE"),
        ("bad-annotations", "MALFORMED_REFERRERS"),
    ],
)
def test_each_page_is_independently_validated(mode: str, code: str) -> None:
    calls = 0

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return response([descriptor(1)], '<?last=p2>; rel="next"')
        assert calls == 2
        if mode == "bad-json":
            return httpx.Response(200, content=b"[]", headers={"Content-Type": OCI_INDEX})
        if mode == "bad-annotations":
            return response([descriptor(2, annotations={"key": 123})])
        extra = (
            {"Docker-Content-Digest": "sha256:" + "f" * 64}
            if mode == "wrong-hash"
            else {"Content-Type": "text/html"}
        )
        return response([descriptor(2)], **extra)

    with pytest.raises(OciError) as error:
        list_referrers(REF, transport=httpx.MockTransport(handle))
    assert calls == 2 and error.value.code == code


def test_standard_fallback_cannot_supply_api_page_links() -> None:
    calls = 0

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(404)
        assert calls == 2 and "/manifests/sha256-" in request.url.path
        return response([], f'<{URL}?last=p2>; rel="next"')

    with pytest.raises(OciError) as error:
        list_referrers(REF, transport=httpx.MockTransport(handle))
    assert calls == 2 and error.value.code == "INVALID_PAGE_LINK"
