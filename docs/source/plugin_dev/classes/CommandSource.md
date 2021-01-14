# CommandSource

CommandSource is command executor model abstracted from a user-type Info instance. It provides several methods for command execution

Inherited from the class CommandSource, there are 2 subclasses, PlayerCommandSource and ConsoleCommandSource, which are used to implement methods dedicatedly

## Property

### source_type

If the source is a player command source, its value is `0`

If the source is a console command source, its value is `1`

Type: int

### is_player

An `@property` decorated method

If the command source is a player command source

Type: bool

### is_console

An `@property` decorated method

If the command source is a console command source

Type: bool

## Method

### get_server

```python
def get_server(self) -> ServerInterface
```

Return the server interface instance

### get_info

```python
def get_info(self) -> Info
```

Return the Info instance that this command source is created from

### get_permission_level

```python
def get_permission_level(self) -> int
```

Return the permission level representing by an int that the command source has

### has_permission

```python
def has_permission(self, level: int) -> bool:
    return self.get_permission_level() >= level
```

Return if the command source has not less level than the given permission level

### has_permission_higher_than

```python
def has_permission_higher_than(self, level: int) -> bool:
    return self.get_permission_level() > level
```

Just like the [has_permission](#has-permission), but this time it is a greater than judgment

### reply

```python
def reply(self, message: Any, **kwargs) -> None
```

Send a message to the command source. The message can be anything including RTexts

The message will be converted to str using `str()` function unless it's a RTextBase object

Keyword Parameter *encoding*: The encoding method for the text. It's only used in PlayerCommandSource to optionally specify the encoding method. Check [here](ServerInterface.html#execute) for more details
