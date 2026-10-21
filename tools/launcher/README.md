# launcher

本目录包含 Windows 原生 launcher 的 C 源码、MSVC 构建脚本，以及用于解包 .xz 文件的 Python 辅助程序。

## 用法

### 构建 launcher

在已配置好 MSVC、Windows SDK 和 rekit 环境变量的机器上，从仓库根目录运行：

~~~powershell
pwsh -File .\tools\launcher\01-build-launchers.ps1
~~~

脚本编译 launcher.c 为 bin/rekit.exe，再复制为 bin/ 下的各工具入口。编译失败会以非零退出码结束。

## 解包 .xz

extract_xz.py 只处理目标目录的直接子文件：

~~~powershell
python .\tools\launcher\extract_xz.py .\tooling\frida
~~~

对每个 *.xz，脚本解出同名无扩展名文件；目标文件已存在且非空时打印 keep <name> 并跳过。成功写入时打印 wrote <name> <字节数>。命令不递归目录，也不会删除压缩包。
## Example output

The extraction helper exposes the repository version without touching an archive:

```text
$ python tools/launcher/extract_xz.py --version
launcher/extract_xz 1.0.2
exit=0
```
## Exit codes

`0` means extraction or the launcher build completed. Archive, output, compiler, or PowerShell errors return a non-zero status. See the [repository exit-code contract](../../docs/exit-code-contract.md) for the automation rules.

## Security notes

Build only from authorized source trees and keep generated `bin/` files out of commits. `extract_xz.py` writes into the directory supplied on the command line. See [security boundaries](../../docs/security-boundaries.md) before running against a real runtime.
