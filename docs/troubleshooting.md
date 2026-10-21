# 常见错误排查

本页只记录仓库脚本已经体现的检查边界。命令中的 `<rekit-root>` 是本地 rekit 根目录占位符，不应替换成仓库中的 `tools` 目录。

## 找不到 `env.ps1`、`repair.exe` 或 `_environment`

迁移和虚拟环境脚本依赖 rekit 的 `bin/`、`requirements/`、`toolchain/` 与 `_environment` 布局。先在目标根目录执行 `python tools/doctor/doctor.py --json --no-write`，根据 JSON 报告补齐目录或修复路径，再运行 `00-after-move.ps1`。不要把真实用户目录或日志复制进仓库。

## 离线安装缺少包

`restore.py`、环境快照和工具链脚本默认优先使用已有缓存或离线依赖。若报告指出 wheel、Cargo crate、Gradle 缓存或 uv 缓存缺失，应在隔离环境中准备依赖后重试；只有明确允许联网时才使用 `--online` 或 `-Online`。离线失败不应通过提交缓存、二进制或日志来“修复”。

## rizin 构建无法重新配置

`12-rizin-setup.ps1` 使用 Meson，已有构建目录的配置冲突时先清理旧的 Meson 元数据，再按脚本提供的 `--wipe` 路径重新配置。确认 Ninja、MSVC 和目标 prefix 可用后，再执行 `13-rizin-build.ps1` 并用 `rizin -v` 验证。

## binwalk、jadx 或 Frida 安装失败

这些脚本分别依赖 Cargo/MSVC、Gradle/JDK、CPython 3.12/uv 以及 Frida server 下载工具。先阅读对应脚本的参数和输出，确认版本工具在 PATH 中；Frida 的在线模式还需要 `curl.exe` 与 `.xz` 解压流程。失败时保留终端错误供本地排查，不要上传访问令牌、会话标识或完整日志。

## 熵图冒烟测试失败

渲染器需要 Pillow。进入隔离 Python 环境后执行 `python -m pip install -r tools/render-entropy/requirements/render.txt`，再用 `examples/entropy.json` 测试：

```powershell
Get-Content examples/entropy.json | python tools/render-entropy/render_entropy.py entropy.png
```

输出应是 PNG 文件；若输入 JSON 缺少 `blocks`、`start`、`end` 或 `entropy` 字段，先修正数据格式。

## 验证脚本输出异常

`verify.py`、`verify-portability.py` 和 `verify-review-fixes.py` 会把检查结果写入被 `.gitignore` 排除的 logs 目录。先查看 JSON 摘要和 stdout/stderr，再核对样本路径变量和本地工具链版本；不要把样本、报告或会话文件加入暂存区。
