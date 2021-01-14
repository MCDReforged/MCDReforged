# API Packages for Plugins

When your plugin needs to import something from MCDR, rather than directly import the package you want, you can import the packages in `mcdreforged.api`

`mcdreforged.api` is the package for plugin developers to import. By only importing from the api package, the import of the target class in the plugin can be decoupled from the actual location of the target class. If MCDR refactors the target class and moves its location in the future, only importing from the api package can keep your plugin unaffected

## all

```python
from mcdreforged.api.all import *
```

This is the simplest way to import everything you want for plugin development. It's a life saver for lazy man

Continue reading to see what it will actually import

## command

`command` package contains the necessities for building a command tree or create your own command, including command tree node classes, command exceptions and some command utils

For example, if you want the class `Literal` and `IllegalArgument` for building your command tree `on_error` exception handling, you can do it like this

```python
from mcdreforged.api.command import Literal, IllegalArgument
```

Of course if you are lazy enough you can just

```python
from mcdreforged.api.command import *
```

## decorator

`decorator` package contains some useful function decorators for plugin development

### new_thread

This is a one line solution to make your function executes asynchronously. When decorated with this decorator, functions will be executed in a new daemon thread

This decorator only changes the return value of the function to the created `Thread` instance. Beside the return value, it reserves all signatures of the decorated function, so you can safely use the decorated function as if there's no decorating at all

It's also a simple compatible upgrade method for old MCDR 0.x plugins

Example:

```python
from mcdreforged.api.decorator import new_thread

def do_something1(text: str):
    print(text)
    time.sleep(5)
    return text

@new_thread
def do_something2(text: str):
    print(text)
    time.sleep(5)
    return text

def on_info(server, info):
    # do_something1('hello')
    do_something2('there')
```

The only difference between `do_something1` and `do_something2` is that `do_something2` is decorated by `@new_thread`. So when executing `do_something2`, it won't lag the following execution of MCDR like `do_something1` since `do_something2` will execute on another thread

If you want to wait for the decorated function to complete, you can simple use the `join` method from class `threading.Thread`. Remember the return value of the decorated function has already been changed in to the `Thread` instance

```python
do_something2('task').join()
```

In addition to simply and directly use a raw `@new_thread`, it's recommend to add a thread name argument for the decorator

```python
@new_thread('My Plugin Thread')
def do_something3(text: str):
    print(threading.current_thread().getName())  # will be "My Plugin Thread"
    time.sleep(10)
```

So when you logs something by `server.logger`, a meaningful thread name will be displayed instead of a plain and meaningless `Thread-3`

**Notes**: Some api methods in `ServerInterface` class are required to be invoked in the MCDR task executor thread. Invoking them in another thread might result in an exception

## event

`event` package contains the classes for creating custom events, and classes of MCDR built-in events

You might already read the [dispatch_event](classes/ServerInterface.html#dispatch-event) method in `ServerInterface` class. It only accepts a `PluginEvent` instance as its first parameter. So if you want to dispatch your custom event, create a `LiteralEvent` for simpleness or a custom event class inherited from `PluginEvent`

## rcon

Package `rcon` contains a single class `RconConnection`. It's is a simply rcon client for connect to any Minecraft servers that supports rcon protocol

### RconConnection

#### RconConnection

```python
def __init__(self, address: str, port: int, password: str, *, logger: Optional[Logger] = None)
```

Create a rcon client instance

Parameter *address*: The address of the rcon server

Parameter *port*: The port if the rcon server

Parameter *password*: The password of the rcon connection

Keyword Parameter *logger*: An instance of `logging.Logger`. It's used to output some warning information like failing to receive a packet

#### connect

```python
def connect(self) -> bool
```

Start a connection to the rcon server and tries to login. If login success it will return `True`, otherwise `False`

#### disconnect

```python
def disconnect(self)
```

Disconnect from the server

#### send_command

```python
def send_command(self, command: str, max_retry_time: int = 3) -> Optional[str]
```

Send  command to the rcon server, and return the command execution result form the server

Parameter *command*: The command you want to send to the server

Parameter *max_retry_time*: The maximum retry time of the operation. This method will return None if *max_retry_time* retries exceeded  

## rtext

Recommend to read the page [Raw JSON text format](https://minecraft.gamepedia.com/Raw_JSON_text_format) in Minecraft Wiki first

This is an advance text component library for Minecraft

Inspired by the [MCD stext API](https://github.com/TISUnion/rtext) made by [Pandaria98](https://github.com/Pandaria98)

### RColor

`RColor` is an enum class storing all Minecraft color codes

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
- `RColor.reset`

### RStyle

`RStyle` is an enum class storing all Minecraft text styles

- `RStyle.bold`
- `RStyle.italic`
- `RStyle.underlined`
- `RStyle.strike_through`
- `RStyle.obfuscated`

### RAction

`RAction` is a enum class storing all click event actions

- `RAction.suggest_command`
- `RAction.run_command`
- `RAction.open_url`
- `RAction.open_file`
- `RAction.copy_to_clipboard`

### RTextBase

`RTextBase` is an abstract class of text component. It's the base class of `RText` and `RTextList`

#### to_json_object

```python
def to_json_object(self)
```

Abstract method

Return an object representing it's data that can be serialized into json string

#### to_json_str

```python
def to_json_str(self) -> str
```

Return a json formatted str representing it's data. It can be used as the second parameter in command `/tellraw <target> <message>` and more

#### to_plain_text

```python
def to_plain_text(self) -> str
```

Abstract method

Return a plain text for console display. Click event and hover event will be ignored

#### copy

```python
def copy(self) -> RTextBase
```

Abstract method

Return a copy version of itself

#### set_color

```python
def set_color(self, color: RColor) -> RTextBase
```

Abstract method

Set the color of the text and return the text component itself

#### set_styles

```python
def set_styles(self, styles: Union[RStyle, Iterable[RStyle]]) -> RTextBase
```

Abstract method

Set the styles of the text and return the text component itself

#### set_click_event

```python
def set_click_event(self, action: RAction, value: str) -> RTextBase
```

Set the click event with given *action* and *value* and return the text component itself

Parameter *action*: The type of the action

Parameter *value*: The string value of the action

Method `c` is the short form of method `set_click_event`

#### set_hover_text

```python
def set_hover_text(self, *args) -> RTextBase
```

Set the hover text with given *\*args* and return the text component itself

Parameter *action*: The elements be used to create a `RTextList` instance. The `RTextList` instance is used as the actual hover text

Method `h` is the short form of method `set_hover_text`

### RText

The regular text component class

#### RText

```python
def __init__(self, text, color: Optional[RColor] = None, styles: Optional[Union[RStyle, Iterable[RStyle]]] = None)
```

Create an `RText` object with specific text, color and style. `styles` can be a `RStyle` or a collection of `RStyle`

### RTextTranslation

The translation text component class. It's almost the same as `RText`

#### RTextTranslation

```python
def __init__(self, translation_key, color: RColor = RColor.reset, styles: Optional[Union[RStyle, Iterable[RStyle]]] = None)
```

Create a RTextTranslation object with specific translation_key. The rest of the parameters are the same to `RText`

Example: `RTextTranslation('advancements.nether.root.title', color=RColor.red)`

### RTextList

A list of RTextBase objects 

#### RTextList

```python
def __init__(self, *args)
```

Use the given *\*args* to create a `RTextList`

Objects in `*args` can be a `str`, a `RTextBase` or any classes implemented `__str__` method. All of them will be convert to `RText`

#### append

```python
def append(self, *args) -> RTextList
```

Add several elements to the end of the current `RTextList`, then return the `RTextList` component itself

Objects in `*args` can be a `str`, a `RTextBase` or any classes implemented `__str__` method. All of them will be convert to `RText`

#### is_empty

```python
def is_empty(self) -> bool
```

Return a bool indicating if the `RTextList` is empty. In other words, has no child element

## types

Who doesn't want a complete type checking to help you reduce silly mistakes etc. when coding your plugin? If you want to add type hints to the server interface or command source parameter, here's the package for you to import those Usually-used classes

```python
from mcdreforged.api.types import ServerInterface, Info

def on_info(server: ServerInterface, info: Info):
    # Now auto completion for server and info parameters should be available for IDE
    pass
```
