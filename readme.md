MCDReforged
--------

[中文](https://github.com/Fallen-Breath/MCDReforged/blob/master/doc/readme_cn.md)

> This is a python based Minecraft server controlling tool

MCDReforge (abbreviated as MCDR) is a tool which provides the management ability of the Minecraft server using custom plugin system. It doesn't need to modify or mod the original Minecraft server at all

From in-game calculator, player high-light, to manipulate scoreboard, manage structure file and backup / load backup, you can implement these by using MCDR and related plugins

Great thanks to chine_desu and his [MCDaemon 1.0](https://github.com/kafuuchino-desu/MCDaemon)

## Advantage

- It's running above the server. It doesn't need to modify the server at all which keep everything vanilla
- Hot-reloadable plugin system. You don't need to shut down the server to update the plugins
- Multi platform / server compatibility. Supports vanilla, paper and bungeecord on Linux / Windows

## Environment

Python version should be python3 and at least it works on Python 3.6 and Python 3.8

Already tested in Windows10 x64 Python3.6 and Centos7 x64 Python 3.8

### Python modules

- PyYAML

The requirements are also stored in `requirements.txt`. You can execute `pip install -r requirement.txt` to install all needed modules

## Usage

1. Download the latest MCDR release in the [release page](https://github.com/Fallen-Breath/MCDReforged/releases)
2. Fill the config file. Put all server related file and MCDR plugins into correct folders
3. Execute `python MCDReforged.py` to start MCDR

For default config, the file structure should be something like this:

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
   ├─minecraft_server.jar
   └─start.sh
```

## Config

The config file is `config.yml`

`working_directory`: The working directory of the server. Default value is `server`, which means the server will run in the `server/` folder

`start_command`: The start command, like `java -jar minecraft_server.jar` or `./start.sh`

`parser`: The specific parser for different type of server. Available options:

- `vanilla_parser`: for Vanilla / Carpet / Fabric server
- `paper_parser`: for Bukkit / Spiogt / Paper server
- `bungeecord_parser`: for Bungeecord / Waterfall server. Please add `-Djline.terminal=jline.UnsupportedTerminal` before `-jar` in the start command for MCDR support. [From](https://www.spigotmc.org/wiki/start-up-parameters/)

`debug_mode`: Debug mode switch. Keep it as `false` unless necessary

## Plugin

[Plugin document](https://github.com/Fallen-Breath/MCDReforged/blob/master/doc/plugin.md)

Input `!!MCDR reload` in game chat or in console to reload plugins

Plugin usage can refer to `plugins/sample_plugin.py`

## Notes

- Make sure you add `-Djline.terminal=jline.UnsupportedTerminal` before `-jar` in the start command if your are running Bungeecord or Waterfall server, or MCDR might not be able to control the standard input stream of the server in Windows OS