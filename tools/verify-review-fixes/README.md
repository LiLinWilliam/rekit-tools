# verify-review-fixes

**verify-review-fixes.py** 回归三类边界：renderer 不依赖 qiling、原生 launcher 可直接调用、Ghidra headless 使用预期最大堆，并检查 bin 工具目录中的原生入口清单。

## 用法

~~~powershell
python .\tools\verify-review-fixes\verify-review-fixes.py
~~~

脚本不接受参数，会在 temp/review-check-* 建立短期工作目录；需要完整的 binwalk、rekit launcher、Ghidra 和 JDK。Frida、真实设备和私有会话不属于该验收范围。

## 输入与输出

成功时打印 PASS 并返回 0；步骤失败时打印 FAIL，返回 1。详细 stdout/stderr 写入 logs/review-*.stdout.txt 与 logs/review-*.stderr.txt，汇总写入 logs/review-verification.json。临时目录在结束时删除。
## Example output

```text
$ python tools/verify-review-fixes/verify-review-fixes.py --version
verify-review-fixes 1.0.2
exit=0
```
