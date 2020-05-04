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

## rtext.py

`from utils.rtext import *`

Recommand to read the page [Raw JSON text format](https://minecraft.gamepedia.com/Raw_JSON_text_format) in Minecraft Wiki first

This is an advance text component library for Minecraft

Inspired by the [MCD rtext API](https://github.com/TISUnion/rtext) made by [Pandaria98](https://github.com/Pandaria98)

### RColor

`RColor` stores all Minecraft color codes

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

`RStyle` stores all Minecraft text styles

- `RStyle.bold`
- `RStyle.italic`
- `RStyle.underlined`
- `RStyle.strike_through`
- `RStyle.obfuscated`

### RAction

`RAction` stores all click event actions

- `RAction.suggest_command`
- `RAction.run_command`
- `RAction.open_url`
- `RAction.open_file`
- `RAction.copy_to_clipboard`

### RTextBase

The base class of `RText` and `RTextList`

#### RTextBase.to_json_object()

Return a `dict` representing it's data

#### RTextBase.to_json_str()

Return a json formatted `str` representing it's data. It can be used as the second parameter in command `/tellraw <target> <message>` and more

#### RTextBase.to_plain_text()

Return a plain text for console display. Click event and hover event will be ignored

#### RTextBase.__str__()

Return `RTextBase.to_plain_text()`

#### RTextBase.__add__, RTextBase.__radd__

Return a `RTextList` created by merging two operand

### RText

The text component class

#### RText.RText(text, color=RColor.white, styles=None)

Create a RText object with specific text and color. `styles` can be a `RStyle` or a `list` of `RStyle`

#### Stext.set_click_event(action, value) -> RText

Set the click event to action `action` and value `value`

`action` and `value` are both `str`

Return the RText itself

#### Stext.set_hover_text(*args) -> RText

Set the hover text to `*args`

Parameter `*args` will be used to create a `RTextList` instance. For the restrictions check the constructor of `RTextList` below

Return the RText itself

### RTextList

It's a list of RText

When converted to json object for displaying to the game it will at a extar empty string at the front to prevent the first object's style affecting the later ones

### RTextList.RTextList(*args)

Objects in `*args` can be a `str`, a `RText`, a `RTextList` or any classes implemented `__str__` method. All of them will be convert to `RText`

---------

`RTextBase` objects can be used as the message parameter in plugin APIs as below:

- `server.tell`
- `server.say`
- `server.reply`
- `add_help_message`

Special judge for console output is unnecessary since `server.reply` etc. will convert `RTextBase` objects into plain text
