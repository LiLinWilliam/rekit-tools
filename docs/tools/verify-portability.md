---
layout: default
title: verify-portability | rekit-tools
permalink: /tools/verify-portability/
---

# `verify-portability`

Verify offline restoration and paths containing spaces.

[Back to documentation home](../index.md) ? [Full tool README](https://github.com/LiLinWilliam/rekit-tools/blob/main/tools/verify-portability/README.md) ? [Edit on GitHub](https://github.com/LiLinWilliam/rekit-tools/edit/main/tools/verify-portability/README.md)

## First command

Run this from the real rekit root when the command needs private runtimes or generated evidence:

```powershell
python tools/verify-portability/verify-portability.py
```

The command keeps the tool's documented exit code and evidence boundaries. Read the full README before using it with real samples, devices, sessions, or a moved runtime.

## Related guides

- [Security boundaries](../security-boundaries.md)
- [Exit-code contract](../exit-code-contract.md)
- [Troubleshooting](../troubleshooting.md)
