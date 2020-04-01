MCDReforged
--------

[English](https://github.com/Fallen-Breath/MCDReforged/blob/master/readme.md)

> 这是一个基于 Python 的 Minecraft 服务端控制工具

MCDReforged（以下简称 MCDR）是一个可以在完全不对 Minecraft 服务端进行修改的情况下，通过可自定义的插件系统，提供对服务端的管理能力的工具

小至计算器、高亮玩家、b站弹幕姬，大至操控计分板、管理结构文件、自助备份回档，都可以通过 MCDR 及相配套的插件实现

非常感谢 chino_desu 以及他的 [MCDaemon 1.0](https://github.com/kafuuchino-desu/MCDaemon)

## 优势

- 运行于服务端之上，完全不需要修改服务端，保留原汁原味的原版特性
- 可热重载的插件系统，无需重启服务端即可更新插件
- 多平台/服务端的兼容性，支持在 Linux / Windows 下运行vanilla、paper 已及 bungeecord

## 环境要求

Python 的版本需要 Python3，至少它在 Python 3.6 与 Python 3.8 中能运行

已在 Windows10 x64 Python3.6 以及 Centos7 x64 Python3.8 下测试运行通过

### Python 模块

- ruamel.yaml

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

`working_directory`: 服务端的工作路径。默认为 `server`，即服务端将在 `server` 文件夹中执行

`start_command`: 启动指令，诸如 `java -jar minecraft_server.jar` 或者 `./start.sh`

`parser`: 解析器选项。对于不同种类的服务端需要使用不同种类的解析器。可用选项为：

- `vanilla_parser`: 适用于原版 / 地毯 / Fabric 服务端
- `paper_parser`: 适用于 Bukkit / Spiogt / Paper 服务端
- `bungeecord_parser`: 适用于 Bungeecord / Waterfall 服务端。请在启动参数的 `-jar` 前添加 `-Djline.terminal=jline.UnsupportedTerminal` 以让其支持 MCDR 的控制，[来源](https://www.spigotmc.org/wiki/start-up-parameters/)

`encoding`: 编码方式。默认情况下使用 `utf8` 即可，如果操作系统是 Windows 中文版的话可使用 `gbk` 以防止出现乱码

`debug_mode`: 调试模式开关。除非有必要，否则设置为 `false` 即可

## 插件

[插件文档](https://github.com/Fallen-Breath/MCDReforged/blob/master/doc/plugin_cn.md)

在游戏聊天中会在控制台输入 `!!MCDR reload` 来重载插件

插件用法可参考 `plugins/sample_plugin.py`

## 权限

MCDR 配备了一个简易的权限系统给插件制作者使用。一共有 4 中不同的权限等级：

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

## 指令

MCDR 提供了一些控制 MCDR 的指令，它们均可在游戏中通过聊天或者通过控制台输入来执行。它们是：

| 指令 | 缩写 | 功能 |
|---|---|---|
| !!MCDR reload plugin | !!MCDR r plg | 重新加载插件
| !!MCDR reload config | !!MCDR r cfg | 重新加载配置文件
| !!MCDR reload permission | !!MCDR r perm | 重新加载权限文件
| !!MCDR reload all | !!MCDR r all | 重新加载上述所有

只有具有 `admin` 权限等级的玩家才被允许通过游戏输入执行这些命令

## 注意事项

- 在使用 Bungeecord / Waterfall 服务端时请确保在启动参数的 `-jar` 前添加了 `-Djline.terminal=jline.UnsupportedTerminal`，否则在 Windows 操作系统下 MCDR 可能会无法控制服务端的标准输入流

