# rtext Tutorials

## First to do

import: `from utils import rtext`

Read the page about [Raw JSON text format](https://minecraft.gamepedia.com/Raw_JSON_text_format)  on Minecraft Wiki is recommanded before you doing this.

rtext is an advanced Minecraft text container

Inspired by [MCD stext API](https://github.com/TISUnion/rtext) by [Pandaria98](https://github.com/Pandaria98)

---

The following classes need to be used in `RText` as parameters

## Rcolor

`Rcolor` class contains all Minecraft color code in it.

| Code | Official Name | Rcolor Code |
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

`RStyle` class contains all Minecraft text style code in it.

| Code | Official Name | Rstyle Code |
| - | - | - |
| §k | obfuscated | RStyle.obfuscated |
| §l | bold | RStyle.bold |
| §m | strike_through | RStyle.strike_through |
| §n | underlined | RStyle.underlined |
| §o | italic | RStyle.italic |

## RAction

`RAction` class contains all Minecraft click event in it.

| Event | Official Name | RAction Code |
| - | - | - |
| Overwrite content in chatting box | suggest_command | RAction.suggest_command |
| Run command | run_command | RAction.run_command |
| Open link | open_url | RAction.open_url |
| Open file | open_file | RAction.open_file |
| Copy to clipboard | copy_to_clipboard | RAction.copy_to_clipboard |

---

Here are the classes you really need to write your plugin

## Rtext

Initialize Rtext:

```python
RText(text, color=RColor.white, styles=None)
```

`text` is an object can be use `str()` function or a Rtext object

`styles` is a `RStyle` object or a `list` contains objects.

For example:

```python
RText('This is an example', color=RColor.blue, styles=None)
```

Result:

- A message in blue with underline output `This is an example`

---

This class has the following methods:

### set_click_event(action, value)

set the click event to `action`, value to `value`

`action` can be a `RAction.action` or an official action in type `str`

`value` is the action parameter in type `str`

For example:

```python
RText('Lobby').set_click_event(RAction.run_command, '/server lobby')
```

Result:

- Message is `Lobby`
- When you click it, it'll execute `/server lobby`

Tips: You can use `c(action, value)` instead of `set_click_event(action, value)`

### set_hover_text(\*args)

The floating text displayed when your mouse floating at the text

If you don't know `*arg` you need to read this https://book.pythontips.com/en/latest/args_and_kwargs.html

`*arg` will be used to Initialize [RTextList](#RTextList)

For example:

```python
RText('§aWelcome new player! Click to welcome!').set_hover_text(r.RText('§7Click me to welcome')).c(r.RAction.run_command, 'Welcome new friend!')`
```

Result:

- Message with text `Welcome new player! Click to welcome!` in green
- Display `Click me to welcome` in gray when your mouse floating at the message
- Send `Welcome new friend!` when you click it

Tip: You can use `h(*args)` instead of `set_hover_text(*args)`

## RTextList

Initialize RTextList:

```python
RTextList(*args)
```

You can use every parameter which can be convert to `RText` to deliver to `RTextList`

### Tips:

- `RText` and `RTextList` objects can be used as `message` in the following methods: `server.tell`, `server.say`, `server.reply`, `add_help_message`
- Don't worry about the output goes into console or in-game

---

## Example Analysis

### [QuickBackupM](https://github.com/TISUnion/QuickBackupM)

```python
from utils.rtext import *
```

```python
def command_run(message, text, command):
    return RText(message).set_hover_text(text).set_click_event(RAction.run_command, command)
```

Define a function with display text and command

Use the function when floating text and click event are needed at the same time

```python
except Exception as e:
	print_message(server, info, RText('§Delete fail§r, check console for more detail').set_hover_text(e), tell=False)
```

Here place a floating text to make players can see the error message in game

### [BotInit](https://github.com/MCDReforged-Plugins/BotInit/blob/master/BotInit.py)

Due to this plugin doesn't have the English version, the message inside still using Chinese

```python
from utils import rtext as r
```

```python
server.add_help_message('!!bot', r.RText('显示机器人列表').c(r.RAction.run_command, '!!bot').h('点击显示机器人列表'))
```

Use Rtext to be the message part of add_help_message

`.h` displayer `点击显示机器人列表` when player's mouse pointing at this help message

`.c` make player say `!!bot` when clicking at the message


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

This kind of code is an advanced writing method

It'll overwrite the chatting box with the command of which line player clicked

When player's mouse point at the line, every line will have its own help message with floating texts

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

Actually, the code here send a `RTextList` with `RTextList` in it

First create a `list` with information of all bots, use wrap to prevent the timestamp of tweakeroo's interference

Then start a traverse of bots' information, a is the name of the bot, b is the information, every bot's information in **RTextList** will be added to a list

After finishing the traverse, use `server.reply(info, r.RTextList(*c))` to send the result to player, `*c` will be used to devide the `list` into lots of parameters

The knowledge of `RTextList`'s Traverse:

- 1,2,3,5 are `str`
- 4,6,7 are the `RTextList` to produce click event and floating texts