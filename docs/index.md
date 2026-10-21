# Documentation index

This index groups the repository's operator and contributor documentation. The tools are intentionally small and keep their command-specific details beside their source code.

## Start here

- [Project overview](../README.md) · [中文说明](../README.zh-CN.md)
- [Changelog](../CHANGELOG.md)
- [Contributing](../CONTRIBUTING.md)
- [Security policy](../SECURITY.md)
- [Security boundaries and authorized use](security-boundaries.md)

## Operator guides

- [Common troubleshooting](troubleshooting.md)
- [Toolchain installation](toolchain-installation.md)
- [Examples and smoke tests](../examples/README.md)

## Tool reference

- [Exit-code contract](exit-code-contract.md) — stable statuses for scripts and CI

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
- [Tag-based release workflow](../.github/workflows/release.yml)
- [Dependabot configuration](../.github/dependabot.yml)
