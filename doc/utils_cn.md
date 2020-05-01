MCDReforged 工具文档
---

## rcon.py

`from utils.rcon import Rcon`

这是一个简易的 rcon 客户端

### Rcon.Rcon(address, port, password, logger=None)

创建一个 rcon 客户端实例

`address` 是一个 `str`, 代表 rcon 服务器的地址

`port` 是一个 `int`, 代表 rcon 服务器的端口

`password` 是一个 `str`, 代表 rcon 的密码

(可选) `logger` 是一个 `logging.Logger` 的实例。这是用于输出一些警告信息所用

### Rcon.connect() -> bool

开始连接至 rcon 服务器并尝试进行登录。如果登录成功，返回 `True`；否则返回 `False`

### Rcon.disconnect()

从 rcon 服务器端口

### Rcon.send_command(command, max_retry_time=3) -> str

像服务器发送一个 `str` 类型的命令 `command`

返回一个代表着命令执行结果的 `str`

`max_retry_time` 是最大失败尝试次数，如果超出了次数限制，这个方法会返回 `None`

## stext.py

`from utils.stext import *`

推荐阅读 Minecraft Wiki 中关于 [原始JSON文本格式](https://minecraft-zh.gamepedia.com/%E5%8E%9F%E5%A7%8BJSON%E6%96%87%E6%9C%AC%E6%A0%BC%E5%BC%8F) 的页面

这是一个 Minecraft 高级文本容器库

受 [Pandaria98](https://github.com/Pandaria98) 制作的 [MCD stext API](https://github.com/TISUnion/stext) 启发

### SColor

`SColor` 储存着 Minecraft 的所有颜色代码

- `SColor.black`
- `SColor.dark_blue`
- `SColor.dark_green`
- `SColor.dark_aqua`
- `SColor.dark_red`
- `SColor.dark_purple`
- `SColor.gold`
- `SColor.gray`
- `SColor.dark_gray`
- `SColor.blue`
- `SColor.green`
- `SColor.aqua`
- `SColor.red`
- `SColor.light_purple`
- `SColor.yellow`
- `SColor.white`

### SStyle

`SStyle` 储存着 Minecraft 所有的样式代码

- `SStyle.bold`
- `SStyle.italic`
- `SStyle.underlined`
- `SStyle.strike_through`
- `SStyle.obfuscated`

### SAction

`SAction` 储存着所有点击事件的行为

- `SAction.suggest_command`
- `SAction.run_command`
- `SAction.open_url`
- `SAction.open_file`
- `SAction.copy_to_clipboard`

### STextBase

`SText` 以及 `STextList` 的基类

#### STextBase.to_json_object()

返回一个代表其数据的 `dict`

#### STextBase.to_json_str()

返回一个代表其数据的 json 格式的 `str`。这可用做例如 `/tellraw <target> <message>` 的第二个参数

#### STextBase.to_plain_text()

返回一个用于控制台显示的朴素字符串。点击事件以及悬浮时间将会被忽略s

#### STextBase.__str__()

返回 `STextBase.to_plain_text()`

#### STextBase.__add__, STextBase.__radd__

返回一个由合并两个运算符得来的 `STextList` 

### SText

文本容器类

#### SText.SText(text, color=SColor.white, styles=None)

创建一个由指定文本以及颜色构成的 `SText`。`styles` 可以是一个 `SStyle` 或者是一个 `SStyle` 的 `list`

#### Stext.set_click_event(action, value) -> SText

设置点击事件，动作为 `action`，值为 `value`

`action` 以及 `value` 均为 `str`

返回 Stext 自身

#### Stext.set_hover_event(*args) -> SText

设置悬浮文本

参数 `*args` 将会用于创建一个 `STextList` 实例。对于参数的约束条件请参考下文的 `STextList` 构造函数

返回 Stext 自身

### STextList

一个由 SText 组成的列表

### STextList.STextList(*args)

`*args` 中的对象可以为一个 `str`, 一个 `SText`, 一个 `STextList` 或者任何实现了 `__str__` 方法的类。它们都会被转化为 `SText`

---------

`STextBase` 可以被当做 `message` 参数在以下的插件 API 中使用:

- `server.tell`
- `server.say`
- `server.reply`
- `add_help_message`

对于控制台的特判是不必要的，因为 `server.reply` 等方法会自动将 `STextBase` 对象转换为朴素文本
