# Contributing to rekit-tools

Thank you for improving rekit-tools. Changes should stay auditable, reproducible, and scoped to this repository's twelve Windows helper tools.

## Before you start

- Use Python 3.10, 3.11, or 3.12. PowerShell 7 or Windows PowerShell is required for `.ps1` checks.
- Keep the repository self-contained. Do not edit the separate `E:/Desktop/rekit` source tree.
- Read [SECURITY.md](SECURITY.md) and [the security boundary guide](docs/security-boundaries.md) before running a tool against a real runtime, sample, device, or session.

Install the package in editable mode and run the test suite:

```powershell
python -m pip install --disable-pip-version-check --no-deps -e .
python -m pytest -q tests --cov=tools --cov-report=term-missing --cov-fail-under=39
```

The editable install provides the `rekit-tools` command. `rekit-tools --version` and `rekit-tools list` are safe local smoke tests.

Install the optional pre-commit runner once, then enable the repository hooks:

```powershell
python -m pip install --disable-pip-version-check pre-commit
pre-commit install
pre-commit run --all-files
```

The hooks apply the repository Ruff configuration and basic YAML, whitespace, and merge-conflict checks. The CI matrix remains the final check for Windows-specific behavior.

## Branches and commits

Start from an up-to-date `main` branch and use a focused branch name:

```powershell
git switch main
git pull --ff-only origin main
git switch -c feat/<short-topic>
```

Use `docs/<topic>` for documentation, `ci/<topic>` for automation, and `test/<topic>` for tests. Keep each branch to one reviewable theme. Commit messages use the Conventional Commits form, for example `docs: clarify restore usage` or `test: cover snapshot parsing`.

## Validation before opening a PR

Run the checks that match your change:

```powershell
python -m ruff check tools tests src
python -m pytest -q tests --cov=tools --cov-report=term-missing --cov-fail-under=39
git diff --check
```

For documentation changes, also check relative Markdown links locally. Do not add generated virtual environments, toolchains, samples, logs, caches, private session databases, credentials, API keys, tokens, or UUIDs. Use placeholders such as `<rekit-root>` in examples.

If a change touches PowerShell, parse the scripts with the same command used by CI. If it touches a tool that needs an authorized runtime, document the exact prerequisite and preserve the command's exit code and evidence output.

## Pull requests

Describe the user-visible behavior, the files changed, and the commands you ran. Keep screenshots and fixtures small and synthetic. Wait for the Windows/Python matrix and Markdown-link checks to pass before merging. Merge with squash and delete the topic branch; never force-push `main`.

Review comments should be resolved with a follow-up commit or an explicit explanation. Security-sensitive reports belong in the private reporting channel described in [SECURITY.md](SECURITY.md), not in a public issue.
