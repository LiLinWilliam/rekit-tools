# restore

**restore.py** 按 requirements/<venv>.txt 的锁定版本恢复 rekit 虚拟环境，默认使用本地 uv 缓存和离线模式；替换环境前会把旧目录移动到 backups/，失败时尝试回滚。

## 用法

~~~powershell
python .\tools\restore\restore.py --venv render --check-only
python .\tools\restore\restore.py --venv misc --venv render
python .\tools\restore\restore.py --venv render --online
~~~

- --venv 可重复，取值来自 bin/_environment.VENVS；不传则处理全部环境。
- --check-only 在 temp/restore-check-* 中验证，不替换已安装环境。
- --online 显式允许访问包索引；默认追加 --offline。

## 输入与输出

脚本需要 rekit 根目录的 Python runtime、uv、requirements 快照和可选的 toolchain/vcredist/*.dll。成功时打印 Restore verified. Log: ... 并返回 0；详细命令输出写入 logs/restore-*.log。参数或依赖失败时返回 1，并保留原环境（若已经移动到备份目录则恢复）。
