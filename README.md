MCDReforged
--------

[![Python Versions](https://img.shields.io/pypi/pyversions/mcdreforged.svg)](https://pypi.org/project/mcdreforged)
[![PyPI Version](https://img.shields.io/pypi/v/mcdreforged.svg)](https://pypi.org/project/mcdreforged)
[![License](https://img.shields.io/github/license/Fallen-Breath/MCDReforged.svg)](https://github.com/Fallen-Breath/MCDReforged/blob/master/LICENSE)
[![Documentation Status](https://readthedocs.org/projects/mcdreforged/badge/)](https://mcdreforged.readthedocs.io/)

![MCDR-banner](logo_long.png)

**English** | [中文](README_cn.md)

> This is a python based Minecraft server control tool

MCDReforged (abbreviated as MCDR) is a tool which provides the management ability of the Minecraft server using custom plugin system. It doesn't need to modify or mod the original Minecraft server at all

From in-game calculator, player high-light, to manipulate scoreboard, manage structure file and backup / load backup, you can implement these by using MCDR and related plugins

Great thanks to chino_desu and his [MCDaemon 1.0](https://github.com/kafuuchino-desu/MCDaemon) for the idea of such a cool Minecraft control tool

Contact me on discord: `Fallen_Breath#1215`

## Advantage

- It's running above the server. It doesn't need to modify the server at all which keep everything vanilla
- Hot-reloadable plugin system. You don't need to shut down the server to update the plugins
- Multi platform / server compatibility. Supports vanilla, paper, bungeecord etc. on Linux / Windows

## How it works?

MCDR uses `Popen` to start the server, so it control the standard input / out stream of the server. That's it

## Plugin

[Here](https://github.com/MCDReforged/PluginCatalogue) is a MCDR plugin collection repository

## Document

Check https://mcdreforged.readthedocs.io/ for more details of MCDR
