---
layout: default
title: render-entropy | rekit-tools
permalink: /tools/render-entropy/
---

# `render-entropy`

Render JSON entropy blocks to a PNG artifact.

[Back to documentation home](../index.md) ? [Full tool README](https://github.com/LiLinWilliam/rekit-tools/blob/main/tools/render-entropy/README.md) ? [Edit on GitHub](https://github.com/LiLinWilliam/rekit-tools/edit/main/tools/render-entropy/README.md)

## First command

Run this from the real rekit root when the command needs private runtimes or generated evidence:

```powershell
Get-Content entropy.json | python tools/render-entropy/render_entropy.py entropy.png
```

The command keeps the tool's documented exit code and evidence boundaries. Read the full README before using it with real samples, devices, sessions, or a moved runtime.

## Related guides

- [Security boundaries](../security-boundaries.md)
- [Exit-code contract](../exit-code-contract.md)
- [Troubleshooting](../troubleshooting.md)
