# 安全边界与授权使用

`rekit-tools` 只适用于你拥有或明确获准维护、测试的 Windows 环境。仓库中的脚本可以检查本地工具链、读取会话数据库、恢复虚拟环境或调用本地命令；它们不会替你取得目标授权，也不会把未授权操作变成合规操作。

## 先确认三个边界

运行前写下这三项，并把它们限制在本地工作目录：

1. **授权边界**：目标机器、样本、Codex 会话和设备的所有者或授权人。
2. **路径边界**：真实 rekit 根目录 `<rekit-root>`，以及允许写入的 `logs/`、`temp/`、`backups/` 等子目录。
3. **数据边界**：本次操作需要的最小样本和最小日志；不要复制用户目录、会话数据库或凭据来“方便排查”。

## 工具的实际读写边界

| 工具 | 主要读取 | 可能写入 | 需要特别确认 |
| --- | --- | --- | --- |
| `doctor` | `bin/`、虚拟环境、Java/Ghidra 与本地目录 | 默认写 `logs/doctor.*`；`--no-write` 时不写 | 检查结果是本机状态快照，不是对第三方目标的安全结论 |
| `environment-snapshot` | `uv pip freeze`、editable 源的本地 Git 提交 | `requirements/*.txt`、`requirements/manifest.json` | 只记录版本，不执行升级；快照可能包含本地路径，应先脱敏 |
| `restore`、`migrate-after-move`、`venv-install-all` | requirements、rekit runtime 与 uv 缓存 | `venv/`、`backups/`、`temp/`、`logs/` | 默认离线；只有明确传入 `--online` 才允许索引访问，先用 `--check-only` |
| `render-entropy` | 标准输入 JSON | 指定的 PNG 文件 | 输入只应来自已获授权的分析结果；不把真实样本加入仓库 |
| `verify` | 本地工具和 `REKIT_SAMPLE_APK` 指向的授权样本 | `logs/`，以及验证所需的本地项目目录 | 验证脚本会记录目录指纹；样本路径与输出必须脱敏 |
| `verify-portability` | runtime、缓存和构建产物 | `temp/portable path-*`、`logs/` | 它验证迁移边界，不等于完整克隆或所有工具都已验证 |
| `verify-review-fixes` | 本地 binwalk、launcher、Ghidra 与 JDK | `temp/review-check-*`、`logs/` | 只检查本地回归，不连接真实设备或会话 |
| `retry-watchdog` | `CODEX_HOME` 下的 SQLite 和 rollout | 日志；非 dry-run 时可能调用 `codex queue` 或 `codex exec resume` | 先用 `--once --dry-run`；只看护本人或明确授权的 thread |
| `launcher`、`toolchain-installers` | 本地源码、缓存、编译器和构建工具 | `bin/`、构建目录和 Frida 本地目录 | Frida 只有 `-Online` 才下载 server；构建产物不要提交 |

脚本的“只读”含义是针对目标数据或数据库的读写行为，不代表进程完全没有日志、临时目录或缓存副作用。运行前后应检查实际写入路径。

## 推荐操作顺序

1. 在真实 rekit 根目录执行 `python tools/doctor/doctor.py --json --no-write`，先确认路径和运行时。
2. 对恢复或迁移先执行 `--check-only`；对 `retry-watchdog` 先执行 `--once --dry-run`。阅读输出中的路径、thread 占位符和 verdict。
3. 只有在确认授权、路径和备份策略后，才启用写入或 `--online`/`-Online`。一次只处理一个环境或一个会话。
4. 保留脱敏后的摘要，删除或隔离本地日志、rollout、SQLite、样本和临时目录；不要把它们复制到仓库。
5. 提交前检查 `git status`、`git diff --check`，并扫描 token、key、私钥、完整路径、会话标识和其他个人数据。

## 发现泄露或越界行为时

立即停止传播并撤销或轮换已经暴露的凭据。不要把完整日志、数据库、样本或可利用细节贴到公开 Issue；按 [`SECURITY.md`](../SECURITY.md) 提交最小化、脱敏的报告。若脚本试图访问 `<rekit-root>` 之外的路径，先停止运行并保留命令、退出码和边界路径，避免用删除或强制覆盖掩盖问题。

本页描述的是仓库代码中的操作边界，不替代组织审批、第三方服务条款或适用法律。
