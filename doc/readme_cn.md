MCDReforged
--------

[English](https://github.com/Fallen-Breath/MCDReforged/blob/master/readme.md)

> 这是一个基于 Python 的 Minecraft 服务端控制工具

MCDReforged（以下简称 MCDR）是一个可以在完全不对 Minecraft 服务端进行修改的情况下，通过可自定义的插件系统，提供对服务端的管理能力的工具

小至计算器、高亮玩家、b站弹幕姬，大至操控计分板、管理结构文件、自助备份回档，都可以通过 MCDR 及相配套的插件实现

非常感谢 chino_desu 以及他的 [MCDaemon 1.0](https://github.com/kafuuchino-desu/MCDaemon)

QQ群: [1101314858](https://jq.qq.com/?k=5gUuw9A)

## 优势

- 运行于服务端之上，完全不需要修改服务端，保留原汁原味的原版特性
- 可热重载的插件系统，无需重启服务端即可更新插件
- 多平台/服务端的兼容性，支持在 Linux / Windows 下运行vanilla、paper 已及 bungeecord

## 它是如何工作的？

MCDR 使用了 `Popen` 来启动服务端，以此来控制服务端的标准输入输出流。就这样

## 环境要求

Python 的版本需要 Python 3.6+。已在如下环境中测试运行通过:

- `Windows10 x64` `Python 3.6`
- `Centos7 x64` `Python 3.8`
- `Ubuntu18.04.4 x64` `Python 3.6`

### 依赖的 python 模块

- ruamel.yaml
- requests
- colorlog
- colorama

需要的模块也储存在了 `requirement.txt` 中，可以直接执行 `pip install -r requirement.txt` 来安装所需要的模块

## 使用方法

1. 于 [Release 页面](https://github.com/Fallen-Breath/MCDReforged/releases) 下载最新的 MCDR 并解压。当然你可以直接 clone 本仓库以获得最新构建（可能不稳定但会有最新功能）
2. 填写配置文件，并将服务端相关文件以及 MCDR 插件放至相应文件夹中
3. 使用 `python MCDReforged.py` 运行 MCDR

对于默认配置而言，文件目录结构大致如下：

```
MCDReforged/
├─ plugins/
│  ├─ my_plugin1.py
│  ├─ my_plugin2.py
│  └─ ...
│
├─ resources/
│  ├─ lang/
│  └─ ...
│
├─ utils/
│  └─ ...
│
├─ server/
│  ├─ world/
│  │   └─ ...
│  ├─ minecraft_server.jar
│  └─ start.sh
│
└─ MCDReforged.py
```

## 配置文件

配置文件为 `config.yml`

### language

默认值: `en_us`

MCDR 使用的语言

语言文件 `my_lang.yml` 需要被放置在 `lang/` 文件夹中，并以 utf8 格式编码

### working_directory

默认值: `server`

服务端的工作路径

默认为 `server`，即服务端将在 `server` 文件夹中执行

### start_command

默认值: `java -Xms1G -Xmx2G -jar minecraft_server.jar nogui`

启动指令，诸如 `java -jar minecraft_server.jar` 或者 `./start.sh`

### parser

默认值: `vanilla_parser`

解析器选项。对于不同种类的服务端需要使用不同种类的解析器。可用选项为：

| 解析器名称 | 兼容的服务器类型 |
|---|---|
| vanilla_parser | 适用于原版 / Carpet / Fabric 服务端 |
| bukkit_parser | 适用于 1.14 以下的 Bukkit / Spiogt 服务端，和任意版本的 Paper 服务端 |
| bukkit_parser_14 | 适用于 1.14 及以上的 Bukkit / Spiogt 服务端 |
| forge_parser | 适用于 Forge 服务端 |
| cat_server_parser | 适用于 [CatServer](https://github.com/Luohuayu/CatServer) 服务端 |
| bungeecord_parser | 适用于Bungeecord 服务端。请在启动参数的 `-jar` 前添加 `-Djline.terminal=jline.UnsupportedTerminal` 以让其支持 MCDR 的控制，[来源](https://www.spigotmc.org/wiki/start-up-parameters/) |
| waterfall_parser | 适用于 Waterfall 服务端 |

### encoding

默认值: ` `

用于编码输入文本至服务端标准输入流的编码格式。Windows 用户如果 MCDR 往聊天栏输出的文字乱码了可以试试填成 `gbk`

留空以让 MCDR 自动检测编码格式

### decoding

默认值: ` `

用于解码服务端标准输出流的文本的编码格式

留空以让 MCDR 自动检测编码格式

### console_command_prefix

默认值: `!!`

对于任意以其为前缀的由控制台输入的命令，MCDR 将不会将此命令输入至服务端的标准输入流

### enable_rcon

默认值: `false`

如果值为 `true`，MCDR 会在服务端启动完成后向服务器发起 rcon 连接，这意味着插件可以通过 rcon 连接来向服务端发送命令并得到返回结果

如果值为 `false`，MCDR 不会向服务端发起 rcon 连接

### rcon_address

用于 rcon 连接的地址。对于本地服务器来说（已经是了）使用默认值即可

默认值: `127.0.0.1`

### rcon_port

用于 rcon 连接的端口，应当与 `server.properties` 文件中的 `rcon.port` 相同

默认值: `25575`

### rcon_password

用于 rcon 连接的密码，应当与 `server.properties` 文件中的 `rcon.password` 相同

默认值: `password`

### disable_console_thread

默认值: `false`

是否禁用控制台命令输入的线程，禁用后将无法从控制台控制 MCDR

除非必要，保持 `false` 即可

### download_update

默认值: `true`

如果值为 `true`，MCDR会在检测到新版本后自动将新版本下载至 `MCDR_update` 文件夹

### debug_mode

默认值: `false`

调试模式开关

除非必要，保持 `false` 即可

## 插件

[插件文档](https://github.com/Fallen-Breath/MCDReforged/blob/master/doc/plugin_cn.md)

插件用法可参考 `plugins/sample_plugin.py`

[这里](https://github.com/MCDReforged-Plugins/PluginCatalogue)是一个 MCDR 的插件收集仓库

## 权限

MCDR 配备了一个简易的权限系统给插件制作者使用

一共有 4 种不同的权限等级：

| 名称 | 值 | 描述 |
|---|---|---|
| admin | 3 | 管理者，拥有控制 MCDR 的能力
| helper | 2 | 助手，可以协助管理者
| user | 1 | 普通用户，普通玩家的身份
| guest | 0 | 访客

控制台输出所属的权限等级总是最高的 `admin` 级

### 权限文件

权限文件 `permission.yml` 是该系统的配置以及储存文件

- `default_level`: 新玩家默认的权限等级。默认值: `user`
- `admin`: 拥有权限等级 `admin` 的玩家列表
- `helper`: 拥有权限等级 `helper` 的玩家列表
- `user`: 拥有权限等级 `user` 的玩家列表
- `guest`: 拥有权限等级 `guest` 的玩家列表

玩家列表可以参照如下方式填写：

```
admin:
- Notch
helper:
- Steve
- Alex
user:
guest:
```

## 命令

MCDR 提供了一些控制 MCDR 的命令，它们均可在游戏中通过聊天或者通过控制台输入来执行。它们是：

| 命令 | 缩写 | 功能 |
|---|---|---|
| !!MCDR |  | 显示帮助信息
| !!MCDR status |  | 显示 MCDR 的状态
| !!MCDR reload | !!MCDR r | 显示 reload 命令的帮助信息
| !!MCDR reload plugin | !!MCDR r plg | 加载 / 重载 / 卸载**有修改的**插件
| !!MCDR reload config | !!MCDR r cfg | 重新加载配置文件
| !!MCDR reload permission | !!MCDR r perm | 重新加载权限文件
| !!MCDR reload all | !!MCDR r all | 重新加载上述所有
| !!MCDR permission | !!MCDR perm | 显示 permission 命令的帮助信息
| !!MCDR permission list \[\<level\>\] | !!MCDR perm list \[\<level\>\] | 列出所有玩家的权限等级。如果\[\<level\>\] 被指定则只会列出权限等级 \[\<level\>\] 的列表
| !!MCDR permission set \<player\> \<level\> | !!MCDR perm set \<player\> \<level\> | 将玩家 \<player\> 的权限等级设置为 \<level\>
| !!MCDR permission remove \<player\> | !!MCDR perm rm \<player\> | 将玩家 \<player\> 从权限等级数据库中移除
| !!MCDR permission setdefault \<level\> | !!MCDR perm setd \<level\> | 将默认权限等级设置为 \<level\>
| !!MCDR plugin list | !!MCDR plg list | 列出所有的插件
| !!MCDR plugin load \<plugin\> | !!MCDR plg load \<plugin\> | 加载 / 重载名为 \<plugin\> 的插件
| !!MCDR plugin enable \<plugin\> | !!MCDR plg enable \<plugin\> | 启用名为 \<plugin\> 的插件
| !!MCDR plugin disable \<plugin\> | !!MCDR plg disable \<plugin\> |  禁用名为 \<plugin\> 的插件
| !!MCDR plugin reloadall | !!MCDR plg ra | 加载 / 重载 / 卸载**所有**插件
| !!MCDR checkupdate | !!MCDR cu | 从 Github 检测更新
  
只有具有 `admin` 权限等级的玩家才被允许通过游戏输入执行这些命令

除此之外还有一个 `!!help` 指令来展示所有的注册了的插件帮助信息

## 注意事项

- 在使用 Bungeecord 服务端时请确保在启动参数的 `-jar` 前添加了 `-Djline.terminal=jline.UnsupportedTerminal`，否则 MCDR 可能会无法控制服务端的标准输入流

