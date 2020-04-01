MCDReforged Plugin Document
---

[English](https://github.com/Fallen-Breath/MCDReforged/blob/master/doc/plugin.md)

与 MCDaemon 类似，一个 MCDR 的插件是一个位与 `plugins/` 文件夹下的 `.py` 文件。MCDR 会在启动时自动加载该文件夹中的所有插件

当服务器触发某些指定事件时，如果插件有声明下列方法的话，MCDR 会调用每个插件的对应方法。MCDR 调用每个插件的方法时会为其新建一个独立的线程供其运行

| 方法 | 调用时刻 | 参考用途 |
|---|---|---|
| on_load(server, old_module) | 插件被加载 | 新插件继承旧插件的信息 |
| on_unload(server) | 插件被卸载 | 清理或关闭旧插件的功能 |
| on_info(server, info) | 服务器的标准输出流有输出，或者控制台有输入 | 插件响应相关信息 |
| on_player_joined(server, player) | 玩家加入服务器 | 插件响应相关信息 |
| on_player_left(server, player) | 玩家离开服务器 | 插件响应相关信息 |

注：每个插件并不需要实现所有上述方法，按需实现即可

其中，各个参数对象的信息如下：

## server

这是用于插件与服务端进行交互的对象，属于 `utils/server_interface.py` 中的 ServerInterface 类。它具有以下方法：

| 方法 | 功能 |
|---|---|
| start() | 启动服务器。仅在服务器未启动的情况下有效 |
| stop() | 使用服务端对应的指令，如 `stop` 来关闭服务器。仅在服务器运行时有效 |
| execute(text) | 发送字符串 `text` 至服务端的标准输入流，并自动在其后方追加一个 `\n` |
| send(text) | 发送字符串 `text` 至服务端的标准输入流 |
| say(text) | 使用 `tellraw @a` 来在服务器中广播字符串消息 `text` |
| tell(player, text) | 使用 `tellraw <player>` 来在对玩家 `<player>` 发送字符串消息 `text` |
| wait_for_start() | 等待直至服务端完全关闭，也就是可以启动 |
| restart() | 依次执行 `stop()`、`wait_for_start()`、`start()` 来重启服务端 |
| stop_exit() | 关闭服务端以及 MCDR，也就是退出整个程序 |

## info

这是一个解析后的消息对象，属于 `utils/info.py` 中的 Info 类。它具有以下属性：

| 属性 | 内容 |
|---|---|
| hour | 一个整数，代表消息发出时间的小时数。若无则为 `None` |
| min | 一个整数，代表消息发出时间的分钟数。若无则为 `None` |
| sec | 一个整数，代表消息发出时间的秒数。若无则为 `None` |
| raw_content | 未解析的该消息的原始字符串 |
| content | 如果该消息是玩家的聊天信息，则其值为玩家的聊天内容。否则其值为原始信息除去时间/线程名等前缀信息后的字符串 |
| player | 当这条消息是一条来自玩家的聊天信息时，值为代表该玩家名称的字符串，否则为 `None` |
| source | 一个整数。若该消息是来自服务端的标准输出流，则为 `0`；若来自控制台输入，则为 `1` |
| is_player | 等价于 `player != None` |
| is_user | 等价于 `source == 1 or is_player` |

### 例子

对于下面这条来自服务端标准输出流的消息：

`[11:10:00 INFO]: Preparing level "world"`

info 对象的属性分别为：

| 属性 | 值 |
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

对于下面这条来自服务端标准输出流的消息：

`[09:00:00] [Server thread/INFO]: <Steve> Hello`

info 对象的属性分别为：

| 属性 | 值 |
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

这是一个字符串，代表相关玩家的名称，如 `Steve`

### old_module

这是一个模块的实例，用于在插件重载后新的插件继承旧插件的一些必要信息用。如果其值为 None 则代表这是 MCDR 刚开始运行时首次在加载插件

相关应用例子：

```
counter = 0

def on_load(server, old_module):
	global counter
    if old_module is not None:
        counter = old_module.counter + 1
    else:
        counter = 1
    server.say(f'这是第{counter}次加载插件')
```

## 将 MCDaemon 的插件移植至 MCDR

1. 将旧插件的仅能在 python2 上运行的代码修改为可在 python3 上运行
2. 将变量/方法名更新为 MCDR 的名称，如将 `onServerInfo` 修改为 `on_info`，将 `isPlayer` 修改为 `is_player`
3. MCDR 在控制台输入指令时也会调用 `on_info`，注意考虑插件是否兼容这种情况

