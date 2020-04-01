MCDReforged Plugin Document
---

[中文](https://github.com/Fallen-Breath/MCDReforged/blob/master/doc/plugin_cn.md)

Like MCDaemon, a MCDR plugin is a `.py` file locating in `plugins/` folder. MCDR will automatically load every plugin inside this folder

When the server has trigger specific event, MCDR will call relevant method of each plugin if the plugin has declared the method. MCDR will create a separated thread for the called method to run


| Method | When to call | Reference usage |
|---|---|---|
| on_load(server, old_module) | A plugin gets loaded | The new plugin inherits information from the old plugin |
| on_unload(server) | A plugin gets unloaded | Clean up or turn off functionality of the old plugin |
| on_info(server, info) | A new line is output from the stdout of the server, or a command is input from the console  | Response to the information |
| on_player_joined(server, player) | A player joined the server | Response to the information |
| on_player_left(server, player) | A player left the server | Response to the information |

Note: the plugin doesn't need to implement all methods above. Just implement what you need

Among them, the information of each parameter object is as follows：

## server

This is a object for the plugin to interact with the server. It belongs to the ServerInterface class in `utils/server_interface.py`. It has the following methods:

| Method | Function |
|---|---|
| start() | Start the server. Only works if the server has stopped |
| stop() | Use the specific command like `stop` to close the server. Only works if the server is running |
| execute(text) | Send a string `text` to the stdin of the server with a extra `\n` at the end |
| send(text) | Send a string `text` to the stdin of the server |
| say(text) | Use `tellraw @a` to broadcast message `text` in the server |
| tell(player, text) | Use `tellraw <player>` to send message `text` to player `<player>` |
| wait_for_start() | Wait until the server is stopped, in other words, startable |
| restart() | Execute `stop()`、`wait_for_start()`、`start()` in order to restart the server |
| stop_exit() | Close the server and MCDR, in the other words, exit the program |

## info

This is a parsed information object. It belongs to the Info class in `utils/info.py`. It has the following attributes:


| Attribute | Content |
|---|---|
| hour | A integer，representing the hour when the message was sent. If there isn't it will be `None` |
| min | A integer，representing the minute when the message was sent. If there isn't it will be `None` |
| sec | A integer，representing the second when the message was sent. If there isn't it will be `None` |
| raw_content | An un-parsed raw message string |
| content | If the info is player's chat message, the value is the player's chat content. Otherwise, the value is a string after omitting the prefix information such as time / thread name from the original message string |
| player | If the info is player's chat message, the value is a string representing the player's name, otherwise `None` |
| source | An integer. `0` if the message is from the server's standard output stream;` 1` if it is from the console input |
| is_player | Equivalent to `player != None` |
| is_user | Equivalent to `source == 1 or is_player` |

### Samples

For the following message from the server's standard output：

`[11:10:00 INFO]: Preparing level "world"`

The attributes of the info object are:

| Attribute | Value |
|---|---|
| hour | 11 |
| min | 10 |
| sec | 0 |
| raw_content | `[09:10:00 INFO]: Preparing level "world"` |
| content | `Preparing level "world"` |
| player | None |
| source | 0 |
| is_player | False |
| is_user | False |

------

For the following message from the server's standard output：

`[09:00:00] [Server thread/INFO]: <Steve> Hello`

The attributes of the info object are:

| Attribute | Value |
|---|---|
| hour | 9 |
| min | 0 |
| sec | 0 |
| raw_content | `[09:00:00] [Server thread/INFO]: <Steve> Hello` |
| content | `Hello` |
| player | `Steve` |
| source | 0 |
| is_player | True |
| is_user | True |

### player

This is a string representing the name of the relevant player, such as `Steve`

### old_module

This is an instance of a module, which is used by the new plugin to inherit some necessary information from the old plugin after the plugin is reloaded. If its value is `None`, it means that this is the first time the MCDR has started loading the plugin

Related examples:

```
counter = 0

def on_load(server, old_module):
	global counter
    if old_module is not None:
        counter = old_module.counter + 1
    else:
        counter = 1
    server.say(f'This is the {counter} time to load the plugin')
```

## Porting MCDaemon's plugin to MCDR

1. Modify the code of the old plugin that only works on python2 to be able to run on python3
2. Update the variable / method name to the name of the MCDR, such as changing `onServerInfo` to` on_info` and `isPlayer` to` is_player`
3. MCDR also calls `on_info` when something has input from the console. Pay attention to whether the plugin is compatible with this situation
