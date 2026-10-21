# rekit-tools

`rekit-tools` 是一组面向 Windows 的逆向工程、运行时验证与开发环境辅助工具源码。仓库只保留可审阅的脚本和小型原生启动器，不携带完整运行时、样本、日志或第三方二进制。

## 工具清单

- `tools/render-entropy/`：把 binwalk 熵块 JSON 渲染成固定尺寸 PNG；依赖声明在 `requirements/render.txt`。
- `tools/restore/`：离线恢复锁定的 Python 环境，并在失败时保留回滚边界。
- `tools/verify-portability/`：验证搬迁后的启动器、离线恢复和可移植 rizin。
- `tools/verify/`：验证参数、标准输入、JSON 输出、工具进程边界和受保护目录。
- `tools/verify-review-fixes/`：回归检查渲染器独立性、原始调用和 JVM 堆配置。
- `tools/doctor/`：输出环境体检结果和 JSON 证据；包含 PowerShell 入口。
- `tools/launcher/`：Windows 原生启动器、XZ 提取脚本和启动器构建脚本。
- `tools/retry-watchdog/`：针对 Codex 会话的只读状态观察、排队重试与模型探测脚本。会话 UUID、工作区路径和运行日志必须由使用者在本机提供。

Frida 目录在源工作区中只有设备端服务器二进制和压缩包，没有符合本仓库范围的快速集成小脚本，因此没有复制；二进制也不纳入仓库。

## 安装与使用

建议使用 Python 3.11 或更新版本，并在隔离虚拟环境中安装需要的依赖：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r .\tools\render-entropy\requirements\render.txt
```

示例：

```powershell
# 将熵块 JSON 渲染为 PNG
Get-Content .\entropy.json | python .\tools\render-entropy\render_entropy.py .\entropy.png

# 解压同目录下的 .xz 文件（不会覆盖已有非空输出）
python .\tools\launcher\extract_xz.py .\archives

# 只读演练 watchdog；请自行提供真实会话 UUID
python .\tools\retry-watchdog\watchdog.py --thread <thread-uuid> --once --dry-run
```

`restore.py`、三个验证脚本、`doctor.py` 和启动器构建脚本原本依赖完整的 rekit 运行时目录（例如 `bin/`、`requirements/` 和本机工具链）。本仓库只提供源码，运行前应在授权的隔离环境中补齐这些依赖，并确认输出目录不会包含隐私或秘密。

## 贡献约定

每次只提交一个工具：从最新 `main` 创建一个短分支，完成检查后提交一个 PR 并合并。提交前请运行 Python 编译检查和针对性冒烟测试，确认 `git diff --check` 通过。

## 安全与免责声明

本项目仅用于你拥有或明确获准分析的系统、应用和设备上的授权安全研究、可移植性验证与开发维护。使用者必须遵守适用法律、合同和组织政策。作者不对未授权访问、数据损失、服务中断或第三方软件行为负责。请勿提交 API key、token、密码、会话日志、样本、私有路径、运行时二进制或其他个人资料。
