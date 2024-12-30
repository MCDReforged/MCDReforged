MCDReforged
--------

[![Python Versions](https://img.shields.io/pypi/pyversions/mcdreforged.svg)](https://pypi.org/project/mcdreforged)
[![PyPI Version](https://img.shields.io/pypi/v/mcdreforged.svg)](https://pypi.org/project/mcdreforged)
[![Docker](https://img.shields.io/docker/v/mcdreforged/mcdreforged/latest?label=docker)](https://hub.docker.com/r/mcdreforged/mcdreforged)
[![License](https://img.shields.io/github/license/MCDReforged/MCDReforged.svg)](https://github.com/MCDReforged/MCDReforged/blob/master/LICENSE)
[![Documentation Status](https://readthedocs.org/projects/mcdreforged/badge/)](https://docs.mcdreforged.com/)

![MCDR-banner](https://raw.githubusercontent.com/MCDReforged/MCDReforged/master/logo/images/logo_long.png)

[English](https://github.com/MCDReforged/MCDReforged/blob/master/README.md) | [简体](https://github.com/MCDReforged/MCDReforged/blob/master/README_cn.md) | **繁體**

> 這是一個基於 Python 的 Minecraft 伺服端控制工具

MCDReforged（以下簡稱 MCDR）是一個可以在完全不對 Minecraft 伺服端進行修改的情況下，通過可自訂義的插件系統，提供對伺服端的管理能力的工具

小至計算機、高亮玩家、b 站彈幕姬，大至操控記分板、管理結構文件、自助備份回檔，都可以通過 MCDR 及相配套的插件實現

非常感謝 chino_desu 以及他的 [MCDaemon 1.0](https://github.com/kafuuchino-desu/MCDaemon) 提出了這樣一個超棒的 Minecraft 伺服端控制工具的點子

在 Discord 上聯絡我：`Fallen_Breath#1215`

## 優勢

- 運行於伺服端之上，完全不需要修改伺服端，保留原汁原味的原版特性
- 可熱重載的插件系統，無須重啟伺服端即可更新插件
- 多平台/伺服端的兼容性，支援在 Linux / Windows 下運行 vanilla、paper 以及 bungeecord 等伺服端

## 它是如何工作的？

MCDR 使用了 [Popen](https://docs.python.org/zh-cn/3/library/subprocess.html#subprocess.Popen) 来將伺服端作為一個子進程啟動，
因此它便擁有了控制伺服端標準輸入/輸出流的能力

Minecraft 伺服器的控制台輸出擁有著穩定的輸出格式，並包含著大量與伺服器有關的有用信息（如玩家聊天信息）。
藉此，MCDR 可以解析並分析伺服端輸出，將他们抽象成不同的事件並派發给插件進行響應

在 Minecraft 内置命令系統的幫助下，MCDR 可以通過向伺服端標準輸入流發送 Minecraft 命令来與 Minecraft 伺服器做出交互

就這樣！如果你願意的话，你可以將 MCDR 視為一個盯著伺服端控制台看的，可以根據伺服端的輸出快速地做出響應並向伺服端輸入相關命令的，一個機器人

## 插件

[這裡](https://github.com/MCDReforged/PluginCatalogue) 是一個 MCDR 的插件收集倉庫

## 文檔

想要了解更多關於 MCDR 的詳情？去看文檔吧 https://docs.mcdreforged.com/zh_CN/latest/
