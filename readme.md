MCDReforged
--------

[中文](https://github.com/Fallen-Breath/MCDReforged/blob/master/doc/readme_cn.md)

> This is a python based Minecraft server control tool

MCDReforge (abbreviated as MCDR) is a tool which provides the management ability of the Minecraft server using custom plugin system. It doesn't need to modify or mod the original Minecraft server at all

From in-game calculator, player high-light, to manipulate scoreboard, manage structure file and backup / load backup, you can implement these by using MCDR and related plugins

Great thanks to chino_desu and his [MCDaemon 1.0](https://github.com/kafuuchino-desu/MCDaemon)

Contact me on discord: `Fallen_Breath#1215`

## Advantage

- It's running above the server. It doesn't need to modify the server at all which keep everything vanilla
- Hot-reloadable plugin system. You don't need to shut down the server to update the plugins
- Multi platform / server compatibility. Supports vanilla, paper and bungeecord on Linux / Windows

## How it works?

MCDR uses `Popen` to start the server, so it control the standard input / out stream of the server. That's it

## Environment

Python version should be Python 3.6+. Already tested in environments  below:

- `Windows10 x64` `Python 3.6`
- `Centos7 x64` `Python 3.8`
- `Ubuntu18.04.4 x64` `Python 3.6`

### Required python modules

- ruamel.yaml
- requests
- colorlog
- colorama

The requirements are also stored in `requirements.txt`. You can execute `pip install -r requirement.txt` to install all needed modules

## Usage

1. Download the latest MCDR release in the [release page](https://github.com/Fallen-Breath/MCDReforged/releases). Of course you can just clone this repository to get the latest build (might be unstable but with latest features)
2. Fill the config file. Put all server related file and MCDR plugins into correct folders
3. Execute `python MCDReforged.py` to start MCDR

For default config, the file structure should be something like this:

```
MCDReforged/
├─ plugins/
│  ├─ my_plugin1.py
│  ├─ my_plugin2.py
│  └─ ...
│
├─ resources/
│  ├─ lang/
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

## Config

The config file is `config.yml`

### language

Default: `en_us`

The language that MCDR will use

Language file `my_lang.yml` needs to be in `lang/` folder, and encoded in utf8

### working_directory

Default: `server`

The working directory of the server

Default value is `server`, which means the server will run in the `server/` folder

### start_command

Default: `java -Xms1G -Xmx2G -jar minecraft_server.jar nogui`

The start command, like `java -jar minecraft_server.jar` or `./start.sh`

### parser

Default: `vanilla_parser`

The specific parser for different type of server. Available options:

| Parser Name | Compatible server types |
|---|---|
| vanilla_parser | For Vanilla / Carpet / Fabric server |
| bukkit_parser | For Bukkit / Spigot server with Minecraft version below 1.14, and Paper server in all version |
| bukkit_parser_14 | For Bukkit / Spigot server with Minecraft version 1.14 and above |
| forge_parser | For Forge server |
| cat_server_parser | For [CatServer](https://github.com/Luohuayu/CatServer) server |
| bungeecord_parser | For Bungeecord. Please add `-Djline.terminal=jline.UnsupportedTerminal` before `-jar` in the start command for MCDR support. From [here](https://www.spigotmc.org/wiki/start-up-parameters/) |
| waterfall_parser | For Waterfall server |

### encoding

Default: ` `

The encoding format used to encode message to the stdin of the server

Leave it blank for MCDR to auto detect the encoding. 

### decoding

Default: ` `

The decoding format used to decode message from the stdout of the server

Leave it blank for MCDR to auto detect the decoding

### console_command_prefix

Default: `!!`

If any command input to the console is prefixed with with the string below, MCDR will not send this command to server's standard input steam

### enable_rcon

Default: `false`

If the value is `true`, MCDR will start a rcon to the server after server startup, which means plugins can use rcon to send command and get result through rcon from the server

If the value is `false`, MCDR will not start rcon connection to the server

### rcon_address

The address for rcon to connect. For local server (It is already) just keep default value

Default: `127.0.0.1`

### rcon_port

The port for rcon to connect. It should be the same as `rcon.port` in `server.properties` file

Default: `25575`

### rcon_password

The password for of rcon. It should be the same as `rcon.password` in `server.properties` file

Default: `password`

### disable_console_thread

Default: `false`

If set to `true`, the thread that used for console command input will be disabled and you can't control MCDR from the console

Keep it as `false` unless necessary

### download_update

Default: `true`

If the value is `true`, if MCDR detects a newer version it will automatically download it

### debug_mode

Default: `false`

Debug mode switch

Keep it as `false` unless necessary

## Plugin

[Plugin document](https://github.com/Fallen-Breath/MCDReforged/blob/master/doc/plugin.md)

Plugin usage can refer to `plugins/sample_plugin.py`

[Here](https://github.com/MCDReforged-Plugins/PluginCatalogue) is a MCDR plugin collection repository

## Permission

There is a simple built-in permission system in MCDR for plugin maker to use

There are 4 different level of permission:

| Name | Value | Description |
|---|---|---|
| admin | 3 | A group with the highest power to control the MCDR
| helper | 2 | A group of admin's helper
| user | 1 | A group that normal player will be in
| guest | 0 | A group for guest

The permission level of console input is always the highest level `admin`

### Permission File

Permission file `permission.yml` is the config and storage file for the system

- `default_level`: The default permission level a new player will get. Default: `user`
- `admin`: A list of names of players who has the permission level `admin`
- `helper`: A list of names of players who has the permission level `helper`
- `user`: A list of names of players who has the permission level `user`
- `guest`: A list of names of players who has the permission level `guest`

Player name list of permission levels can be filled like this:

```
admin:
- Notch
helper:
- Steve
- Alex
user:
guest:
```

## Command

There several commands to control MCDR. These command can be both input in game chat or in console:

| Command | Short form | Function |
|---|---|---|
| !!MCDR |  | Show help message 
| !!MCDR status |  | show MCDR status
| !!MCDR reload | !!MCDR r | Show reload command help message
| !!MCDR reload plugin | !!MCDR r plg | Reload all **changed** plugins 
| !!MCDR reload config | !!MCDR r cfg | Reload config file
| !!MCDR reload permission | !!MCDR r perm | Reload permission file
| !!MCDR reload all | !!MCDR r all | Reload everything above
| !!MCDR permission | !!MCDR perm | Show permission command help message
| !!MCDR permission list \[\<level\>\] | !!MCDR perm list \[\<level\>\] | List all player's permission. Only list permission level \[\<level\>\] if \[\<level\>\] has set
| !!MCDR permission set \<player\> \<level\> | !!MCDR perm set \<player\> \<level\> | Set the permission level of \<player\> to \<level\>
| !!MCDR permission remove \<player\> | !!MCDR perm remove \<player\> | Remove \<player\> from the permission database
| !!MCDR permission setdefault \<level\> | !!MCDR perm setd \<level\> | Set the default permission level to \<level\>
| !!MCDR plugin list | !!MCDR plg list | List all plugins
| !!MCDR plugin load \<plugin\> | !!MCDR plg load \<plugin\> | Load / Reload a plugin named \<plugin\>
| !!MCDR plugin enable \<plugin\> | !!MCDR plg enable \<plugin\> | Enable a plugin named \<plugin\>
| !!MCDR plugin disable \<plugin\> | !!MCDR plg disable \<plugin\> | Disable a plugin named \<plugin\>
| !!MCDR plugin reloadall | !!MCDR plg ra | Load / Reload / Unloaded every plugins
| !!MCDR plugin checkupdate | !!MCDR plg cu | Check update from Github

Only player with `admin` permission level is allow to execute these command in game chat

And there is a `!!help` command to display registered help messages from plugins

## Notes

- Make sure you add `-Djline.terminal=jline.UnsupportedTerminal` before `-jar` in the start command if your are running a Bungeecord server, or MCDR might not be able to control the standard input stream of the server

