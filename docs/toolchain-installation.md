# Toolchain installation guide

The scripts in `tools/toolchain-installers/` build or configure the optional local toolchain used by an authorized `rekit` runtime. They read paths from the runtime's `env.ps1` and write only inside that runtime's source, `toolchain`, `venv`, and build output directories. They do not install into the repository or change the system tool directories.

## Prerequisites

Run these commands from a checkout that is next to the separate runtime root. The scripts expect the runtime layout documented by [the troubleshooting guide](troubleshooting.md), including `env.ps1`, `toolchain/`, and the relevant source trees.

- Use a supported Python 3.10–3.12 runtime and the MSVC environment required by the selected build.
- Prepare Cargo, Gradle, Meson/Ninja, uv, and their local caches before an offline build.
- Read [the security boundaries](security-boundaries.md) before using real samples or enabling online downloads.

## Commands

```powershell
pwsh -File .\tools\toolchain-installers\10-build-binwalk.ps1
pwsh -File .\tools\toolchain-installers\11-build-jadx.ps1
pwsh -File .\tools\toolchain-installers\12-rizin-setup.ps1
pwsh -File .\tools\toolchain-installers\13-rizin-build.ps1
pwsh -File .\tools\toolchain-installers\21-frida-setup.ps1 -Online
```

The first four scripts are offline-first. The Frida script is offline by default and accepts `-Online` only when downloading locked Python packages or Android `frida-server` archives is explicitly authorized. Use `-Force` only when the Frida virtual environment may be recreated safely.

## What each script verifies

- `10-build-binwalk.ps1` runs Cargo with `--release --locked --offline -j 6`, then invokes the built `binwalk.exe --help`.
- `11-build-jadx.ps1` runs the checked-in Gradle wrapper for CLI and GUI distributions with `--offline --no-daemon`.
- `12-rizin-setup.ps1` configures a portable release build with Meson. Existing metadata is reconfigured; a failed reconfigure falls back to `--wipe`. Success prints `MESON-SETUP-OK`.
- `13-rizin-build.ps1` builds and installs with Ninja, then runs the installed `rizin.exe -v`.
- `21-frida-setup.ps1` creates `venv/frida`, installs `requirements/frida.txt`, runs `uv pip check`, extracts the two Android server archives, and imports `frida`, `objection`, and `frida_tools`. Success prints `Frida environment ready.`

Each script preserves the child process exit code by throwing on a failed build, install, download, extraction, or verification step. Keep command output and generated reports local; do not commit binaries, archives, virtual environments, credentials, or device data.

## Offline recovery

If an offline command reports a missing package or cache entry, prepare that dependency in an isolated, authorized environment and retry. Do not work around the failure by committing caches or switching to online mode silently. For a moved rizin build directory, rerun the setup script so its Meson metadata can be regenerated, then run the build script again.
