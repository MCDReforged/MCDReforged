[English](README.md) | **中文**

<p align="center">
    <img src="logo.png" alt="MCDR logo" width="200" height="200">
</p>

<h1 align="center">MCDReforged</h1>

<p align="center">
    强大的，基于 Python 的 Minecraft 服务端控制工具。
</p>

<p align="center">
    <a href="https://pypi.org/project/mcdreforged">
        <img src="https://img.shields.io/pypi/pyversions/mcdreforged.svg?style=flat-square&logo=python&logoColor=white" alt="Python Versions">
    </a>
    <a href="https://pypi.org/project/mcdreforged">
        <img src="https://img.shields.io/pypi/v/mcdreforged.svg?style=flat-square&label=version" alt="PyPI Version">
    </a>
    <a href="https://github.com/Fallen-Breath/MCDReforged/blob/master/LICENSE">
        <img src="https://img.shields.io/github/license/Fallen-Breath/MCDReforged.svg?style=flat-square" alt="License">
    </a>
    <a href="https://mcdreforged.readthedocs.io/">
        <img src="https://readthedocs.org/projects/mcdreforged/badge/?style=flat-square" alt="Documentation Status">
    </a>
</p>

<p align="center">
    <a href="https://mcdreforged.readthedocs.io/zh_CN/latest">文档</a>
    ·
    <a href="https://github.com/MCDReforged/PluginCatalogue">插件</a>
    ·
    <a href="#常见问题">常见问题</a>
    ·
    <a href="#联系">联系</a>
</p>

## 关于

MCDReforged（以下简称 MCDR）是一个可以在完全不对 Minecraft 服务端进行修改的情况下，通过可自定义的插件系统，提供对服务端的管理能力的工具

小至计算器、高亮玩家、b 站弹幕姬，大至操控计分板、管理结构文件、自助备份回档，都可以通过 MCDR 及相配套的插件实现

非常感谢 chino_desu 以及他的 [MCDaemon 1.0](https://github.com/kafuuchino-desu/MCDaemon) 提出了这样一个超棒的 Minecraft 服务端控制工具的点子

## 优势

- 运行于服务端之上，完全不需要修改服务端，保留原汁原味的原版特性
- 可热重载的插件系统，无需重启服务端即可更新插件
- 多平台/服务端的兼容性，支持在 Linux / Windows 下运行 vanilla、paper 以及 bungeecord 等服务端

## 它是如何工作的？

MCDR 使用了 [Popen](https://docs.python.org/zh-cn/3/library/subprocess.html#subprocess.Popen) 来将服务端作为一个子进程启动，因此它便拥有了控制服务端标准输入/输出流的能力

Minecraft 服务器的控制台输出拥有着稳定的输出格式，并包含着大量与服务器有关的有用信息（如玩家聊天信息）。借此，MCDR 可以解析并分析服务端输出，将他们抽象成不同的事件并派发给插件进行响应

在 Minecraft 内置指令系统的帮助下，MCDR 可以通过向服务端标准输入流发送 Minecraft 指令来与 Minecraft 服务器做出交互

就这样！如果你愿意的话，你可以将 MCDR 视为一个盯着服务端控制台看的，可以根据服务端的输出快速地做出响应并向服务端输入相关指令的，一个机器人

## 常见问题

<details>
  <summary>如何安装/使用 MCDR？</summary>
  
  > 冷知识：MCDR 有还算详细的文档说明。你可以仔细看看这个页面的开头。
</details>

<details>
  <summary>MCDR 能否在XX服务端上使用？</summary>

  > 先查看文档的 `handler` 部分。如果 MCDR 尚不支持你使用的服务端，欢迎提交 Issue 或 PR。
</details>

<details>
  <summary>插件不能用怎么办？</summary>

  > 首先，检查插件是否正常加载。阅读插件的 README。插件问题不一定与 MCDR 本身有关。请先在插件的 Github 仓库中提交 Issue。
</details>

<details>
  <summary>没有我想要的插件，垃圾项目</summary>

  > 自己动手，丰衣足食。当然，你也可以在 QQ 群里找到许多愿意“帮助”你的开发者。
</details>

## 联系

在 Discord 上联系我: `Fallen_Breath#1215`

QQ 群: [1101314858](https://jq.qq.com/?k=5gUuw9A)