"""CLI contracts and negative cases; no runtime, credentials or network."""

import json
import socket
import subprocess
from pathlib import Path
from typing import Any, Literal
from unittest.mock import Mock

import pytest
from typer.testing import CliRunner

from trustforge import __version__
from trustforge.cli import app
from trustforge.doctor import DoctorReport, RequirementCheck, collect_checks

runner = CliRunner()


def test_help_lists_foundation_and_oci_commands() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert all(command in result.output for command in ("version", "doctor"))
    assert "read-only OCI metadata inspection" in result.output
    assert "--install-completion" not in result.output


def test_version_matches_installed_metadata() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert result.output == f"TrustForge {__version__}\n"


@pytest.mark.parametrize(
    "arguments",
    [
        [],
        ["unknown"],
        ["inspect", "example.invalid/image"],
        ["--unknown"],
        ["version", "unexpected"],
        ["doctor", "--fix"],
        ["doctor", "--json", "unexpected"],
    ],
)
def test_invalid_arguments_fail(arguments: list[str]) -> None:
    result = runner.invoke(app, arguments)
    assert result.exit_code == 2
    assert "Usage" in result.output
    assert "Traceback" not in result.output


@pytest.mark.parametrize("available", [True, False])
def test_doctor_human_and_json(monkeypatch: pytest.MonkeyPatch, available: bool) -> None:
    names: tuple[Literal["python", "git", "uv"], ...] = ("python", "git", "uv")
    checks = tuple(
        RequirementCheck(name=name, available=available, requirement=name) for name in names
    )
    report = DoctorReport(checks=checks)
    monkeypatch.setattr("trustforge.cli.collect_checks", lambda: report)
    human = runner.invoke(app, ["doctor"])
    machine = runner.invoke(app, ["doctor", "--json"])
    assert human.exit_code == machine.exit_code == (0 if available else 1)
    assert ("PASS" if available else "MISSING") in human.output
    parsed = json.loads(machine.output)
    assert parsed["schema_version"] == 1
    assert parsed["ready"] is available
    assert [check["name"] for check in parsed["checks"]] == ["python", "git", "uv"]
    assert "Development prerequisites" not in machine.output


def test_doctor_missing_tools_and_unsupported_python(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("trustforge.doctor.sys.version_info", (3, 12, 0))
    monkeypatch.setattr("trustforge.doctor.shutil.which", lambda _name: None)
    report = collect_checks()
    assert not report.is_ready()
    assert all(not check.available for check in report.checks)


def test_doctor_supported_python_and_available_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("trustforge.doctor.sys.version_info", (3, 13, 0))
    monkeypatch.setattr("trustforge.doctor.shutil.which", lambda _name: "/fixture/tool")
    assert collect_checks().is_ready()


@pytest.mark.parametrize("missing", ["git", "uv"])
def test_doctor_one_missing_tool(monkeypatch: pytest.MonkeyPatch, missing: str) -> None:
    monkeypatch.setattr("trustforge.doctor.sys.version_info", (3, 13, 0))
    monkeypatch.setattr(
        "trustforge.doctor.shutil.which",
        lambda name: None if name == missing else "/fixture/tool",
    )
    result = runner.invoke(app, ["doctor", "--json"])
    assert result.exit_code == 1
    parsed = json.loads(result.output)
    assert [check["name"] for check in parsed["checks"] if not check["available"]] == [missing]


@pytest.mark.parametrize("arguments", [["--help"], ["version"], ["doctor"], ["doctor", "--json"]])
def test_cli_has_no_process_network_or_filesystem_side_effects(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, arguments: list[str]
) -> None:
    """Executable markers on PATH must be detected but never run."""
    home = tmp_path / "home"
    tools = tmp_path / "tools"
    home.mkdir()
    tools.mkdir()
    for name in ("git", "uv"):
        tool = tools / name
        tool.write_text("#!/bin/sh\nexit 99\n")
        tool.chmod(0o755)
    secret = home / ".credentials"
    secret.write_text("fixture sentinel, never read by the application")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("PATH", str(tools))
    monkeypatch.chdir(tmp_path)
    forbidden = Mock(side_effect=AssertionError("external operation attempted"))
    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    before = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    original_open = Path.open

    def guarded_open(path: Path, *args: Any, **kwargs: Any) -> Any:
        assert path != secret, "credential access attempted"
        return original_open(path, *args, **kwargs)

    with monkeypatch.context() as guard:
        guard.setattr(Path, "open", guarded_open)
        result = runner.invoke(app, arguments)
    after = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert result.exit_code == 0, result.output
    assert before == after
    forbidden.assert_not_called()


def test_doctor_report_rejects_unexpected_fields() -> None:
    invalid: dict[str, Any] = {"checks": (), "credentials": "not accepted"}
    with pytest.raises(ValueError):
        DoctorReport.model_validate(invalid)
