# environment-snapshot

**02-snapshot-environments.py** 使用 rekit 的 uv pip freeze 记录已安装版本，不执行升级。它还会把 editable 安装的本地源映射为相对路径并记录当前 Git 提交。

## 用法

~~~powershell
python .\tools\environment-snapshot\02-snapshot-environments.py
~~~

脚本必须在包含 bin/_environment、venv/ 和 requirements/ 的 rekit 根目录中运行。它会遍历 _environment.VENVS，对每个环境调用 uv pip freeze --python <venv>/Scripts/python.exe。

## 输入与输出

- 输入是当前 rekit 的虚拟环境和 uv 可执行文件；不接受命令行参数。
- 输出为 requirements/<环境名>.txt 与 requirements/manifest.json，并在终端打印 <环境名>: <数量> pinned entries。
- 普通依赖必须带 ==，否则脚本抛出 ValueError: Unpinned requirement: ...。
- manifest.json 记录生成时间、每个环境的锁定条目数量和 editable 源的 path、commit。
