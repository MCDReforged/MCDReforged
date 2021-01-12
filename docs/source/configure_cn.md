# 配置文件

MCDR的配置文件是`config.yml`。它位于，也应该位于MCDR的工作目录中。

在启动时，MCDR将尝试加载配置文件。如果配置文件不存在，MCDR则将生成默认配置文件并退出。否则，MCDR将加载配置文件并将其内容与默认配置文件进行比较。如果您的配置文件缺少任何选项，MCDR则会将默认值添加到您的配置文件末尾。

配置文件使用[YAML](https://zh.wikipedia.org/wiki/YAML)格式。

当MCDR运行时，你可以使用`!!MCDR reload config`命令（或其缩写`!!MCDR r cfg`）来重载配置文件。

## 配置项列表

### 基本

#### language

MCDR用于输出信息的语言。

选项类型：string

默认值：`en_us`

可选项：`en_us`，`zh_cn`

#### working_directory

服务端的工作目录。你应该将所有与服务器相关的文件放入此目录。

选项类型：string

默认值：`server`

#### start_command

启动服务器的命令行。

例如:

- `java -Xms1G -Xmx2G -jar minecraft_server.jar nogui`，直接启动服务器
- `./start.sh`，已经在工作目录中写了启动脚本

选项类型：string

默认值：`java -Xms1G -Xmx2G -jar minecraft_server.jar nogui`

#### handler

不同服务端有着截然不同的输出和指令。服务端解析器是用于在各种服务器之间进行处理的模块，也是MCDR控制服务端的接入点。

解析器确定解析服务器标准输出文本的特定方法，并使用正确的命令控制服务端。

内置的解析器及其适用的服务端如下表所示：

| 解析器名称 | 兼容的服务器类型 |
|---|---|
| vanilla_handler | 适用于 原版 / Carpet / Fabric 服务端。 |
| beta18_handler | 适用于 原版beta 1.8。也许能在其他beta版本运行，但是只测试过beta 1.8.1。 |
| bukkit_handler | 适用于 1.14以下的Bukkit/Spigot 服务端，和任意版本的 Paper 服务端。 |
| bukkit_handler_14 | 适用于 1.14及以上的Bukkit/Spigot 服务端。 |
| forge_handler | 适用于 Forge 服务端。 |
| cat_server_handler | 适用于 [CatServer](https://github.com/Luohuayu/CatServer) 服务端。 |
| bungeecord_handler | 适用于Bungeecord 服务端。请在启动参数的`-jar`前添加`-Djline.terminal=jline.UnsupportedTerminal`以让其支持 MCDR 的控制。[来源](https://www.spigotmc.org/wiki/start-up-parameters/) |
| waterfall_handler | 适用于 Waterfall 服务端 |
| basic_handler | 这个解析器除了返回原始字符串不干任何事。除非你想用MCDR启动非Minecraft服务器，否则不要用它。 |

选项类型：string

默认值：`vanilla_handler`

#### encoding / decoding

用于解码服务端标准输出流的文本的编码格式。

留空以让 MCDR 自动检测编码格式。如果它不起作用（例如游戏中的随机字符），则需要根据您的操作系统和语言手动进行指定。

选项类型：string 或 null

默认值：` `

例如：`utf8`，`gbk`

#### plugin_directories

MCDR搜索将要加载插件的目录列表。

选项类型：string列表

默认值：

```yaml
plugin_directories:
- plugins
```

例如：

```yaml
plugin_directories:
- plugins
- path/to/my/plugin/directory
- another/plugin/directory
```

#### rcon

rcon的设置。如果启用了rcon，则在服务端rcon启动后，MCDR将启动rcon客户端并连接到服务端。这样插件就可以通过rcon让服务端执行查询命令。

##### enable

rocn开关

选项类型：boolean

默认值：`false`

##### address

用于rcon连接的地址。

选项类型：string

默认值：`127.0.0.1`

##### port

用于 rcon 连接的端口。

选项类型：integer

默认值：`25575`

##### password

用于 rcon 连接的密码。

选项类型：string

默认值：`password`

#### check_update

如果设置为true，MCDR将会每隔24小时执行一次更新检测。

选项类型：boolean

默认值：`true`


### 高级

为高级用户配置选项

#### disable_console_thread

设置为true时，MCDR将不会启动控制台线程来处理控制台命令输入。

如果你不知道这是啥，请不要动它。

选项类型：boolean

默认值：`false`

#### disable_console_color

设置为true时，MCDR将在所有消息打印到控制台之前删除所有控制台字体格式化程序代码。

选项类型：boolean

默认值：`false`

#### custom_info_reactors

用于处理info实例的自定义info响应器类所组成的列表。这些类应当是`AbstractInfoReactor`的子类。

所有自定义info响应器都将注册到反应堆列表中，以处理来自服务器的信息。

选项类型：string列表，或null

默认值：

```yaml
custom_info_reactors:
```

例如：

下面这个例子中，`my.custom.reactor`是包路径，`MyInfoReactor`是类名。

```yaml
custom_info_reactors:
- my.custom.reactor.MyInfoReactor
```

#### custom_handlers

用于处理info实例的自定义info响应器类所组成的列表。这些类应当是`AbstractServerHandler`的子类。

这样你就可以在上面的[handler](#handler)选项中通过解析器的名称指派其解析标准输出文本。

解析器名称通过get_name方法定义。

选项类型：string列表，或null

默认值：

```yaml
custom_handlers:
```

例如：

下面这个例子中，`my.custom.handler`是包路径，`MyHandler`是类名。

```yaml
custom_handlers:
- my.custom.handler.MyHandler
```

#### debug

调试日志模式开关。将`all`设置为true启用所有的调试输出。也可以仅仅打开某些选项，来启用某些调试日志输出。

默认值：

```yaml
debug:
  all: false
  mcdr: false
  handler: false
  reactor: false
  plugin: false
  permission: false
  command: false
```
