# doctor

**doctor.py** 在 rekit 根目录执行一组只读健康检查：原生工具版本、各虚拟环境的导入与依赖、Java/Ghidra、原生参数传递，以及关键目录和 Frida server 的存在性。

## 用法

~~~powershell
python .\tools\doctor\doctor.py --json --no-write
python .\tools\doctor\doctor.py
pwsh -File .\tools\doctor\90-doctor.ps1
~~~

- **--json** 把每项检查和总结果打印为 JSON。
- **--no-write** 不写 logs/doctor.json 和 logs/doctor.txt；默认会写入这两个文件。
- **90-doctor.ps1** 只调用 bin/doctor.exe，并把参数原样转发。

## 输入与输出

脚本通过 rekit 根目录的 bin/_environment 读取路径和虚拟环境列表，不读取仓库中的样本。成功时退出码为 0，任一检查失败时为 1。文本模式会打印 PASS: <通过数>/<总数> checks；JSON 模式的顶层 ok 和每个 checks[].ok 可用于自动化判断。

请在真实 rekit 根目录中运行；本仓库的 tools 目录不是 rekit 根目录。
## Example output

The version-only path is safe to run before a full rekit root is available:

```text
$ python tools/doctor/doctor.py --version
doctor 1.0.2
exit=0
```
