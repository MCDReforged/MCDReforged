MCDReforged
--------

[![Python Versions](https://img.shields.io/pypi/pyversions/mcdreforged.svg)](https://pypi.org/project/mcdreforged)
[![PyPI Version](https://img.shields.io/pypi/v/mcdreforged.svg)](https://pypi.org/project/mcdreforged)
[![License](https://img.shields.io/github/license/Fallen-Breath/MCDReforged.svg)](https://github.com/Fallen-Breath/MCDReforged/blob/master/LICENSE)
[![Documentation Status](https://readthedocs.org/projects/mcdreforged/badge/)](https://mcdreforged.readthedocs.io/)

![MCDR-banner](https://raw.githubusercontent.com/Fallen-Breath/MCDReforged/master/logo_long.png)

[English](https://github.com/Fallen-Breath/MCDReforged/blob/master/README.md) | **中文**

> 这是一个基于 Python 的 Minecraft 服务端控制工具

MCDReforged（以下简称 MCDR）是一个可以在完全不对 Minecraft 服务端进行修改的情况下，通过可自定义的插件系统，提供对服务端的管理能力的工具

小至计算器、高亮玩家、b 站弹幕姬，大至操控计分板、管理结构文件、自助备份回档，都可以通过 MCDR 及相配套的插件实现

非常感谢 chino_desu 以及他的 [MCDaemon 1.0](https://github.com/kafuuchino-desu/MCDaemon) 提出了这样一个超棒的 Minecraft 服务端控制工具的点子

QQ 群: [1101314858](https://jq.qq.com/?k=5gUuw9A)

## 优势

- 运行于服务端之上，完全不需要修改服务端，保留原汁原味的原版特性
- 可热重载的插件系统，无需重启服务端即可更新插件
- 多平台/服务端的兼容性，支持在 Linux / Windows 下运行 vanilla、paper 以及 bungeecord 等服务端

## 它是如何工作的？

MCDR 使用了 `Popen` 来将服务端作为一个子进程启动，因此它便拥有了控制服务端标准输入/输出流的能力

Minecraft 服务器的控制台输出拥有着稳定的输出格式，并包含着大量与服务器有关的有用信息（如玩家聊天信息）。借此，MCDR 可以解析并分析服务端输出，将他们抽象成不同的时间并派发给插件进行相应

在 Minecraft 内置指令系统的帮助下，MCDR 可以通过向服务端标准输入流发送 Minecraft 指令来与 Minecraft 服务器做出交互

就这样！如果你愿意的话，你可以将 MCDr 视为一个盯着服务端控制台看的，可以根据服务端的输出快速地做出响应并向服务端输入相关指令的，一个机器人

## 插件

[这里](https://github.com/MCDReforged/PluginCatalogue) 是一个 MCDR 的插件收集仓库

## 文档

想要了解更多关于 MCDR 的详情？去看文档吧 https://mcdreforged.readthedocs.io/zh_CN/latest/
