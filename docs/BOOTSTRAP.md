# Initial GitHub bootstrap

This repository is not created by generating this archive. `scripts/bootstrap_github.sh` is intended for an authenticated `gh` CLI with repository creation privileges. It creates the **public** `jnbntc/trustforge` repository, commits this baseline on `main`, and creates M0–M5 milestones and 28 issues.

1. Extract archive and `cd trustforge_bootstrap`.
2. Install GitHub CLI (`gh`) and ensure `gh auth status` succeeds for `jnbntc`.
3. Inspect `scripts/bootstrap_github.sh` and issue catalogue; it performs public GitHub writes.
4. Run `bash scripts/bootstrap_github.sh`.
5. Verify the repository, issues, and milestone assignments on GitHub. Enable branch protection/rulesets and private vulnerability reporting manually if available.

The script checks that `jnbntc/trustforge` does **not** exist before creating it, to avoid overwriting an existing repository. Do not rerun it after a partial run; examine GitHub state and resume manually.
