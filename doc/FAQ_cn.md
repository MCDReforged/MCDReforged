# **请先阅读MCDR的Readme!!!**
[简体中文](https://github.com/Fallen-Breath/MCDReforged/blob/master/doc/readme_cn.md)

[Englist](https://github.com/Fallen-Breath/MCDReforged/blob/master/readme.md)

MCDReforged Frequently Asked Questions
---

> 由于总有人在群里问各种蠢问题，所以我就写了这个

##目录
  * [第一次使用](#第一次使用)
  * [插件开发](#插件开发)

## 第一次使用
这是你很多人第一次使用MCDR经常遇到的问题

> 这是个啥，怎么用？

把你的服务器放到`server/`里面，然后修改一下`config`文件，加入一些你认为有用的插件

然后开启服务器，像常规开服那样直接使用即可

> 为啥这玩意是英文的？

配置文件第一条，你改成`zh_cn`啊

> 服务器无法启动？

你服务器有没有放进`server`文件夹？如果放进去了:

MCDR又不会自动给你生成个启动参数啊，把你原来的开服参数填到配置文件`start_command`啊

> 在后台的指令正常反馈，游戏内输什么也没用

检查一下你的服务器使用的核心，然后按照这个表格修改配置文件中的`paser`

| 解析器名称 | 兼容的服务器类型 |
|---|---|
| vanilla_parser | 适用于原版 / Carpet / Fabric 服务端 |
| bukkit_parser | 适用于 1.14 以下的 Bukkit / Spiogt 服务端，和任意版本的 Paper 服务端 |
| bukkit_parser_14 | 适用于 1.14 及以上的 Bukkit / Spiogt 服务端 |
| forge_parser | 适用于 Forge 服务端 |
| cat_server_parser | 适用于 [CatServer](https://github.com/Luohuayu/CatServer) 服务端 |
| bungeecord_parser | 适用于Bungeecord 服务端。请在启动参数的 `-jar` 前添加 `-Djline.terminal=jline.UnsupportedTerminal` 以让其支持 MCDR 的控制，[来源](https://www.spigotmc.org/wiki/start-up-parameters/) |
| waterfall_parser | 适用于 Waterfall 服务端 |

## 这是我们见过的开发者在群里问过的各种问题
**请先阅读插件开发文档!!!**

[简体中文](https://github.com/Fallen-Breath/MCDReforged/blob/master/doc/plugin_cn.md)

[Englist](https://github.com/Fallen-Breath/MCDReforged/blob/master/doc/plugin.md)

> 我该怎么开发?

用你聪明的大脑和灵巧的双手，还有基础的Python技能

> 读取的路径似乎错误，这是什么原因

MCDR的工作路径为`MCDReforged.py`的目录，所以要访问的子目录应该这样写:
```
.\config\
.\plugins\
```