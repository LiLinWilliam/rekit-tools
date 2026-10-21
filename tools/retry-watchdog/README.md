# retry-watchdog

本目录提供针对 Codex 会话的只读状态观察和受控重试脚本。**watchdog.py** 只读打开 CODEX_HOME 下的 SQLite，判断目标 turn 是否仍在运行、已完成或停摆；只有判定停摆后才会调用 codex queue，可选地回退到 codex exec resume。

## 用法

### 先做只读演练

~~~powershell
python .\tools\retry-watchdog\watchdog.py --thread <thread-uuid> --once --dry-run
python .\tools\retry-watchdog\show_progress.py <thread-uuid> -n 20
~~~

--once --dry-run 只轮询一次并打印判断，不发送队列消息。show_progress.py 读取 state_5.sqlite 和 rollout 文件，列出最近事件，不修改会话。

## 持续运行

~~~powershell
pwsh -File .\tools\retry-watchdog\start.ps1 -Thread <thread-uuid> -Interval 15 -Stall 120
pwsh -File .\tools\retry-watchdog\stop.ps1
python .\tools\retry-watchdog\watchdog.py --thread <thread-uuid> --interval 15 --stall-seconds 120 --max-attempts 3
~~~

start.ps1 会在本目录的 logs/ 创建 PID、标准输出和错误日志；stop.ps1 按 PID 或锁文件停止进程并清理这些控制文件。watchdog.py --help 列出完整参数，包括 --codex-home、--codex-exe、--consume-timeout、--turn-timeout、--prompt、--model、--effort 和 --exec-fallback。

## 输入与输出

输入是已授权的 thread UUID、可读的 CODEX_HOME SQLite 数据库和本机 Codex CLI。每轮状态会写入指定日志目录并打印 verdict；正常完成返回 0，参数、锁或执行器错误返回非零。不要把 SQLite、rollout、UUID 或日志提交到仓库。
## Example output

```text
$ python tools/retry-watchdog/watchdog.py --version
watchdog.py 1.0.2
exit=0
```
## Exit codes

`0` means a check or retry loop ended normally; `2` means `CODEX_HOME` is unavailable; `3` means another watchdog owns the lock; `130` means Ctrl+C. `--version` returns `0`. See the [repository exit-code contract](../../docs/exit-code-contract.md) for the automation rules.

## Security notes

Watch only an authorized Codex session. Begin with `--once --dry-run`; SQLite, rollout, UUID, and log data can be sensitive and must stay outside commits. See [security boundaries](../../docs/security-boundaries.md) before running against a real runtime.
