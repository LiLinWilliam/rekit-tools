# 最小用法示例

这些示例只使用占位路径和测试数据，不会读取真实样本、会话或凭据。命令请在对应工具目录中执行；`<rekit-root>` 表示本地 rekit 根目录。

| 工具 | 示例 |
| --- | --- |
| render-entropy | `Get-Content examples/entropy.json | python tools/render-entropy/render_entropy.py entropy.png` |
| restore | `python tools/restore/restore.py --venv render --check-only` |
| verify-portability | `python tools/verify-portability/verify-portability.py` |
| verify | `python tools/verify/verify.py` |
| verify-review-fixes | `python tools/verify-review-fixes/verify-review-fixes.py` |
| doctor | `python tools/doctor/doctor.py --json --no-write` |
| launcher | `python tools/launcher/extract_xz.py <rekit-root>/archives` |
| migrate-after-move | `pwsh -File tools/migrate-after-move/00-after-move.ps1 --venv render --check-only` |
| environment-snapshot | `python tools/environment-snapshot/02-snapshot-environments.py` |
| toolchain-installers | `pwsh -File tools/toolchain-installers/10-build-binwalk.ps1` |
| venv-install-all | `pwsh -File tools/venv-install-all/12-venv-install-all.ps1 --check-only` |
| retry-watchdog | `python tools/retry-watchdog/watchdog.py --thread <thread-uuid> --once --dry-run` |

脚本会根据当前环境写入各自定义的日志或清单；这些运行产物应保留在本地，并由仓库的忽略规则排除。
