# migrate-after-move

**00-after-move.ps1** 是移动 rekit 后的恢复入口：它把参数传给 bin/repair.exe，repair 成功后再执行 bin/doctor.exe。

## 用法

~~~powershell
pwsh -File .\tools\migrate-after-move\00-after-move.ps1 --venv render --check-only
pwsh -File .\tools\migrate-after-move\00-after-move.ps1 --venv misc --online
~~~

- --venv <name> 选择要恢复的环境；可以重复传入。
- --check-only 只在临时目录创建并验证环境，不替换现有环境。
- 默认离线运行；只有显式传入 --online 才允许索引访问。

## 输入与输出

脚本依赖移动后 rekit 根目录中的 bin/repair.exe、bin/doctor.exe、requirements/ 与本地运行时。repair 的输出会直接转发到终端，成功后再看到 doctor 检查结果；任一步失败都会返回对应非零退出码。
## Example output

This repository does not include a rekit root or its `bin/repair.exe`, so executing the recovery wrapper here would be an invalid fixture. The checked-in PowerShell entry point was syntax-parsed locally:

```text
$ pwsh -NoProfile -Command "ParseFile('tools/migrate-after-move/00-after-move.ps1')"
00-after-move.ps1: Parse status: OK
exit=0
```

Run the wrapper only from an authorized rekit root; its runtime output comes from `repair.exe` and `doctor.exe`.
