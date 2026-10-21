---
layout: default
title: rekit-tools documentation
description: Auditable Windows tooling for portable local runtimes.
---

# rekit-tools documentation

Auditable Windows tooling for portable local runtimes. This page is the source index for the [published Pages site](https://lilinwilliam.github.io/rekit-tools/) and groups operator, tool, and contributor documentation.

The tools are intentionally small: each keeps its command-specific details beside its source code, emits inspectable evidence, and avoids changing unrelated system state.

## Start in 60 seconds

1. Read [security boundaries](security-boundaries.md) before using real samples, devices, or Codex sessions.
2. Try the repository-only [safe smoke example](../examples/README.md).
3. For a real rekit root, run `doctor --json --no-write`, then follow the [tool cards](#tool-cards).

## Tool cards

| Area | Tools | First question |
| --- | --- | --- |
| Audit and evidence | [doctor](../tools/doctor/README.md), [verify](../tools/verify/README.md), [verify-portability](../tools/verify-portability/README.md), [verify-review-fixes](../tools/verify-review-fixes/README.md) | Is the runtime healthy and unchanged? |
| State and recovery | [environment-snapshot](../tools/environment-snapshot/README.md), [restore](../tools/restore/README.md), [migrate-after-move](../tools/migrate-after-move/README.md), [venv-install-all](../tools/venv-install-all/README.md) | What was installed, and can it be restored offline? |
| Rendering and launchers | [render-entropy](../tools/render-entropy/README.md), [launcher](../tools/launcher/README.md) | Can a native boundary produce a deterministic artifact? |
| Toolchains and sessions | [toolchain-installers](../tools/toolchain-installers/README.md), [retry-watchdog](../tools/retry-watchdog/README.md) | Which external state is authorized and observable? |

## Operator guides

- [Common troubleshooting](troubleshooting.md)
- [Toolchain installation](toolchain-installation.md)
- [Security boundaries and authorized use](security-boundaries.md)
- [Exit-code contract](exit-code-contract.md)
- [Examples and smoke tests](../examples/README.md)

## Contributor entry points

- [Project overview](../README.md) ? [Chinese overview](../README.zh-CN.md)
- [Changelog](../CHANGELOG.md)
- [Contributing](../CONTRIBUTING.md)
- [Security policy](../SECURITY.md)
- [Code of Conduct](../CODE_OF_CONDUCT.md)

## Tool reference

| Tool | Reference |
| --- | --- |
| doctor | [tools/doctor](../tools/doctor/README.md) |
| environment-snapshot | [tools/environment-snapshot](../tools/environment-snapshot/README.md) |
| launcher | [tools/launcher](../tools/launcher/README.md) |
| migrate-after-move | [tools/migrate-after-move](../tools/migrate-after-move/README.md) |
| render-entropy | [tools/render-entropy](../tools/render-entropy/README.md) |
| restore | [tools/restore](../tools/restore/README.md) |
| retry-watchdog | [tools/retry-watchdog](../tools/retry-watchdog/README.md) |
| toolchain-installers | [tools/toolchain-installers](../tools/toolchain-installers/README.md) |
| venv-install-all | [tools/venv-install-all](../tools/venv-install-all/README.md) |
| verify | [tools/verify](../tools/verify/README.md) |
| verify-portability | [tools/verify-portability](../tools/verify-portability/README.md) |
| verify-review-fixes | [tools/verify-review-fixes](../tools/verify-review-fixes/README.md) |

## CI and release

- [Continuous integration](../.github/workflows/ci.yml)
- [Markdown link checks](../.github/workflows/markdown-links.yml)
- [Documentation Pages workflow](../.github/workflows/pages.yml)
- [Tag-based release workflow](../.github/workflows/release.yml)
- [Dependabot configuration](../.github/dependabot.yml)
