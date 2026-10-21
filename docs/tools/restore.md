---
layout: default
title: restore | rekit-tools
permalink: /tools/restore/
---

# `restore`

Restore virtual environments from locked requirements.

[Back to documentation home](../index.md) ? [Full tool README](https://github.com/LiLinWilliam/rekit-tools/blob/main/tools/restore/README.md) ? [Edit on GitHub](https://github.com/LiLinWilliam/rekit-tools/edit/main/tools/restore/README.md)

## First command

Run this from the real rekit root when the command needs private runtimes or generated evidence:

```powershell
python tools/restore/restore.py --venv render --check-only
```

The command keeps the tool's documented exit code and evidence boundaries. Read the full README before using it with real samples, devices, sessions, or a moved runtime.

## Related guides

- [Security boundaries](../security-boundaries.md)
- [Exit-code contract](../exit-code-contract.md)
- [Troubleshooting](../troubleshooting.md)
