# Info

An Info instance contains the parsed result from the server or from the console. 

## Property

Property might be None if MCDR didn't parse out the related property

### id

A increasing id number for distinguishing info instance. The id is monotonously rising by time

Type: int

### hour, min, sec

Time information from the parsed text

Type: int

### raw_content

Very raw unparsed content from the server stdout. It's also the content to be echoed to the stdout

Type: str

### content

The parsed message text. If the text is sent by a player it will be what the player said

Type: str

### player

The name of the player. If it's not sent by a player the value will be None

Type: str

### source

A int representing the the type of the info

For info from the server, its value is `0`

For info from the console, its value is `1`

Type: int

### logging_level

The logging level of the server's stdout, such as `INFO` or `WARN`

Type: str

### is_from_console

An `@property` decorated method

If the source of the info is `1`, aka from the console

Type: bool

### is_from_server

An `@property` decorated method

If the source of the info is `0`, aka from the server

Type: bool

### is_player

An `@property` decorated method

If the source is from a player in the server

Type: bool

### is_user

An `@property` decorated method

If the source is from a user, in other words, if the source is from the console or from a player in the server

Type: bool

## Method

### get_server

```python
def get_server(self) -> ServerInterface
```

Return the server interface instance

### get_command_source

```
def get_command_source(self) -> Optional[CommandSource]
```

Extract an command source object from this info instance. ConsoleCommandSource if this info is from console, or PlayerCommandSource if this info is from a player in game

Return the command source instance, or None if it can't extract a command source

### to_command_source

```
def to_command_source(self) -> CommandSource
```

The same to method `get_command_source`, but it raises a `IllegalCallError` if it can't extract a command source

### should_send_to_server

```
def should_send_to_server(self) -> bool
```

Representing if MCDR should send the content to the standard input stream of the server if this info is input from the console

### cancel_send_to_server

```
def cancel_send_to_server(self) -> None
```

Prevent this info from being sent to the standard input stream of the server
