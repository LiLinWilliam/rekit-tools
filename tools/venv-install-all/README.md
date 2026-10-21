# venv-install-all

**12-venv-install-all.ps1** 是批量恢复入口，直接把参数转发给 bin/repair.exe。

## 用法

~~~powershell
pwsh -File .\tools\venv-install-all\12-venv-install-all.ps1 --check-only
pwsh -File .\tools\venv-install-all\12-venv-install-all.ps1 --venv render --check-only
pwsh -File .\tools\venv-install-all\12-venv-install-all.ps1 --venv render --online
~~~

支持 repair.exe 的 --venv、--check-only、--online 参数。默认不联网，显式 --online 才允许索引访问。

## 输入与输出

脚本需要 rekit 根目录的 bin/repair.exe 和 requirements 快照。repair 的标准输出和退出码直接返回给调用方；成功后可继续运行 doctor 验证导入与依赖。
## Example output

The wrapper was syntax-parsed locally; running it requires the `repair.exe` from an authorized rekit root:

```text
$ pwsh -NoProfile -Command "ParseFile('tools/venv-install-all/12-venv-install-all.ps1')"
12-venv-install-all.ps1: Parse status: OK
exit=0
```
## Exit codes

The wrapper forwards the status from `repair.exe`; successful repair returns `0`, and a repair failure is non-zero. See the [repository exit-code contract](../../docs/exit-code-contract.md) for the automation rules.

## Security notes

Run `--check-only` before changing environments and keep the default offline behavior. Use only an authorized rekit root; never point the wrapper at a system or third-party environment. See [security boundaries](../../docs/security-boundaries.md) before running against a real runtime.
