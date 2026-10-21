# venv-install-all

**12-venv-install-all.ps1** 是批量恢复入口，直接把参数转发给 bin/repair.exe。

## 用法

~~~powershell
pwsh -File .\tools\venv-install-all\12-venv-install-all.ps1 --check-only
pwsh -File .\tools\venv-install-all\12-venv-install-all.ps1 --venv render --check-only
pwsh -File .\tools\venv-install-all\12-venv-install-all.ps1 --venv render --online
~~~

支持 repair.exe 的 --venv、--check-only、--online 参数。默认不联网，显式 --online 才允许索引访问。

## 输入与输出

脚本需要 rekit 根目录的 bin/repair.exe 和 requirements 快照。repair 的标准输出和退出码直接返回给调用方；成功后可继续运行 doctor 验证导入与依赖。
