# verify-portability

**verify-portability.py** 把验证所需的 runtime、脚本、依赖和构建产物复制到 temp/portable path-*，在含空格的路径中执行离线恢复、Python 导入、便携 rizin 和裸 binwalk PNG 检查，最后删除临时目录。

## 用法

~~~powershell
python .\tools\verify-portability\verify-portability.py
~~~

脚本不接受参数，必须在具有完整 rekit runtime、缓存与构建产物的根目录中运行。它会清理临时复制目录，但把摘要写入 logs/portability.json，各步骤 stdout/stderr 写入 logs/portability-*.txt。

## 输入与输出

成功时终端会显示 PASS 并返回 0；缺少任一待复制路径、离线包或工具时会在对应步骤打印 FAIL，摘要的 ok 为 false，返回 1。该脚本验证的是迁移边界，不代表每个工具或完整 rekit 克隆都已验证。
## Example output

```text
$ python tools/verify-portability/verify-portability.py --version
verify-portability 1.0.2
exit=0
```
## Exit codes

`0` means all portability checks passed; `1` means a required path, package, or tool check failed. `--version` returns `0`. See the [repository exit-code contract](../../docs/exit-code-contract.md) for the automation rules.

## Security notes

Run from an authorized complete runtime. The tool copies files into temporary portable paths and writes logs; inspect the boundary and remove sensitive evidence after review. See [security boundaries](../../docs/security-boundaries.md) before running against a real runtime.
