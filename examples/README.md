# Examples

The examples below use placeholders for a real `rekit` runtime. They never authorize access to samples, devices, private session databases, or credentials. Run the safe smoke script after installing the package and the renderer dependency:

```powershell
python -m pip install --disable-pip-version-check --no-deps -e .
python -m pip install --disable-pip-version-check -r tools/render-entropy/requirements/render.txt
python examples/safe_smoke.py
```

The smoke script creates temporary synthetic data, then verifies these real outputs:

- `rekit-tools 1.0.1` followed by the twelve tool names from `rekit_tools.cli`.
- A `2048x1024` PNG from `render_entropy.py` with the standard PNG signature.
- `wrote synthetic.bin <bytes>` from `extract_xz.py`, followed by a byte-for-byte check.

## Commands for an authorized runtime

Run the following from a valid `rekit` root. `<rekit-root>` is a placeholder and must not be committed as a local path. A successful command exits with `0`; the expected evidence is listed so a caller can verify the behavior without copying logs into this repository.

| Tool | Minimal command | Expected evidence |
| --- | --- | --- |
| doctor | `python tools/doctor/doctor.py --json --no-write` | JSON with top-level `ok`; text mode reports `PASS: ... checks` |
| environment-snapshot | `python tools/environment-snapshot/02-snapshot-environments.py` | `requirements/<name>.txt`, `requirements/manifest.json`, and `<name>: <count> pinned entries` |
| launcher | `python tools/launcher/extract_xz.py <rekit-root>/tooling/frida` | `wrote <name> <bytes>` or `keep <name>` for an existing non-empty output |
| migrate-after-move | `pwsh -File tools/migrate-after-move/00-after-move.ps1 --venv render --check-only` | Repair output followed by the doctor result; non-zero exit on either failure |
| render-entropy | `Get-Content examples/entropy.json | python tools/render-entropy/render_entropy.py entropy.png` | `entropy.png` with a PNG signature; exit `0` |
| restore | `python tools/restore/restore.py --venv render --check-only` | `Restore verified. Log: ...`; exit `0` |
| retry-watchdog | `python tools/retry-watchdog/watchdog.py --thread <thread-uuid> --once --dry-run` | One read-only verdict; no queue message is sent in dry-run mode |
| toolchain-installers | `pwsh -File tools/toolchain-installers/12-rizin-setup.ps1` | `MESON-SETUP-OK`; the build script later prints `rizin -v` |
| venv-install-all | `pwsh -File tools/venv-install-all/12-venv-install-all.ps1 --venv render --check-only` | Repair output and the propagated exit code; no environment is replaced in check-only mode |
| verify | `python tools/verify/verify.py` | Per-check `OK`/`FAIL` lines and final `PASS` when all checks succeed |
| verify-portability | `python tools/verify-portability/verify-portability.py` | Temporary portable-path checks and final `PASS`; summary is written under local `logs/` |
| verify-review-fixes | `python tools/verify-review-fixes/verify-review-fixes.py` | Final `PASS`; temporary review fixtures are removed on completion |

Before running a row that touches a runtime, read [the security boundary guide](../docs/security-boundaries.md) and the tool's README. Keep generated logs, manifests, virtual environments, archives, and samples outside commits.
