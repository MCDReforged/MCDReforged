# rtext使用文档

## 准备

导入: `from utils.rtext import *`

下文所有使用RText的地方不再使用前缀，自己使用时可根据需要 import

推荐阅读 Minecraft Wiki 中关于 [原始JSON文本格式](https://minecraft-zh.gamepedia.com/%E5%8E%9F%E5%A7%8BJSON%E6%96%87%E6%9C%AC%E6%A0%BC%E5%BC%8F) 的页面

这是一个 Minecraft 高级文本容器库

受 [Pandaria98](https://github.com/Pandaria98) 制作的 [MCD stext API](https://github.com/TISUnion/rtext) 启发

---------

以下三个类需要作为参数在`RText`中使用

## RColor

`RColor` 类储存着 Minecraft 的所有颜色代码

| 代码 | 官方名称 | Rcolor代码 |
| - | - | - |
| §0 | black | RColor.black |
| §1 | dark_blue | RColor.dark_blue |
| §2 | dark_green | RColor.dark_green |
| §3 | dark_aqua | RColor.dark_aqua |
| §4 | dark_red | RColor.dark_red |
| §5 | dark_purple | RColor.dark_purple |
| §6 | gold | RColor.gold |
| §7 | gray | RColor.gray |
| §8 | dark_gray | RColor.dark_gray |
| §9 | blue | RColor.blue |
| §a | green | RColor.green |
| §b | aqua | RColor.aqua |
| §c | red | RColor.red |
| §d | light_purple | RColor.light_purple |
| §e | yellow | RColor.yellow |
| §f | white | RColor.white |

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
| 复制到剪贴板 | copy_to_clipboard | RAction.copy_to_clipboard |

---------

以下为编写插件时真正需要的类

## RText类

该类的实例化：

```python
RText(text, color=RColor.reset, styles=None)
```

`text` 接受可以实现 `str()` 方法的对象或RText

`color` 接受颜色名的str，可以使用[RColor](#RColor)的属性

`styles` 接受样式名的str或多个的list，可以使用[RStyle](#RStyle)的属性

例子：

```python
RText('这是例子', color=RColor.blue, styles=None)
```

效果：

- 消息为有下划线的蓝色文字 `这是例子`

---------

该类拥有以下方法:

### set_insertion(text)

设置 shift + 鼠标点击时添加到聊天框的内容

`text` 接受str

例子：

```python
RText('这里有密码').set_insertion('2468')
```

效果：

- 消息为 `这里有密码`
- shift + 点击后在聊天栏追加文本 `2468`

### set_click_event(action, value)

设置一个动作为 `action`，值为 `value`的点击事件

`action` 接受动作名的str，可以使用[RAction](#RAction)的属性

`value` 接受执行动作的参数的str

例子：

```python
RText('点我去主城').set_click_event(RAction.run_command, '/server lobby')
```

效果：

- 消息为 `点我去主城`
- 点击后执行 `/server lobby`

注：该类的方法 `c(action, value)` 会调用 `set_click_event(action, value)`，两种方法效果完全相同，使用时可按需调用

### set_hover_text(*args)

用于设置鼠标指向时，显示的悬浮文本

`*args` 将会用于创建一个 [RTextList](#RTextList类) 对象

例子：

```python
RText('§a欢迎新玩家加入服务器，点击欢迎').set_hover_text(RText('§7点击欢迎新人')).c(RAction.run_command, '欢迎新人')
```

效果：

- 消息为绿色的 `欢迎新玩家加入服务器，点击欢迎`
- 鼠标指向时显示灰色的 `点击欢迎新人`
- 点击后发送 `欢迎新人`

注：该类的方法 `h(*args)` 会调用 `set_hover_text(*args)`，两种方法效果完全相同，使用时可按需调用

### set_hover_item(data)

用于设置鼠标指向时，显示的悬浮物品

`data` 为一个 [物品通用标签](https://minecraft-zh.gamepedia.com/Player.dat%E6%A0%BC%E5%BC%8F#.E7.89.A9.E5.93.81.E7.BB.93.E6.9E.84)

例子：

```python
RText('展示物品').set_hover_item('{id:"minecraft:wooden_axe",Count:1b,tag:{Damage:1}}')
```

效果：

- 消息为白色的 `展示物品`
- 鼠标指向时显示 `木斧`，耐久缺少1

注：不可使用 `h(*args)`

## RTextList类

该类的实例化：

```python
RTextList(*args)
```

`*args` 接受可以实现 `str()` 方法的对象或RText或RTextList

---------

该类拥有以下方法:

### append(*args)

向已经实例化的RTextList对象添加文本

`*args` 接受可以实现 `str()` 方法的对象或RText或RTextList

---------

## 提示

- `RText` 和 `RTextList` 的对象可以被当做 `message` 参数在以下方法中使用: `server.tell`，`server.say`，`server.reply`，`add_help_message`

- 使用时别操心输出到控制台还是游戏内

---------

## 插件实例分析

### [QuickBackupM](https://github.com/TISUnion/QuickBackupM)

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

### [BotInit](https://github.com/MCDReforged-Plugins/BotInit)

```python
server.add_help_message('!!bot', RText('显示机器人列表').c(RAction.run_command, '!!bot').h('点击显示机器人列表'))
```

这里使用RText作为add_help_message第二个参数

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
c = [RText(f'{a} {b}\n').c(RAction.suggest_command, a.replace('§6', '')).h(b) for a, b in help_msg.items()]
server.reply(info, RTextList(*c))
```

这是一个高级help_msg的应用

每行点击时都会在聊天框显示每行的指令

鼠标指向每行时都会显示悬浮的功能说明

```python
c = ['']
for a, b in bot_list.items():
    bot_info = RTextList(
        '\n'
        f'§7----------- §6{a}§7 -----------\n',
        f'§7Dimension:§6 {b["dim"]}\n',
        RText(f'§7Position:§6 {b["pos"]}\n').c(RAction.run_command, '[x:{}, y:{}, z:{}, name:{}, dim{}]'.format(*[int(i) for i in b['pos']], a, b['dim'])).h('点击显示可识别坐标点'),
        f'§7Facing:§6 {b["facing"]}\n',
        RText('§d点击放置\n').c(RAction.run_command, f'!!bot spawn {a}').h(f'放置§6{a}'),
        RText('§d点击移除\n').c(RAction.run_command, f'!!bot kill {a}').h(f'移除§6{a}')
    )
    c.append(bot_info)
server.reply(info, RTextList(*c))
```

这里向玩家发送的是 `RTextList` 嵌套 str，RText和RTextList

首先创建一个存储bot信息的 `list` ，在最前加个空行用来避免tweakeroo的时间戳显示影响效果

然后进行机器人信息的遍历，a为机器人名称，b为信息，每次遍历将机器人信息的各项内容组成的RTextList添加到列表

遍历结束之后使用 `server.reply(info, RTextList(*c))` 向玩家发送，`*c` 用于将 `list` 变为多个参数
