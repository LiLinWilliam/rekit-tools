---
layout: default
title: launcher | rekit-tools
permalink: /tools/launcher/
---

# `launcher`

Build Windows native launchers and extract .xz archives.

[Back to documentation home](../index.md) ? [Full tool README](https://github.com/LiLinWilliam/rekit-tools/blob/main/tools/launcher/README.md) ? [Edit on GitHub](https://github.com/LiLinWilliam/rekit-tools/edit/main/tools/launcher/README.md)

## First command

Run this from the real rekit root when the command needs private runtimes or generated evidence:

```powershell
python tools/launcher/extract_xz.py <dir>
```

The command keeps the tool's documented exit code and evidence boundaries. Read the full README before using it with real samples, devices, sessions, or a moved runtime.

## Related guides

- [Security boundaries](../security-boundaries.md)
- [Exit-code contract](../exit-code-contract.md)
- [Troubleshooting](../troubleshooting.md)
