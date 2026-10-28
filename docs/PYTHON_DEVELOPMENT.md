# Python development — TF-004

M0 foundation only: package, CLI and read-only development diagnostics. No OCI transport, cryptographic verifier, policy engine or runtime operations are implemented here. The workspace/bootstrap remain exclusively in distrobox-stack.

## Requirements and installation
Python >=3.13, Git and uv 0.13.5 are the development baseline. .python-version selects 3.13; local validation may explicitly select another supported interpreter. Do not install packages into Fedora's system Python.

From a reviewed checkout, with Python 3.13 and uv already available:
```bash
uv lock --check
uv sync --locked
uv run --no-sync trustforge --help
uv run --no-sync trustforge version
uv run --no-sync trustforge doctor
uv run --no-sync trustforge doctor --json
```
Sync creates only the project .venv and uv's cache; it may access PyPI and build the local Python package. It does not create a Distrobox or pull/build OCI images. For a private cache, set UV_CACHE_DIR to a writable directory reserved for this checkout. Disable interpreter downloads with UV_PYTHON_DOWNLOADS=never when using an existing interpreter.

HTTPX is deferred until M1 introduces HTTP transport. Pydantic validates the doctor report now; Typer parses the CLI and Rich renders its human table. uv.lock pins application and dev dependencies, including the build backend. Dependency updates are reviewed pyproject/lock changes, not implicit upgrades.

## CLI contract
- --help: exit 0; no arguments: help and exit 2.
- version: installed package metadata version, exit 0. 0.0.1.dev0 is a foundation version, not the planned M3 v0.1.0 release.
- doctor: observes Python version and Git/uv presence on PATH only. It does not execute detected binaries, inspect Podman/Distrobox, connect to registries, read credentials, install or repair anything.
- doctor --json: one JSON object with schema_version=1, checks and ready; no host paths. Exit 0 when every prerequisite is present, 1 otherwise.
- Unknown commands/options/extra arguments: exit 2. OCI commands intentionally do not exist yet.

A PASS from doctor is not a host audit, runtime test or security approval. It does not verify the authenticity/version of detected tools.

## Quality and packaging
```bash
uv run --no-sync pytest
uv run --no-sync ruff check .
uv run --no-sync ruff format --check .
uv run --no-sync mypy
uv build --python .venv/bin/python --no-build-isolation
```
The final command builds only a Python wheel/sdist, using the locked backend installed by sync; it does not publish. The isolated default build mode may resolve build dependencies separately. Test a rebuilt wheel in a fresh venv before release. The companion TF-005 draft automates checks and installation of a wheel rebuilt from the sdist.

src/trustforge/cli.py handles presentation and exit codes; doctor.py collects typed observations; __init__.py reads installed metadata; __main__.py supports python -m trustforge; py.typed marks the typed package.

Tests cover normal/invalid CLI input, Python/tool prerequisites, JSON and human output, return codes, blocked subprocess/network calls, credential sentinel access and unchanged working files. These are application tests, not Cosign, OCI or container interoperability tests.

## Review order
Review the independent TF-001 Apache license draft first. TF-004 can be reviewed independently of governance documentation. TF-005 CI is based on the TF-004 branch because main has no package yet; merge TF-004, rebase/retarget TF-005 to main and require fresh green CI. No issue is closed automatically.
