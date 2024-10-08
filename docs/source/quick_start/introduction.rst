
What is MCDR
============

MCDReforged (MCDR, hereinafter) is a tool to manage your Minecraft server with the custom plugin system. No need to modify the original Minecraft server at all

In-game calculator, player high-light, scoreboard manipulate, structure file management, backup / rollback... you can control the whole world with MCDR and its plugins

Greatly thanks to chino_desu and his MCDaemon 1.0 for the idea of such a cool tool

Advantage
---------

Vanilla
~~~~~~~

MCDR runs above the server. It doesn't need to modify the server at all, which keep everything **vanilla**

Plugin System
~~~~~~~~~~~~~

MCDR has a hot-reloadable plugin system. You don't need to shut down the server to update the plugins

Compatibility
~~~~~~~~~~~~~

We supports most popular server softwares (Vanilla, Fabric, Spigot, Paper, etc.)

On multiple platforms (Windows, Linux, Mac, etc.)

How it works
------------

**TL;DR:** MCDR works like robot that stares at the server console, respond to server output quickly, and inputting commands for users

MCDR uses `Popen <https://docs.python.org/3/library/subprocess.html#subprocess.Popen>`__ to start the server software as a sub-process, so it has the ability to control the standard input / out stream of the server

Since the console output of a Minecraft server has a stable format and contains a large amount of useful information about the server, e.g. player chat messages, MCDR is able to parse and analyze the server output, abstract them into different events and dispatch them towards plugins for responding

With the help of Minecraft command system, MCDR can send Minecraft commands via the standard input stream to affect the actual Minecraft server
