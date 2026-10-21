# toolchain-installers

这些 PowerShell 脚本分别构建或配置 binwalk、jadx、rizin 和 Frida。它们操作 rekit 自己的源码、缓存、toolchain 与 venv，不会把构建产物写入仓库外的系统工具目录。

## 用法

~~~powershell
pwsh -File .\tools\toolchain-installers\10-build-binwalk.ps1
pwsh -File .\tools\toolchain-installers\11-build-jadx.ps1
pwsh -File .\tools\toolchain-installers\12-rizin-setup.ps1
pwsh -File .\tools\toolchain-installers\13-rizin-build.ps1
pwsh -File .\tools\toolchain-installers\21-frida-setup.ps1 -Online
~~~

10 使用 Cargo release/offline 构建 binwalk；11 使用 Gradle offline 构建 jadx；12 配置 rizin 的 Meson build；13 用 Ninja 编译并安装 rizin；21 创建 venv/frida、安装锁定依赖，并按参数决定是否下载 Android frida-server。

## 输入与输出

脚本从 rekit 根目录的 env.ps1、本地源码和缓存读取输入。首次准备依赖可能需要网络；默认脚本尽量离线，Frida 只有 -Online 才允许下载。成功时会打印各自的构建版本或 Frida environment ready.；失败时返回非零退出码。
## Example output

The installer scripts were syntax-parsed with PowerShell without starting a build or downloading a toolchain:

```text
$ pwsh -NoProfile -Command "ParseFile('tools/toolchain-installers/*.ps1')"
10-build-binwalk.ps1: Parse status: OK
11-build-jadx.ps1: Parse status: OK
12-rizin-setup.ps1: Parse status: OK
13-rizin-build.ps1: Parse status: OK
21-frida-setup.ps1: Parse status: OK
exit=0
```

A successful build prints its own version or readiness marker; missing sources, caches, or toolchain dependencies terminate with a non-zero PowerShell error.
## Exit codes

`0` means the selected installer completed. Missing sources, build tools, downloads, or import checks raise a PowerShell error and produce a non-zero status. See the [repository exit-code contract](../../docs/exit-code-contract.md) for the automation rules.

## Security notes

Install into the rekit-owned toolchain and cache directories. `-Online` is an explicit network action; review the source and keep generated binaries and private logs out of the repository. See [security boundaries](../../docs/security-boundaries.md) before running against a real runtime.
