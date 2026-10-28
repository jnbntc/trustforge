# Python CI — TF-005

The .github/workflows/python.yml change is rebased onto main after Apache-2.0 license PR #32 (7cde9a63ee7fe9b90d79545f6dd2b79613832969) and TF-004 package PR #33 (af83598dceef0ee7660f73eb199071bf9fa3196f) were integrated by squash. PR #34 targets main and changes only this workflow and this document. Require a fresh green run on the rebased head before integration.

Stable required-check candidate: **Python 3.13 checks**. Every pull request runs it, including documentation PRs; pushes to main also run it. There is no path filter that could leave the required result pending. All pytest/lint/format/type/lock/distribution checks share this job, so success means all steps passed. Register this exact name only after seeing a real successful GitHub Actions run.

The job uses Ubuntu 24.04, setup-python 3.13 and uv 0.13.5. Actions are pinned to verified official tag commits:
- actions/checkout 7.0.1: 3d3c42e5aac5ba805825da76410c181273ba90b1
- actions/setup-python 7.1.0: 6d4fd22b20465ccc0f7354476588e8df7c9ca0e0
- astral-sh/setup-uv 10.3.2: 07a047e608db84b3d8c06cd9a7c7dcc9c355c18e

Permissions are contents:read at workflow/job level; checkout credentials are not persisted. No pull_request_target, secrets/custom token, OIDC/packages write, environment, reusable privileged workflow or publication exists. uv cache lives in runner.temp; shared cache persistence is disabled. Package installation executes reviewed build code in the disposable CI runner, not on the Fedora host.

Steps: lock consistency; locked sync; pytest; Ruff check; Ruff format --check; strict mypy; wheel/sdist build using the locked hatchling in .venv; wheel rebuilt from sdist; fresh venv installation of hash-locked runtime dependencies plus the local wheel; dependency consistency and installed console/module entry points, including invalid-command exit 2.
Build and smoke tests only create Python distributions/environments on the runner. They do not publish to PyPI/GHCR, sign artifacts, build OCI images or touch containers.

After retargeting a stacked PR, verify the checkout commit in the Actions log: a run queued before the base change can still test the previous merge ref even when the API already reports the new base. A new push after retargeting provides a fresh run against main; confirm its head and base before merging.

Local commands and limits are in the TF-004 Python development guide. CI status is live evidence; do not infer a Python 3.13 pass from local Python 3.14 results. No issue closes on merge. Branch/environment settings are owner actions described by the independent governance draft; CI does not configure them.
