"""Read-only development checks; never execute a detected tool."""

import shutil
import sys
from typing import Literal

from pydantic import BaseModel, ConfigDict


class RequirementCheck(BaseModel):
    """A non-sensitive observation, without host paths or credentials."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    name: Literal["python", "git", "uv"]
    available: bool
    requirement: str


class DoctorReport(BaseModel):
    """Structured observations, not runtime or security certification."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    schema_version: Literal[1] = 1
    checks: tuple[RequirementCheck, ...]

    def is_ready(self) -> bool:
        return all(check.available for check in self.checks)


def collect_checks() -> DoctorReport:
    """Inspect Python and PATH only; no subprocesses, network or writes."""
    return DoctorReport(
        checks=(
            RequirementCheck(
                name="python",
                available=sys.version_info[:2] >= (3, 13),
                requirement="Python >=3.13",
            ),
            RequirementCheck(
                name="git", available=shutil.which("git") is not None, requirement="Git"
            ),
            RequirementCheck(name="uv", available=shutil.which("uv") is not None, requirement="uv"),
        )
    )
