---
layout: default
title: venv-install-all | rekit-tools
permalink: /tools/venv-install-all/
---

# `venv-install-all`

Restore all virtual environments through repair.exe.

[Back to documentation home](../index.md) ? [Full tool README](https://github.com/LiLinWilliam/rekit-tools/blob/main/tools/venv-install-all/README.md) ? [Edit on GitHub](https://github.com/LiLinWilliam/rekit-tools/edit/main/tools/venv-install-all/README.md)

## First command

Run this from the real rekit root when the command needs private runtimes or generated evidence:

```powershell
pwsh -File tools/venv-install-all/12-venv-install-all.ps1 --check-only
```

The command keeps the tool's documented exit code and evidence boundaries. Read the full README before using it with real samples, devices, sessions, or a moved runtime.

## Related guides

- [Security boundaries](../security-boundaries.md)
- [Exit-code contract](../exit-code-contract.md)
- [Troubleshooting](../troubleshooting.md)
