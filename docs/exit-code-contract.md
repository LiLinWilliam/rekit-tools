# 工具退出码约定

本文档记录当前源码中已经实现的退出码。退出码是脚本与 CI、PowerShell 包装器之间的接口；调用方应优先依据退出码判断成功，不要只匹配终端输出。

## 约定范围

- `0` 表示命令完成了它声明的工作。对于持续运行的 watchdog，`0` 也表示一次检查或重试循环按参数正常结束。
- 非零值表示参数、依赖、输入或运行时失败。没有显式返回码的 Python 异常由 Python 解释器转换为非零退出码；该数值不属于 rekit-tools 的稳定接口。
- PowerShell 工具链脚本使用 `throw` 报告失败，宿主会以非零状态结束；`doctor.ps1`、`migrate-after-move.ps1` 和 `venv-install-all.ps1` 会转发被调用程序的 `$LASTEXITCODE`。
- `--version` 是只读操作，所有 Python 入口都以 `0` 返回并只输出一行版本信息。

## 工具表

| 工具目录 | 成功 | 明确的非零码 | 说明 |
| --- | ---: | ---: | --- |
| `doctor` | `0` | `1` | 所有健康检查通过返回 `0`；任一检查失败返回 `1`。`90-doctor.ps1` 原样转发 `doctor.exe` 的状态。 |
| `environment-snapshot` | `0` | 未固定 | 成功写入 `requirements/*.txt` 和 `manifest.json` 后正常结束。冻结环境、Git 修订或文件写入异常会由 Python 解释器报告非零状态。 |
| `launcher` | `0` | 未固定 | `extract_xz.py` 成功处理目录后返回 `0`；归档读取或输出文件异常属于未捕获运行时错误。`01-build-launchers.ps1` 在 C 编译失败时 `throw`。 |
| `migrate-after-move` | 依被调用程序 | 依被调用程序 | `00-after-move.ps1` 先运行 `repair.exe`，成功后运行 `doctor.exe`，并转发最后一个程序的 `$LASTEXITCODE`；repair 失败时立即转发其状态。 |
| `render-entropy` | `0` | `2`, `3` | PNG 写入成功返回 `0`；JSON、输入数据或文件操作错误返回 `2`；Pillow 不可用返回 `3`。 |
| `restore` | `0` | `1` | 所有选定虚拟环境安装、`pip check` 和导入检查通过后输出 `Restore verified` 并返回 `0`；失败时回滚已替换环境并返回 `1`。 |
| `retry-watchdog` | `0` | `2`, `3`, `130` | `--once`、`--dry-run` 或正常完成返回 `0`；`CODEX_HOME` 不存在返回 `2`；已有 watchdog 锁返回 `3`；收到 Ctrl+C 返回 `130`。达到重试上限时由参数路径结束并返回 `0`。 |
| `toolchain-installers` | `0` | 未固定 | 各 PowerShell 安装器在 cargo、Gradle、Meson、Ninja、下载、解压或导入检查失败时 `throw`；成功路径自然结束。`12-rizin-setup.ps1` 成功时打印 `MESON-SETUP-OK`。 |
| `venv-install-all` | 依被调用程序 | 依被调用程序 | `12-venv-install-all.ps1` 直接运行 `repair.exe` 并转发 `$LASTEXITCODE`。 |
| `verify` | `0` | `1` | 功能验收报告的 `ok` 为真返回 `0`，受保护路径、进程边界或 JSON 检查失败返回 `1`。 |
| `verify-portability` | `0` | `1` | 所有可移植性检查通过返回 `0`，任一检查失败返回 `1`。 |
| `verify-review-fixes` | `0` | `1` | review-fix 验收报告通过返回 `0`，任一回归检查失败返回 `1`。 |

## 在自动化中使用

PowerShell 示例：

```powershell
python tools/verify/verify.py
if ($LASTEXITCODE -ne 0) {
    throw "verify failed: $LASTEXITCODE"
}
```

批处理或 CI 应保留原始状态：

```powershell
& .\tools\doctor\90-doctor.ps1 --no-write
$status = $LASTEXITCODE
Write-Host "doctor exit code: $status"
exit $status
```

这些示例只依赖仓库中已有的入口，不会创建虚拟环境、下载工具链或修改受保护目录。需要安装或恢复环境的命令仍应按照各工具 README 中的授权和在线/离线参数执行。
