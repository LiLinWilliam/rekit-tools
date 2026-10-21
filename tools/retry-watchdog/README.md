# Codex 自动重试守护 (codex-retry-watchdog)

## 先给结论（2026-10-20 18:02 实测）

**不是账号被标记，账号是好的。** 同一个账号、同一时间段：

| 会话 | 模型 | 最近 90 分钟 turn |
|---|---|---|
| <thread-id-prefix>（<workspace-path> 那个任务） | gpt-6-astra / ultra | **failed 21 次**，全是 at capacity |
| <thread-id-prefix>（Firefox 那个会话） | gpt-6.1-sol / xhigh | **completed 8 次**（17:11、17:17、17:21 都正常完成） |

模型目录（18:02 刚刷新）里：
    gpt-6.1-sol   priority=1
    gpt-6-astra   priority=2
    gpt-6-sol     priority=4
    ...

所以被"卡"的是 **gpt-6-astra 这个模型的容量**（服务端返回 serverOverloaded /
"Selected model is at capacity"），不是你的账号被针对。体感上确实像被折磨，
但它针对的是 astra 这个模型档，不是账号本身。

## 到底发生了什么

后台 Codex 会话 **<thread-uuid>**
（cwd  <workspace-path> ，模型  gpt-6-astra ，reasoning  ultra ，service_tier  priority）
在 17:38 之后反复起 turn、反复失败：

    Turn error: Selected model is at capacity. Please try a different model.
    {"codexErrorInfo":"serverOverloaded"}

每次失败后 Codex 自己会 fork 一个新 turn 重来（日志里 user_input_count=0 的自动恢复），
但 Codex 内部有重试上限（协议错误码里有 "Reached the retry limit for responses"），
到上限后会话就停在"失败且没人动"的状态，等外部再触发。

## 为什么不能直接用 codex exec resume

外部进程续跑同一会话会撞锁：

    thread-store conflict: thread <thread-id-prefix>-... already has an active writer
    Error: thread/resume: thread/resume failed ... (code -32600)

桌面端的 app-server 只要还开着这个会话，就持有 thread 写锁，任何外部 app-server
（codex exec resume / 新 daemon）都进不去。所以"拔插头式"接管不可行。

## 交互桥：codex queue（纯空输入重试）

Codex 自带的官方命令：

    codex queue --thread <会话ID> --message " "

    * 写的是 ~/.codex/queue_1.sqlite 的 queued_items 表，不申请 thread 写锁
    * 桌面端 app-server 常驻监听队列，实测 30 秒内消费
    * 消息内容用**单个空格**：等价于空输入，不向会话写入任何文案，
      效果就是"纯粹的重试"（和 Codex 自己的自动恢复 turn 一样）
    * 消费后立刻起新 turn（日志出现新 submission.id / turn.id）

脚本只往队列里丢一个空格，真正的重试由 Codex 自己在桌面端跑。

## 守护逻辑

    每 interval 秒读一次 sqlite（只读）：
      turn = 该会话日志里最新的 turn.id
      status = thread_history 里该 turn 的状态（按 turn_id 查，绕开 fork 后的 id 错位）

      如果 status == inProgress 且未超龄      -> 让路，等它跑
      如果最近有活动（< stall-seconds）        -> 让路，等它跑（桌面端可能在自动重试）
      如果 status == completed                 -> 已完成，再观察一个周期确认，退出
      否则（停摆：failed / 无活动）            -> codex queue 一个空格（纯重试）
            等队列被消费（默认 90s）
            跟踪新 turn 直到 completed / failed
            failed -> 指数退避（30s 起，上限 300s）后再排队
            无限循环，直到 turn 正常完成

若 queue 消息一直没人消费（比如桌面端被关了），加 --exec-fallback 会自动回退到
codex exec resume（此时没有写锁冲突）。

## 文件

    watchdog.py    核心守护脚本（Python 3，无第三方依赖）
    start.ps1      后台启动（隐藏窗口，写 pid 文件）
    stop.ps1       停止守护
    logs/          运行日志（watchdog.log、exec-*.jsonl）

## 用法

    # 只看状态，不执行
    python watchdog.py --thread <thread-uuid> --once --dry-run

    # 后台挂守护（推荐，当前已挂）
    powershell -ExecutionPolicy Bypass -File start.ps1 -Thread <thread-uuid>

    # 前台跑、看实时日志
    python watchdog.py --thread <thread-uuid> --interval 15

    # 停止
    powershell -ExecutionPolicy Bypass -File stop.ps1

## 主要参数

    --thread              目标会话 UUID（必填）
    --interval            轮询间隔秒（默认 15）
    --stall-seconds       无活动多久算停摆（默认 120）
    --max-turn-age        inProgress turn 超过多久视为卡死（默认 7200）
    --consume-timeout     queue 后等消费的秒数（默认 90）
    --turn-timeout        跟踪单轮的最长秒数（默认 3600）
    --max-attempts        最多接管次数，0 = 不限（默认 0）
    --backoff-base/max    失败退避（默认 30 / 300 秒）
    --prompt              排队消息内容，默认单个空格（纯重试）；可传入自定义文本
    --exec-fallback       队列无人消费时回退 exec resume
    --model / --effort    仅 exec 兜底时生效
    --dry-run / --once    演练模式
    --no-lock             不加单实例锁

## 注意

* 守护每轮只排队一条空格消息，等价于空输入重试，不向会话写入任何文案；
  UI 里最多出现一个空用户气泡。
* 只读 sqlite，不会破坏 Codex 的 WAL 数据；所有写操作都通过 codex 自己的命令完成。
* 根因是 gpt-6-astra 的模型容量。想立刻把任务干完，可以换成 gpt-6.1-sol
  （priority=1，刚实测可用，目录描述是 near-Astra performance），
  或者继续等 astra 恢复（守护会一直重试）。
* 如果桌面端一直自己在重试（日志持续有活动），守护会安静等待，不重复注入消息。

## 实测记录（2026-10-20）

    17:55  诊断出 serverOverloaded / at capacity；桌面端自动重试已停摆 ~4 分钟
    17:56  codex queue 注入文案消息 -> 桌面端 1 秒内消费，起 turn（验证交互桥成立）
    17:58  桌面端恢复了一阵自动重试（<thread-id-prefix>、<thread-id-prefix> 轮次）
    17:59  codex queue 注入空格消息 -> 18:00:25 被消费，turn 跑了 42 秒并执行了工具调用
           （codex_core::tools::parallel），仍被服务端容量打断
    18:02  证据确认：同账号 gpt-6.1-sol 会话 8 轮 completed，astra 21 轮 failed
    18:02  守护进程挂后台（纯空格无限重试版），等待 astra 容量恢复
