# rtext使用文档

## 准备

导入: `from utils import rtext`

推荐阅读 Minecraft Wiki 中关于 [原始JSON文本格式](https://minecraft-zh.gamepedia.com/%E5%8E%9F%E5%A7%8BJSON%E6%96%87%E6%9C%AC%E6%A0%BC%E5%BC%8F) 的页面

这是一个 Minecraft 高级文本容器库

受 [Pandaria98](https://github.com/Pandaria98) 制作的 [MCD stext API](https://github.com/TISUnion/rtext) 启发

---------

以下三个类需要作为参数在`RText`中使用

## RColor

`RColor` 类储存着 Minecraft 的所有颜色代码

<table class="wikitable" style="text-align:center;">
<tbody><tr>
<th rowspan="2">代码
</th>
<th rowspan="2">官方名称
</th></tr>
<tr>
<th>Rcolor代码</th></tr>
<tr style="background-color: #000; color: #FFF">
<td>§0</td>
<td>black</td>
<td>RColor.black
</td></tr>
<tr style="background-color: #00A; color: #FFF">
<td>§1</td>
<td>dark_blue</td>
<td>RColor.dark_blue
</td></tr>
<tr style="background-color: #0A0; color: #FFF">
<td>§2</td>
<td>dark_green</td>
<td>RColor.dark_green
</td></tr>
<tr style="background-color: #0AA; color: #FFF">
<td>§3</td>
<td>dark_aqua</td>
<td>RColor.dark_aqua
</td></tr>
<tr style="background-color: #A00; color: #FFF">
<td>§4</td>
<td>dark_red</td>
<td>RColor.dark_red
</td></tr>
<tr style="background-color: #A0A; color: #FFF">
<td>§5</td>
<td>dark_purple</td>
<td>RColor.dark_purple
</td></tr>
<tr style="background-color: #FA0">
<td>§6</td>
<td>gold</td>
<td>RColor.gold
</td></tr>
<tr style="background-color: #AAA">
<td>§7</td>
<td>gray</td>
<td>RColor.gray
</td></tr>
<tr style="background-color: #555; color: #FFF">
<td>§8</td>
<td>dark_gray</td>
<td>RColor.dark_gray
</td></tr>
<tr style="background-color: #55F; color: #FFF">
<td>§9</td>
<td>blue</td>
<td>RColor.blue
</td></tr>
<tr style="background-color: #5F5">
<td>§a</td>
<td>green</td>
<td>RColor.green
</td></tr>
<tr style="background-color: #5FF">
<td>§b</td>
<td>aqua</td>
<td>RColor.aqua
</td></tr>
<tr style="background-color: #F55">
<td>§c</td>
<td>red</td>
<td>RColor.red
</td></tr>
<tr style="background-color: #F5F">
<td>§d</td>
<td>light_purple</td>
<td>RColor.light_purple
</td></tr>
<tr style="background-color: #FF5">
<td>§e</td>
<td>yellow</td>
<td>RColor.yellow
</td></tr>
<tr style="background-color: #FFF">
<td>§f</td>
<td>white</td>
<td>RColor.white
</td></tr>
</tbody></table>

## RStyle

`RStyle` 类储存着 Minecraft 所有的样式代码

| 代码 | 官方名称 | Rstyle代码 |
| - | - | - |
| §k | obfuscated | RStyle.obfuscated |
| §l | bold | RStyle.bold |
| §m | strike_through | RStyle.strike_through |
| §n | underlined | RStyle.underlined |
| §o | italic | RStyle.italic |

## RAction

`RAction` 储存着所有点击事件的行为

| 行为 | 官方名称 | RAction代码 |
| - | - | - |
| 覆盖聊天框内容 | suggest_command | RAction.suggest_command |
| 执行命令 | run_command | RAction.run_command |
| 打开链接 | open_url | RAction.open_url |
| 打开文件 | open_file | RAction.open_file |
| 辅助到剪贴板 | copy_to_clipboard | RAction.copy_to_clipboard |

---------

以下为编写插件时真正需要的类

## RText类

该类的实例化：

```python
RText(text, color=RColor.white, styles=None)
```

`text` 是一个可以实现 `str()` 方法的对象或一个RText对象

`styles` 是一个 `RStyle` 对象或多个对象的 `list`

例子：

```python
RText('这是例子', color=RColor.blue, styles=None)
```

效果：

- 消息为有下划线的蓝色文字 `这是例子`

---------

该类拥有以下方法:

### set_click_event(action, value)

设置一个动作为 `action`，值为 `value`的点击事件

`action` 可以使用 `RAction.action` 或官方名称的 `str`

`value` 是要执行动作参数的 `str`

例子：

```python
RText('点我去主城').set_click_event(RAction.run_command, '/server lobby')
```

效果：

- 消息为 `点我去主城`
- 点击后执行 `/server lobby`

注：使用 `c(action, value)` 完全相同

### set_hover_text(*args)

用于设置鼠标指向时，显示的悬浮文本

不知道 `*args` 看 <https://www.jianshu.com/p/be92113116c8>

`*args` 将会用于创建一个 [RTextList](#rtl) 实例

例子：

```python
RText('§a欢迎新玩家加入服务器，点击欢迎').set_hover_text(r.RText('§7点击欢迎新人')).c(r.RAction.run_command, '欢迎新人')`
```

效果：

- 消息为绿色的 `欢迎新玩家加入服务器，点击欢迎`
- 鼠标指向时显示灰色的 `点击欢迎新人`
- 点击后发送 `欢迎新人`

注：使用 `h(*args)` 完全相同

<span id="rtl"></span>

## RTextList类

该类的实例化：

```python
RTextList(*args)
```

你可以使用任何可以被转化为 `RText` 的对象传递给 `RTextList`

---------

## 提示

- `RText` 和 `RTextList` 的对象可以被当做 `message` 参数在以下方法中使用: `server.tell`, `server.say`, `server.reply`, `add_help_message`

- 使用时别操心输出到控制台还是游戏内

---------

## 实例分析

### [QuickBackupM](https://github.com/TISUnion/QuickBackupM)

```python
from utils.rtext import *
```

```python
def command_run(message, text, command):
    return RText(message).set_hover_text(text).set_click_event(RAction.run_command, command)
```

将显示悬浮文本和点击运行指令封装为函数

需要一条信息同时有悬浮文本和点击执行指令时即可直接调用该函数

```python
except Exception as e:
        print_message(server, info, RText('§4删除失败§r，详细错误信息请查看服务端后台').set_hover_text(e), tell=False)
```

这里通过RText设置悬浮文本让玩家可以在游戏内查看错误详细信息

### [BotInit](https://github.com/MCDReforged-Plugins/BotInit/blob/master/BotInit.py)

```python
from utils import rtext as r
```

```python
server.add_help_message('!!bot', r.RText('显示机器人列表').c(r.RAction.run_command, '!!bot').h('点击显示机器人列表'))
```

这里使用RText作为add_help_message后半部分

`.h` 让玩家将鼠标指向这条帮助信息时显示 `点击显示机器人列表`

`.c` 让玩家点击这条帮助信息时说出 `!!bot`

```python
help_msg = {
    '': '',
    '§6!!bot': '§7显示机器人列表',
    '§6!!bot spawn <name>': '§7生成机器人',
    '§6!!bot kill <name>': '§7移除机器人',
    '§6!!bot reload': '§7从文件重载机器人列表',
    '§6!!bot add <name> <dim> <pos> <facing>': '§7添加机器人到机器人列表',
    '§6!!bot remove <name>': '§7从机器人列表移除机器人'
}
c = [r.RText(f'{a} {b}\n').c(r.RAction.suggest_command, a.replace('§6', '')).h(b) for a, b in help_msg.items()]
server.reply(info, r.RTextList(*c))
```

这里一顿操作达到了高级的help_msg效果

每行点击都会在聊天框显示每行的指令

鼠标指向每行时都会显示悬浮的功能说明

```python
c = ['']
for a, b in bot_list.items():
    bot_info = r.RTextList(
        '\n'
        f'§7----------- §6{a}§7 -----------\n',
        f'§7Dimension:§6 {b["dim"]}\n',
        r.RText(
            f'§7Position:§6 {b["pos"]}\n', ).c(
            r.RAction.run_command,
            '[x:{}, y:{}, z:{}, name:{}, dim{}]'.format(
                *[int(i) for i in b['pos']], a, b['dim'])).h(
            '点击显示可识别坐标点'),
        f'§7Facing:§6 {b["facing"]}\n',
        r.RText('§d点击放置\n').c(r.RAction.run_command, f'!!bot spawn {a}').h(f'放置§6{a}'),
        r.RText('§d点击移除\n').c(r.RAction.run_command, f'!!bot kill {a}').h(f'移除§6{a}')
    )
    c.append(bot_info)
server.reply(info, r.RTextList(*c))
```

这里向玩家发送的其实是 `RTextList` 嵌套 `RTextList`

首先创建一个存储bot信息的 `list` ，在最前加个空行用来躲开tweakeroo的时间戳

然后进行机器人信息的遍历，a为机器人名称，b为信息，每次遍历将机器人信息的**RTextList**对象添加到列表

遍历结束之后使用 `server.reply(info, r.RTextList(*c))` 向玩家发送，`*c` 用于将 `list` 变为多个参数

每次遍历的 `RTextList` 知识点：

- 1,2,3,5为 `str`
- 4,6,7为 `RTextList`用于产生点击和悬浮效果