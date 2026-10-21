# render-entropy

**render_entropy.py** 将包含 blocks 数组的 JSON 转换为 2048×1024 的 PNG。每个块需要 start、end 和 entropy 字段，熵值会限制在 0 到 8。

## 用法

~~~powershell
'{"blocks":[{"start":0,"end":512,"entropy":1.2},{"start":512,"end":1024,"entropy":7.6}]}' |
  python .\tools\render-entropy\render_entropy.py .\entropy.png
~~~

也可以把 binwalk 生成的 JSON 文件通过标准输入传入：

~~~powershell
Get-Content .\entropy.json |
  python .\tools\render-entropy\render_entropy.py .\entropy.png
~~~

## 输入与输出

程序从标准输入读取 JSON，位置参数是输出路径；无论传入什么扩展名，实际输出都会规范为 <路径>.png。成功退出码为 0，PNG 头为标准 89 50 4E 47。输入缺少 blocks、块字段无效或文件无法写入时，错误会写到 stderr 并返回 2。未安装 Pillow 时返回 3，并提示使用 render 环境恢复依赖。
