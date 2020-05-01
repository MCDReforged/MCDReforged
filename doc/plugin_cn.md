MCDReforged 插件文档
---

[English](https://github.com/Fallen-Breath/MCDReforged/blob/master/doc/plugin.md)

与 MCDaemon 类似，一个 MCDR 的插件是一个位与 `plugins/` 文件夹下的 `.py` 文件。MCDR 会在启动时自动加载该文件夹中的所有插件

在 `plugins/` 文件夹中有一个样板插件 `sample_plugin.py`，可以参考其中的内容

## 事件

当服务端触发某些指定事件时，如果插件有声明下列方法的话，MCDR 会调用每个插件的对应方法。MCDR 调用每个插件的方法时会为其新建一个独立的线程供其运行

| 方法 | 调用时刻 | 阻塞 | 参考用途 |
|---|---|---|---|
| on_load(server, old_module) | 插件被加载 | 否 | 新插件继承旧插件的信息 |
| on_unload(server) | 插件被卸载 | 否 | 清理或关闭旧插件的功能 |
| on_info(server, info) | 服务端的标准输出流有输出，或者控制台有输入 | 否 | 插件响应相关信息 |
| on_player_joined(server, player) | 玩家加入服务端 | 否 | 插件响应玩家加入游戏 |
| on_player_left(server, player) | 玩家离开服务端 | 否 | 插件响应玩家离开游戏 |
| on_death_message(server, death_message) | 玩家死亡显示死亡信息 | 否 | 插件响应玩家死亡 |
| on_player_made_advancement(server, player, advancement) | 玩家获得了一个进度 | 否 | 插件响应相关信息 |
| on_server_startup(server) | 服务端启动完成，如原版服务端输出 `Done (1.0s)! For help, type "help"` 后 | 否 | 插件相关初始化 |
| on_server_stop(server) | 服务端已关闭，更准确地说，服务端进程已终止 | 否 | 处理相关事情 |
| on_mcdr_stop(server) | 服务端已经关闭，MCDR 即将退出 | 是 | 保存数据、释放资源

注：每个插件并不需要实现所有上述方法，按需实现即可

其中，各个参数对象的信息如下：

### player, death_message, advancement

这些参数均为字符串，其中：

`player` 代表相关玩家的名称，如 `Steve`

`death_message` 表示死亡信息，如 `Steve tried to swim in lava`， 其值等同于 `info.content`

`advancement` 表示成就内容，如 `Stone Age`

### server

这是用于插件与服务端进行交互的对象，属于 `utils/server_interface.py` 中的 ServerInterface 类

它具有以下常量：

| 常量 | 类型 | 功能 |
|---|---|---|
| MCDR | bool | 这个常量是给插件判断他是否运行在 MCDR中的。你可以使用 `hasattr(server, 'MCDR')` 来判断

它具有以下变量：

| 变量 | 类型 | 功能 |
|---|---|---|
| logger | logging.Logger | MCDR 的一个记录器，推荐用 `server.logger.info(message)` 替代 `print(message)` 来向控制台输出信息。[相关文档](https://docs.python.org/zh-cn/3/library/logging.html#logger-objects)

它具有以下方法：

**服务端控制**

| 方法 | 功能 |
|---|---|
| start() | 启动服务端。仅在服务端未启动的情况下有效 |
| stop() | 使用服务端对应的指令，如 `stop` 来关闭服务端。仅在服务端运行时有效 || is_running() | 服务端（准确地说，服务端进程）是否在运行 |
| wait_for_start() | 等待直至服务端完全关闭，也就是可以启动 |
| restart() | 依次执行 `stop()`、`wait_for_start()`、`start()` 来重启服务端 |
| stop_exit() | 关闭服务端以及 MCDR，也就是退出整个程序 |
| is_server_running() | 返回一个 bool 代表服务端（更准确地，服务端进程）是否在运行 |
| is_server_startup() | 返回一个 bool 代表服务端是否已经启动完成 |
| is_rcon_running() | 返回一个 bool 代表 rcon 是否在运行 |

**文本交互**

| 方法 | 功能 |
|---|---|
| execute(text) | 发送字符串 `text` 至服务端的标准输入流，并自动在其后方追加一个 `\n` |
| say(text) | 使用 `tellraw @a` 来在服务端中广播字符串消息 `text` |
| tell(player, text) | 使用 `tellraw <player>` 来在对玩家 `<player>` 发送字符串消息 `text` |
| reply(info, text) | 向消息源发生消息字符串 `text`: 如果消息来自玩家则调用 `tell(info.player, text)`; 如果不是则调用 MCDR 的 logger 来将 `text` 告示至控制台

字符串 `text` 中如果含有特殊字符 `"`、`\\`、`\n`，MCDR 会自动对其进行转义，因此无需担心传入的字符串格式

**其他**

| 方法 | 功能 |
|---|---|
| get_permission_level(obj) | 返回一个[整数](https://github.com/Fallen-Breath/MCDReforged/blob/master/doc/readme_cn.md#权限)，代表 `obj` 对象拥有的最高权限等级。`obj` 对象可为一个 `Info` 实例，或者是一个表示玩家名称的字符串。如果 `obj` 的类型不被支持或者 `Info` 实例并不来源自用户（`not info.is_user`），则返回 `None` |
| rcon_query(command) | 通过 rcon 向服务端发送指令 `command`，然后返回一个字符串，表示该指令执行后的返回值。如果 rcon 未在运行或者有异常发生，返回 `None` |
| get_plugin_instance(plugin_name) | 返回当前加载着的位于 `plugins/plugin_name.py` 的插件实例。使用此方法而非在插件中手动 import 可保证得到的目标插件实例与 MCDR 中的实例相同。若未找到该插件，返回 `None` |
| add_help_message(prefix, message) | 向 MCDR 的 `!!help` 信息库中加入一条指令前缀为 `prefix`，信息为 `message` 的帮助信息。`!!help` 信息库将在插件重载前清空。**推荐在方法 `on_load()` 中进行相关信息添加** |

### info

这是一个解析后的消息对象，属于 `utils/info.py` 中的 Info 类。它具有以下属性：

| 属性 | 内容 |
|---|---|
| id | 由一个静态的累加计数器赋值。id 代表着这个 Info 是第几个被创建的信息类。比如 MCDR 启动时第一条被解析的 Info 的 id 是 `1`，第二条的 id 是 `2`  |
| hour | 一个整数，代表消息发出时间的小时数。若无则为 `None` |
| min | 一个整数，代表消息发出时间的分钟数。若无则为 `None` |
| sec | 一个整数，代表消息发出时间的秒数。若无则为 `None` |
| raw_content | 一个字符串，未解析的该消息的原始字符串 |
| content | 如果该消息是玩家的聊天信息，则其值为玩家的聊天内容。否则其值为原始信息除去时间/线程名等前缀信息后的字符串 |
| player | 当这条消息是一条来自玩家的聊天信息时，值为代表该玩家名称的字符串，否则为 `None` |
| source | 一个整数。若该消息是来自服务端的标准输出流，则为 `0`；若来自控制台输入，则为 `1` |
| logging_level | 一个字符串，代表该信息的 logging 级别，例如 `INFO` 或者 `WARN`。如果该消息来自控制台输入，则为 `None` |
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

### old_module

这是一个模块的实例，用于在插件重载后新的插件继承旧插件的一些必要信息用。如果其值为 `None` 则代表这是 MCDR 刚开始运行时首次在加载插件

相关应用例子：

```
counter = 0

def on_load(server, old_module):
    global counter
    if old_module is not None:
        counter = old_module.counter + 1
    else:
        counter = 1
    server.logger.info(f'这是第{counter}次加载插件')
```

## 工具

一些给插件开发者使用的造好的轮子

目前可以使用的有：

- `utils/rcon.py`: 一个 rcon 客户端
- `utils/stext.py`: Minecraft 高级文本容器

[工具文档](https://github.com/Fallen-Breath/MCDReforged/blob/master/doc/utils_cn.md)

## 一些编写插件的提示

- 默认工作路径是 MCDR 所在的文件夹。**不要**改变工作路径，这会弄乱各种东西的
- 对于 `on_info` 中的 info 参数请不要对其进行修改，只读就好
- 如果你需要导入其他插件，使用 `server.get_plugin_instance()` 而不是手动导入，这样子你可以得到跟 MCDR 所使用的相同的插件实例
- 在 `on_load()` 时调用 `server.add_help_message()` 来添加一些必要的帮助信息，这样子玩家可以通过 `!!help` 指令来了解到你的插件
- 保持环境整洁。将你的数据存放至 `MCDR/plugins/my_plugin/` 文件夹、将你的配置文件存放在 `MCDR/config/` 文件夹和将你的日志文件存放在 `MCDR/log/` 文件夹都是好主意
- `on_mcdr_stop()` 给予了你充足的时间来保存数据。但是要小心，不要跑进死循环里了，MCDR 还在等着你完工的

## 将 MCDaemon 的插件移植至 MCDR

1. 将旧插件的仅能在 python2 上运行的代码修改为可在 python3 上运行，并安装插件需要的 Python 模块
2. 将变量/方法名更新为 MCDR 的名称，如将 `onServerInfo` 修改为 `on_info`，将 `isPlayer` 修改为 `is_player`
3. MCDR 在控制台输入指令时也会调用 `on_info`，注意考虑插件是否兼容这种情况

一种比较偷懒的是在解决 python3 兼容问题后在旧插件末尾加入诸如以下的方法：

```
import copy

def on_load(server, old):
	onServerStartup(server)

def on_player_joined(server, player):
	onPlayerJoin(server, player)

def on_player_left(server, player):
	onPlayerLeave(server, player)

def on_info(server, info):
	info2 = copy.deepcopy(info)
	info2.isPlayer = info2.is_player
	onServerInfo(server, info2)
```
