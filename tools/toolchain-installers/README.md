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
