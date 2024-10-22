
What is MCDR
============

MCDReforged (MCDR, hereinafter) is a tool to manage your Minecraft server with the custom plugin system. No need to modify the original Minecraft server at all

In-game calculator, player high-light, scoreboard manipulate, structure file management, world backup / rollback... you can control the whole Minecraft server with MCDR and its plugins

Greatly thanks to `chino_desu <https://github.com/kafuuchino-desu>`__ and his `MCDaemon 1.0 <https://github.com/kafuuchino-desu/MCDaemon>`__ for the idea of such a cool tool

Advantages
----------

Vanilla
~~~~~~~

MCDR runs above the server. It doesn't need to modify the server at all, which keeps everything **vanilla**

Plugin System
~~~~~~~~~~~~~

MCDR has a rich ecosystem of plugins from the community. From an in-game calculator, player highlighter, and Twitch chat bot, to a scoreboard manipulator, file manager, and backup system, all of them can be implemented with MCDReforged plugins

Meanwhile, the plugin system is hot-reloadable, so you don't need to shut down the server to update the plugins

Compatibility
~~~~~~~~~~~~~

MCDR supports most popular servers (Vanilla, Fabric, Spigot, Paper, etc.)

Supports multiple platforms (Windows, Linux, Mac, etc.)

How it works
------------

**TL;DR:** MCDR works like a robot that stares at the server console, responds to server output quickly, and inputs commands for users

MCDR uses `Popen <https://docs.python.org/3/library/subprocess.html#subprocess.Popen>`__ to start the server as a sub-process, so it has the ability to control the standard input / output stream of the server

Since the console output of a Minecraft server has a stable format and contains a large amount of useful information about the server, e.g. player chat messages, MCDR is able to parse and analyze the server output, abstract them into different events and dispatch them towards plugins for responding

With the help of the Minecraft command system, MCDR can send Minecraft commands via the standard input stream to affect the actual Minecraft server
