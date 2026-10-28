"""CLI uses the real HTTP adapter with MockTransport; internet is not required."""

import json
from pathlib import Path

import httpx
import pytest
from typer.testing import CliRunner

from trustforge.cli import app
from trustforge.oci.client import inspect_reference
from trustforge.oci.digest import digest_bytes
from trustforge.oci.errors import OciError
from trustforge.oci.models import OCI_INDEX

runner = CliRunner()
RAW = (Path(__file__).parent / "fixtures" / "oci" / "index.json").read_bytes()
REFERENCE = "registry.example/team/image:tag"


def install_mock(
    monkeypatch: pytest.MonkeyPatch,
    transport: httpx.MockTransport,
) -> None:
    def inspect(value: str) -> object:
        return inspect_reference(value, transport=transport)

    monkeypatch.setattr("trustforge.oci_cli.inspect_reference", inspect)


@pytest.mark.parametrize("machine", [False, True])
def test_inspect_cli_json_and_human(monkeypatch: pytest.MonkeyPatch, machine: bool) -> None:
    calls = 0

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        assert request.method == "GET"
        assert request.url.path == "/v2/team/image/manifests/tag"
        return httpx.Response(
            200,
            content=RAW,
            headers={
                "Content-Type": OCI_INDEX,
                "Docker-Content-Digest": digest_bytes(RAW),
            },
        )

    install_mock(monkeypatch, httpx.MockTransport(handle))
    result = runner.invoke(app, ["oci", "inspect", REFERENCE] + (["--json"] if machine else []))
    assert result.exit_code == 0, result.output
    assert calls == 1
    if machine:
        parsed = json.loads(result.stdout)
        assert result.stderr == ""
        assert parsed["schema_version"] == 1 and parsed["kind"] == "index"
        assert parsed["digest"] == digest_bytes(RAW)
        assert parsed["resolved_reference"] == "registry.example/team/image@" + digest_bytes(RAW)
        children = parsed["document"]["manifests"]
        assert {d["platform"]["architecture"] for d in children} == {"amd64", "arm64"}
        assert all(child["digest"] != parsed["digest"] for child in children)
        assert "verification" not in parsed and "token" not in parsed
    else:
        assert "Kind: index" in result.stdout and "Metadata bytes:" in result.stdout
        assert "linux/amd64" in result.stdout and "linux/arm64" in result.stdout
        assert "authenticity and deployment are not verified" in result.stdout


@pytest.mark.parametrize("machine", [False, True])
def test_invalid_reference_fails_before_http(
    monkeypatch: pytest.MonkeyPatch, machine: bool
) -> None:
    def fail(request: httpx.Request) -> httpx.Response:
        pytest.fail("invalid reference attempted network")

    install_mock(monkeypatch, httpx.MockTransport(fail))
    result = runner.invoke(
        app,
        ["oci", "inspect", "http://user:secret@evil.invalid/image"]
        + (["--json"] if machine else []),
    )
    assert result.exit_code == 2
    assert result.stdout == "" and "secret" not in result.output
    if machine:
        assert json.loads(result.stderr)["error"]["code"] == "INVALID_REFERENCE"
    else:
        assert "INVALID_REFERENCE" in result.stderr


@pytest.mark.parametrize(
    "code,exit_code",
    [
        ("TIMEOUT", 3),
        ("AUTH_REQUIRED", 4),
        ("DIGEST_MISMATCH", 5),
        ("RATE_LIMITED", 6),
    ],
)
def test_error_contract_and_return_codes(
    monkeypatch: pytest.MonkeyPatch,
    code: str,
    exit_code: int,
) -> None:
    def fail(value: str) -> object:
        raise OciError(code, "Sanitized failure.", exit_code)

    monkeypatch.setattr("trustforge.oci_cli.inspect_reference", fail)
    result = runner.invoke(app, ["oci", "inspect", REFERENCE, "--json"])
    assert result.exit_code == exit_code and result.stdout == ""
    assert json.loads(result.stderr) == {
        "schema_version": 1,
        "error": {"code": code, "message": "Sanitized failure."},
    }
    assert "Traceback" not in result.output


@pytest.mark.parametrize(
    "arguments",
    [
        ["oci"],
        ["oci", "inspect"],
        ["oci", "inspect", REFERENCE, "--insecure"],
        ["oci", "inspect", REFERENCE, "--credentials", "secret"],
        ["oci", "inspect", REFERENCE, "--platform", "linux/amd64"],
    ],
)
def test_unsupported_operations_and_arguments(arguments: list[str]) -> None:
    result = runner.invoke(app, arguments)
    assert result.exit_code == 2
    assert "Usage" in result.output


def test_token_is_not_in_auth_failure_output(monkeypatch: pytest.MonkeyPatch) -> None:
    token = "fixture-token.NO-LOG"
    calls = 0

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(
                401, headers={"WWW-Authenticate": 'Bearer realm="https://registry.example/token"'}
            )
        if calls == 2:
            return httpx.Response(200, json={"token": token})
        assert request.headers["authorization"] == "Bearer " + token
        return httpx.Response(500, content=token)

    install_mock(monkeypatch, httpx.MockTransport(handle))
    result = runner.invoke(app, ["oci", "inspect", REFERENCE, "--json"])
    assert result.exit_code == 6 and token not in result.output
    assert calls == 3
