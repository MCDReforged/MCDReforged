MCDReforged Utils Document
---

## rcon.py

`from utils.rcon import Rcon`

This is a simply rcon client

### Rcon.Rcon(address, port, password, logger=None)

Create a rcon client instance

`address` is a `str`, the address of the rcon server

`port` is an `int`, the port if the rcon server

`password` is a `str`, the password of the rcon connection

(Optional) `logger` is an instance of `logging.Logger`. It's used to output some warning information

### Rcon.connect() -> bool

Start a connection to the rcon server and tries to login. If login success it will return `True`, otherwise `False`

### Rcon.disconnect()

Disconnect from the server

### Rcon.send_command(command, max_retry_time=3) -> str

Send a `str` command `command` to the rcon server

Return a `str`, the command execution result form the server

`max_retry_time` is the maximum retry time of the operation. This method will return `None` if it's exceeded  

## stext.py

`from utils.stext import *`

Recommand to read the page [Raw JSON text format](https://minecraft.gamepedia.com/Raw_JSON_text_format) in Minecraft Wiki first

This is an advance text component library for Minecraft

Inspired by the [MCD stext API](https://github.com/TISUnion/stext) made by [Pandaria98](https://github.com/Pandaria98)

### SColor

`SColor` stores all Minecraft color codes

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

`SStyle` stores all Minecraft text styles

- `SStyle.bold`
- `SStyle.italic`
- `SStyle.underlined`
- `SStyle.strike_through`
- `SStyle.obfuscated`

### SAction

`SAction` stores all click event actions

- `SAction.suggest_command`
- `SAction.run_command`
- `SAction.open_url`
- `SAction.open_file`
- `SAction.copy_to_clipboard`

### STextBase

The base class of `SText` and `STextList`

#### STextBase.to_json_object()

Return a `dict` representing it's data

#### STextBase.to_json_str()

Return a json formatted `str` representing it's data. It can be used as the second parameter in command `/tellraw <target> <message>` and more

#### STextBase.to_plain_text()

Return a plain text for console display. Click event and hover event will be ignored

#### STextBase.__str__()

Return `STextBase.to_plain_text()`

#### STextBase.__add__, STextBase.__radd__

Return a `STextList` created by merging two operand

### SText

The text component class

#### SText.SText(text, color=SColor.white, styles=None)

Create a SText object with specific text and color. `styles` can be a `SStyle` or a `list` of `SStyle`

#### Stext.set_click_event(action, value) -> SText

Set the click event to action `action` and value `value`

`action` and `value` are both `str`

Return the SText itself

#### Stext.set_hover_event(*args) -> SText

Set the hover text to `*args`

Parameter `*args` will be used to create a `STextList` instance. For the restrictions check the constructor of `STextList` below

Return the SText itself

### STextList

It's a list of SText

### STextList.STextList(*args)

Objects in `*args` can be a `str`, a `SText`, a `STextList` or any classes implemented `__str__` method. All of them will be convert to `SText`

---------

`STextBase` objects can be used as the message parameter in plugin APIs as below:

- `server.tell`
- `server.say`
- `server.reply`
- `add_help_message`

Special judge for console output is unnecessary since `server.reply` etc. will convert `STextBase` objects into plain text
