---
layout: default
title: migrate-after-move | rekit-tools
permalink: /tools/migrate-after-move/
---

# `migrate-after-move`

Restore environments after moving rekit and run doctor.

[Back to documentation home](../index.md) ? [Full tool README](https://github.com/LiLinWilliam/rekit-tools/blob/main/tools/migrate-after-move/README.md) ? [Edit on GitHub](https://github.com/LiLinWilliam/rekit-tools/edit/main/tools/migrate-after-move/README.md)

## First command

Run this from the real rekit root when the command needs private runtimes or generated evidence:

```powershell
pwsh -File tools/migrate-after-move/00-after-move.ps1 --check-only
```

The command keeps the tool's documented exit code and evidence boundaries. Read the full README before using it with real samples, devices, sessions, or a moved runtime.

## Related guides

- [Security boundaries](../security-boundaries.md)
- [Exit-code contract](../exit-code-contract.md)
- [Troubleshooting](../troubleshooting.md)
