# verify

**verify.py** 是面向真实 rekit 运行时的功能验收脚本。它在隔离的 PATH 环境中检查原生参数传递、stdin、退出码、rizin JSON、diec APK 识别、capa/floss JSON、jadx、Ghidra 导入，以及可用时的 binwalk PNG。

## 用法

~~~powershell
$env:REKIT_SAMPLE_APK = '<authorized-sample-apk>'
python .\tools\verify\verify.py
~~~

REKIT_SAMPLE_APK 必须指向已获授权的 APK；不设置时脚本会使用占位路径，相关检查会失败。脚本不接受额外参数。

## 输入与输出

脚本会在 logs/ 写入每项检查的 stdout/stderr 和 verification.json，终端逐项打印 OK 或 FAIL，最后打印 PASS/FAIL。所有检查通过返回 0，任一检查失败返回 1。它会记录受保护目录前后指纹，验证期间不会主动修改这些目录。
## Example output

```text
$ python tools/verify/verify.py --version
verify 1.0.2
exit=0
```
## Exit codes

`0` means every acceptance check passed; `1` means at least one check failed. `--version` returns `0`. See the [repository exit-code contract](../../docs/exit-code-contract.md) for the automation rules.

## Security notes

`REKIT_SAMPLE_APK` must reference an authorized sample. Logs include command output and path fingerprints; redact them and keep them outside public commits. See [security boundaries](../../docs/security-boundaries.md) before running against a real runtime.
