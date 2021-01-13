# ServerInterface

ServerInterface is the interface for plugins to interact with the server. The first argument in all plugin events is always the ServerInterface. It's recommend to use `server` as the parameter name of the ServerInterface argument which is widely used in this document

You can check the code to see the implementation for deeper understanding

## Property

### logger

A logger for logging message to the console

Type: MCDReforgedLogger, which is inherited from `logging.Logger`

## Method

Methods in the SererInterface object are also the API interface for plugins to control the server and the MCDR

### Server Control

#### start

```python
def start(self) -> bool
```

Start the server. Return if the action succeed.

If the server is running or being starting by other plugin it will return `False`

#### stop

```python
def stop(self) -> None
```

Soft shutting down the server by sending the correct stop command to the server

This option will not stop MCDR

#### wait_for_start

```python
def wait_for_start(self) -> None
```

Wait until the server is able to start. In other words, wait until the server is stopped

#### restart

```python
def restart(self) -> None
```

Restart the server

It will first soft stop the server and then wait until the server is stopped, then start the server up

#### stop_exit

```python
def stop_exit(self) -> None
```

Soft stop the server and exit MCDR

#### exit

```python
def exit(self) -> None
```

Exit MCDR when the server is stopped

If the server is running return False otherwise return True

#### is_server_running

```python
def is_server_running(self) -> bool
```

Return if the server is running

#### is_server_startup

```python
def is_server_startup(self) -> bool
```

Return if the server has started up

#### is_rcon_running

```python
def is_rcon_running(self) -> bool
```

Return if MCDR's rcon is running

#### get_server_pid

```python
def get_server_pid(self) -> Optional[int]
```

Return the pid of the server process, None if the server is stopped

Notes the process with this pid is a bash process, which is the parent process of real server process you might be interested in

### Text Interaction

#### execute

```python
def execute(self, text: str, *, encoding: Optional[str] = None) -> None
```

Execute a command by sending the command content to server's standard input stream

Parameter *text*: The content of the command you want to send

Parameter *encoding*: The encoding method for the text. Leave it empty to use the encoding method from the configure of MCDR

#### tell

```python
def tell(self, player: str, text: Union[str, RTextBase], *, encoding: Optional[str] = None) -> None
```

Use command like `/tellraw` to send the message to the specific player

Parameter *player*: The name of the player you want to tell

Parameter *text*: the message you want to send to the player

Parameter *encoding*: The encoding method for the text. Leave it empty to use the encoding method from the configure of MCDR

#### say

```python
def say(self, text: Union[str, RTextBase], *, encoding: Optional[str] = None) -> None
```

Use command like `/tellraw @a` to send the message to broadcast the message in game

Parameter *text*: the message you want to send

Parameter *encoding*: The encoding method for the text. Leave it empty to use the encoding method from the configure of MCDR

#### broadcast

```python
def broadcast(self, text: Union[str, RTextBase], *, encoding: Optional[str] = None) -> None
```

Broadcast the message in game and to the console

Parameter *text*: the message you want to send

Parameter *encoding*: The encoding method for the text. Leave it empty to use the encoding method from the configure of MCDR

#### reply

```python
def reply(self, info: Info, text: Union[str, RTextBase], *, encoding: Optional[str] = None, console_text: Optional[Union[str, RTextBase]] = None)
```

Reply to the source of the Info

If the Info is from a player then use tell to reply the player, otherwise if the Info is from the console use logger.info to output to the console. In the rest of the situations, the Info is not from a user, a IllegalCallError is raised

Parameter *info*: the Info you want to reply to

Parameter *text*: the message you want to send

Parameter *console_text*: If it's specified, console_text will be used instead of text when replying to console

Parameter *encoding*: The encoding method for the text

### Plugin Operations

**Notes**: All plugin manipulation will trigger a dependency check, which might cause unwanted plugin operations

#### load_plugin

```python
def load_plugin(self, plugin_file_path: str) -> bool
```

Load a plugin from the given file path. Return if the plugin gets loaded successfully

Parameter *plugin_file_path*: The file path of the plugin to load. Example: `plugins/my_plugin.py`

#### load_plugin

```python
def enable_plugin(self, plugin_file_path: str) -> bool
```

Enable an unloaded plugin from the given path. Return if the plugin gets enabled successfully

Parameter *plugin_file_path*: The file path of the plugin to enable. Example: "plugins/my_plugin.py.disabled"

#### reload_plugin

```python
def reload_plugin(self, plugin_id: str) -> Optional[bool]
```

Reload a plugin specified by plugin id. Return a bool indicating if the plugin gets reloaded successfully, or None if plugin not found

Parameter *plugin_id*: The id of the plugin to reload. Example: "my_plugin"

#### unload_plugin

```python
def unload_plugin(self, plugin_id: str) -> Optional[bool]
```

Unload a plugin specified by plugin id. Return a bool indicating if the plugin gets unloaded successfully, or None if plugin not found

Parameter *plugin_id*: The id of the plugin to unload. Example: "my_plugin"

#### disable_plugin

```python
def disable_plugin(self, plugin_id: str) -> Optional[bool]
```

Disable a plugin specified by plugin id. Return a bool indicating if the plugin gets disabled successfully, or None if plugin not found

Parameter *plugin_id*: The id of the plugin to disable. Example: "my_plugin"

#### refresh_all_plugins

```python
def refresh_all_plugins(self) -> None
```

Reload all plugins, load all new plugins and then unload all removed plugins

#### refresh_changed_plugins

```python
def refresh_all_plugins(self) -> None
```

Reload all changed plugins, load all new plugins and then unload all removed plugins

#### get_plugin_list

```python
def get_plugin_list(self) -> List[str]
```

Return a list containing all loaded plugin id like ["my_plugin", "another_plugin"]

#### get_plugin_metadata

```python
def get_plugin_list(self) -> Optional[Metadata]
```

Return the metadata of the specified plugin, or None if the plugin doesn't exist

Parameter *plugin_id*: The plugin id of the plugin to query metadata

#### get_plugin_file_path

```python
def get_plugin_list(self) -> Optional[str]
```

Return the file path of the specified plugin, or None if the plugin doesn't exist

Parameter *plugin_id*: The plugin id of the plugin to query file path

#### get_plugin_instance

```python
def get_plugin_instance(self) -> Optional[Any]
```

Return the current loaded plugin instance, or None if the plugin doesn't exist. With this api your plugin can access the same plugin instance to MCDR

It's quite important to use this instead of manually import the plugin you want if the target plugin needs to react to events from MCDR

Parameter *plugin_id*: The plugin id of the plugin you want

Example: 

```python
# My API plugin with id my_api
def info_query_api(item):
    pass
```

```python
# Another plugin that needs My API
server.get_plugin_instance('my_api').info_query_api(an_item)
```

### Plugin Registry

#### register_event_listener

```python
def register_event_listener(self, event: Union[PluginEvent, str], callback: Callable, priority: int = 1000) -> None
```

Register an event listener for the current plugin

Raise an `IllegalCallError` if it's not invoked in the task executor thread

Parameter *event*: The id of the event to listen, or the PluginEvent instance

Parameter *callback*: The callback listener method for the event

Parameter *priority*: The priority of the listener. It will be set to the default value 1000 if it's not specified

#### register_command

```python
def register_command(self, root_node: Literal) -> None
```

Register an event listener for the current plugin

Raise an `IllegalCallError` if it's not invoked in the task executor thread

Parameter *root_node*: The root node of your command tree. It should be a `Literal` node

#### register_help_message

```python
def register_help_message(self, prefix: str, message: Union[str, RTextBase], permission: int = PermissionLevel.MINIMUM_LEVEL) -> None
```
Register a help message for the current plugin, which is used in !!help command

Raise an `IllegalCallError` if it's not invoked in the task executor thread

Parameter *prefix*: The help command of your plugin. When player click on the displayed message it will suggest this prefix parameter to the player. It's recommend to set it to the entry command of your plugin

Parameter *message*: A neat command description

Parameter *permission*: The minimum permission level for the user to see this help message. With default, anyone can see this message

#### dispatch_event

```python
def dispatch_event(self, event: PluginEvent, args: Tuple[Any, ...]) -> None
```

Dispatch an event to all loaded plugins

The event will be immediately dispatch if it's on the task executor thread, or gets enqueued if it's on other thread

Parameter *event*: The event to dispatch. It need to be a `PluginEvent` instance. For simple usage, you can create a `LiteralEvent` instance for this argument

Parameter *args*: The argument that will be used to invoke the event listeners. An ServerInterface instance will be automatically added to the beginning of the argument list

### Permission

#### get_permission_level

```python
def get_permission_level(self, obj: Union[str, Info, CommandSource]) -> int
```

Return an int indicating permission level number the given object has

The object could be a str indicating the name of a player, an Info instance or a command source

Parameter *obj*: The object your are querying

It raises `TypeError` if the type of the given object is not supported for permission querying

#### set_permission_level

```python
def set_permission_level(self, player: str, value: Union[int, str]) -> None
```

Set the permission level of the given player. It raises `TypeError` if the value parameter doesn't proper represent a permission level

Parameter *player*: The name of the player that you want to set his/her permission level

Parameter *value*: The target permission level you want to set the player to. It can be an int or a str as long as it's related to the permission level. Available examples: 1, '1', 'user'

### Misc

#### is_on_executor_thread

```python
def is_on_executor_thread(self) -> bool
```

Return if the current thread is the task executor thread

Task executor thread is the main thread to parse messages and trigger listeners where some ServerInterface APIs  are required to be invoked on

#### rcon_query

```python
def rcon_query(self, command: str) -> Optional[str]
```

Send command to the server through rcon connection. Return the result that server returned from rcon. Return None if rcon is not running or rcon query failed

Parameter *command*: The command you want to send to the rcon server
