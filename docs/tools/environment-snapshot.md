---
layout: default
title: environment-snapshot | rekit-tools
permalink: /tools/environment-snapshot/
---

# `environment-snapshot`

Record locked package versions and editable-source commits.

[Back to documentation home](../index.md) ? [Full tool README](https://github.com/LiLinWilliam/rekit-tools/blob/main/tools/environment-snapshot/README.md) ? [Edit on GitHub](https://github.com/LiLinWilliam/rekit-tools/edit/main/tools/environment-snapshot/README.md)

## First command

Run this from the real rekit root when the command needs private runtimes or generated evidence:

```powershell
python tools/environment-snapshot/02-snapshot-environments.py
```

The command keeps the tool's documented exit code and evidence boundaries. Read the full README before using it with real samples, devices, sessions, or a moved runtime.

## Related guides

- [Security boundaries](../security-boundaries.md)
- [Exit-code contract](../exit-code-contract.md)
- [Troubleshooting](../troubleshooting.md)
