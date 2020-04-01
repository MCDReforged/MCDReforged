MCDReforged
--------

[English](https://github.com/Fallen-Breath/MCDReforged/blob/master/readme.md)

> 这是一个基于 Python 的 Minecraft 服务端控制程序

MCDReforged（以下简称 MCDR）是一个可以在完全不对 Minecraft 服务端进行修改的情况下，通过可自定义的插件系统，提供对服务端的管理能力

小至计算器、高亮玩家、b站弹幕姬，大至操控计分板、管理结构文件、自助备份回档，都可以通过 MCDR 及相配套的插件实现

感谢 chino_desu 以及他的 [MCDaemon 1.0](https://github.com/kafuuchino-desu/MCDaemon)

## 优势

- 运行于服务端之上，完全不需要修改服务端，保留原汁原味的原版特性
- 可热重载的插件系统，无需重启服务端即可更新插件
- 多平台/服务端的兼容性，vanilla、paper 甚至 bungeecord（仅 linux）均能使用

## 环境要求

Python 的版本需要 Python3，至少它在 Python 3.6 与 Python 3.8 中能运行

已在 Windows10 x64 以及 Centos7 x64 下测试运行通过

### Python 模块

- PyYAML

## 使用方法

1. 于 [Release 页面](https://github.com/Fallen-Breath/MCDReforged/releases) 下载最新的 MCDReforged 并解压
2. 填写配置文件，并将服务端相关文件以及 MCDReforged 插件放至相应文件夹中
3. 使用 `python MCDReforged.py` 运行 MCDReforged

对于默认配置而言，文件目录结构如下：

```
MCDReforged
├─plugins
│  ├─my_plugin1.py
│  ├─my_plugin2.py
│  └─...
│
├─utils
│  └─...
│
└─server
   ├─world
   │   └─...
   └─minecraft_server.jar
```

## 配置文件

配置文件为 `config.yml`

`working_directory`: 服务端的工作路径。默认为 `server`，即服务端将在 `server` 文件夹中执行

`start_command`: 启动指令，诸如 `java -jar minecraft_server.jar` 或者 `./start.sh`

`parser`: 解析器设置。对于不同种类的服务端需要使用不同种类的解析器。可用选项为：

- `vanilla_parser`: 适用于原版 / 地毯 / fabric 服务端
- `paper_parser`: 适用于 bukkit / spiogt / paper 服务端
- `bungeecord_parser`: 适用于 bungeecord / waterfall 服务端。请在启动参数的 `-jar` 前添加 `-Djline.terminal=jline.UnsupportedTerminal` 以让其支持 MCDR 的控制，[来源](https://www.spigotmc.org/wiki/start-up-parameters/)

`debug_mode`: 调试模式开关

## 插件

[插件文档](https://github.com/Fallen-Breath/MCDReforged/blob/master/doc/plugin_cn.md)

在游戏聊天中会在控制台输入 `!!MCDR reload` 来重载插件

插件用法可参考 `plugins/test_plugin.py`

## 注意事项

- 在使用 Bungeecord / Waterfall 服务端时请确保在启动参数的 `-jar` 前添加了 `-Djline.terminal=jline.UnsupportedTerminal`，否则在 Windows 下可能会无法控制服务端的标准输入
- 
