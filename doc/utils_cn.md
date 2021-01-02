MCDReforged 工具文档
---

## rcon_connection.py

`from utils.rcon import RconConnection`

这是一个简易的 rcon 客户端

### RconConnection.RconConnection(address, port, password, logger=None)

创建一个 rcon 客户端实例

`address` 是一个 `str`, 代表 rcon 服务器的地址

`port` 是一个 `int`, 代表 rcon 服务器的端口

`password` 是一个 `str`, 代表 rcon 的密码

(可选) `logger` 是一个 `logging.Logger` 的实例。这是用于输出一些警告信息所用

### RconConnection.connect() -> bool

开始连接至 rcon 服务器并尝试进行登录。如果登录成功，返回 `True`；否则返回 `False`

### RconConnection.disconnect()

从 rcon 服务器端口

### RconConnection.send_command(command, max_retry_time=3) -> str

向服务器发送一个 `str` 类型的命令 `command`

返回一个代表着命令执行结果的 `str`

`max_retry_time` 是最大失败尝试次数，如果超出了次数限制，这个方法会返回 None

## rtext.py

`from utils.rtext import *`

推荐阅读 Minecraft Wiki 中关于 [原始JSON文本格式](https://minecraft-zh.gamepedia.com/%E5%8E%9F%E5%A7%8BJSON%E6%96%87%E6%9C%AC%E6%A0%BC%E5%BC%8F) 的页面

这是一个 Minecraft 高级文本容器库

受 [Pandaria98](https://github.com/Pandaria98) 制作的 [MCD stext API](https://github.com/TISUnion/rtext) 启发

### RColor

`RColor` 储存着 Minecraft 的所有颜色代码

- `RColor.black`
- `RColor.dark_blue`
- `RColor.dark_green`
- `RColor.dark_aqua`
- `RColor.dark_red`
- `RColor.dark_purple`
- `RColor.gold`
- `RColor.gray`
- `RColor.dark_gray`
- `RColor.blue`
- `RColor.green`
- `RColor.aqua`
- `RColor.red`
- `RColor.light_purple`
- `RColor.yellow`
- `RColor.white`

### RStyle

`RStyle` 储存着 Minecraft 所有的样式代码

- `RStyle.bold`
- `RStyle.italic`
- `RStyle.underlined`
- `RStyle.strike_through`
- `RStyle.obfuscated`

### RAction

`RAction` 储存着所有点击事件的行为

- `RAction.suggest_command`
- `RAction.run_command`
- `RAction.open_url`
- `RAction.open_file`
- `RAction.copy_to_clipboard`

### RTextBase

`RText` 以及 `RTextList` 的基类

#### RTextBase.to_json_object()

返回一个代表其数据的 `dict`

#### RTextBase.to_json_str()

返回一个代表其数据的 json 格式的 `str`。这可用做例如 `/tellraw <target> <message>` 的第二个参数

#### RTextBase.to_plain_text()

返回一个用于控制台显示的朴素字符串。忽略其中的点击、悬浮事件

#### RTextBase.__str__()

返回 `RTextBase.to_plain_text()`

#### RTextBase.__add__, RTextBase.__radd__

返回一个由合并两个运算符得来的 `RTextList` 

### RText

文本容器类

#### RText.RText(text, color=RColor.reset, styles=None)

创建一个由指定文本以及颜色构成的 `RText`。`styles` 可以是一个 `RStyle` 或者是一个 `RStyle` 的 `list`

#### RText.set_click_event(action, value) -> RText

设置一个动作为 `action`，值为 `value`的点击事件

`action` 以及 `value` 均为 `str`

返回应用点击事件后的 RText 自身

#### RText.c(action, value) -> RText

同 `RText.set_click_event`

#### RText.set_hover_text(*args) -> RText

设置悬浮文本

参数 `*args` 将会用于创建一个 `RTextList` 实例。对于参数的约束条件请参考下文的 `RTextList` 构造函数

返回应用悬浮文本后的 RText 自身

#### RText.h(*args) -> RText

同 `RText.set_hover_text`


### RTextTranslation

可翻译的文本容器类

例子：`RTextTranslation('advancements.nether.root.title', color=RColor.red)`

#### RTextTranslation.RTextTranslation(text, color=RColor.reset, styles=None)

创建一个由指定翻译键字的 `RTextTranslation`。其余参数同 `RText`


### RTextList

一个由 RText 组成的列表

当转换为 json 格式用于输出至游戏中时，会在前面额外添加一个空串，从而防止第一个元素的样式影响到后方元素

#### RTextList.RTextList(*args)

`*args` 中的对象可以为一个 `str`, 一个 `RText`, 一个 `RTextList` 或者任何实现了 `__str__` 方法的类。它们都会被转化为 `RText`

---------

`RTextBase` 可以被当做 `message` 参数在以下的插件 API 中使用:

- `server.tell`
- `server.say`
- `server.reply`
- `add_help_message`

因 `server.reply` 等方法会自动将 `RTextBase` 对象转换为朴素文本，所以没有必要判断控制台这个特例。

#### RTextList.append(*args)

将若干个元素添加至当前 `RTextList` 的末尾

`*args` 中的对象可以为一个 `str`, 一个 `RText`, 一个 `RTextList` 或者任何实现了 `__str__` 方法的类。它们都会被转化为 `RText`
