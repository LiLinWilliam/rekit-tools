# rekit-tools

[![CI](https://github.com/LiLinWilliam/rekit-tools/actions/workflows/ci.yml/badge.svg)](https://github.com/LiLinWilliam/rekit-tools/actions/workflows/ci.yml)

`rekit-tools` 是一组面向 Windows 的可审计工具：它们围绕本地 rekit 运行时提供环境快照、恢复、健康检查、可迁移性验证、熵图渲染和 Codex 会话看护。工具保持独立目录，优先使用 rekit 内置的运行时与路径，不把依赖写入系统 Python 或全局 PATH。

## 展示

`render-entropy` 接收 binwalk 风格的 `blocks` JSON，并生成固定尺寸的 PNG。下面的图由仓库中的真实渲染器生成，再缩小为文档预览图（原始输出为 2048×1024，文件约 21 KB）：

![render-entropy 示例](docs/assets/entropy-demo.png)

```powershell
'{"blocks":[{"start":0,"end":512,"entropy":1.2},{"start":512,"end":1024,"entropy":5.8},{"start":1024,"end":1536,"entropy":7.6}]}' | python .\tools\render-entropy\render_entropy.py .\entropy-demo.png
```

命令成功后会在当前目录写入 `entropy-demo.png`；脚本会把输出扩展名规范为 `.png`，并用临时文件替换目标文件。

## 工具一览

| 工具 | 用途 | 典型入口 |
| --- | --- | --- |
| `doctor` | 检查 rekit 原生工具、Python 环境与关键目录 | `python tools/doctor/doctor.py --json --no-write` |
| `environment-snapshot` | 记录各虚拟环境的锁定包版本与 editable 源提交 | `python tools/environment-snapshot/02-snapshot-environments.py` |
| `launcher` | 构建 Windows 原生 launcher，并提供 `.xz` 解包辅助 | `python tools/launcher/extract_xz.py <dir>` |
| `migrate-after-move` | 移动 rekit 后恢复环境并重新执行 doctor | `pwsh -File tools/migrate-after-move/00-after-move.ps1 --check-only` |
| `render-entropy` | 将 JSON 熵块渲染成 PNG | `Get-Content entropy.json | python tools/render-entropy/render_entropy.py entropy.png` |
| `restore` | 按 requirements 快照离线恢复虚拟环境 | `python tools/restore/restore.py --venv render --check-only` |
| `retry-watchdog` | 只读观察 Codex SQLite，并按策略排队重试 | `python tools/retry-watchdog/watchdog.py --thread <thread-uuid> --once --dry-run` |
| `toolchain-installers` | 构建或配置 binwalk、jadx、rizin、Frida | 见对应目录 README |
| `venv-install-all` | 通过 `repair.exe` 恢复全部虚拟环境 | `pwsh -File tools/venv-install-all/12-venv-install-all.ps1 --check-only` |
| `verify` | 执行真实工具边界、参数传递与 JSON/PNG 验收 | `python tools/verify/verify.py` |
| `verify-portability` | 在带空格的临时目录验证离线恢复与可迁移路径 | `python tools/verify-portability/verify-portability.py` |
| `verify-review-fixes` | 回归渲染器独立性、原生调用与 Ghidra 堆配置 | `python tools/verify-review-fixes/verify-review-fixes.py` |

每个工具的参数、输入、输出和副作用写在对应的 [`tools/`](tools/) README 中。

## 快速开始

渲染器只需要 Python 3 和 Pillow：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r .\tools\render-entropy\requirements\render.txt
Get-Content .\entropy.json | python .\tools\render-entropy\render_entropy.py .\entropy.png
```

依赖 rekit 根目录的工具必须在真实 rekit 根目录中运行；`<rekit-root>` 只是文档占位符，不应替换为本仓库的 `tools` 目录。迁移、恢复和验证脚本会把日志、清单与临时结果写回 rekit 根目录，仓库规则会忽略这些运行产物。

## 仓库结构

```text
tools/<tool-name>/   一个工具及其 README
tests/               纯函数与边界测试
docs/                安全边界、排错与安装说明
examples/            不含真实凭据的最小命令索引
.github/workflows/   CI 与发布自动化
```

不要把 `venv/`、`toolchain/`、`samples/`、`logs/`、缓存、私有会话数据库或 Frida server 提交到仓库。涉及真实样本、设备或 Codex 会话时，只在获得授权的本地环境中运行，并先阅读 [`SECURITY.md`](SECURITY.md) 与[安全边界说明](docs/security-boundaries.md)。

## 贡献

新工具使用 `tool/<name>` 分支，文档使用 `docs/<name>` 分支。提交前运行 `python -m pytest -q tests --cov=tools --cov-report=term-missing`、`git diff --check`，并检查作者与敏感信息。完整流程见 [`CONTRIBUTING.md`](CONTRIBUTING.md)。
