# Configure

The configure file of MCDR is `config.yml`. It's located and should be located in the working directory of MCDR.

At startup, MCDR will try to load the configure file. If the configure file is not present, MCDR will generate a default config file and exit. Otherwise, MCDR will load the config file and compare its content with the default configure file. If your configure file has any missing options, MCDR will add default values to the end of your configure file.

The configure file use [YAML](https://en.wikipedia.org/wiki/YAML) format.

You can use command `!!MCDR reload config` or its short form `!!MCDR r cfg` to reload the config file when MCDR is running

## List of options

#### language

The language that MCDR will use to display information

Option type: string

Default value: `en_us`

Available options: `en_us`, `zh_cn`

#### working directory

The working directory of the server. You should probably put all the files related to the server int this directory

Option type: string

Default value: `server`

#### start_command

The console command to launch the server.

Some examples:

- `java -Xms1G -Xmx2G -jar minecraft_server.jar nogui`, if you want to launch a Minecraft server
- `./start.sh`, if you have already written a startup script in the working directory

Option type: string

Default value: `java -Xms1G -Xmx2G -jar minecraft_server.jar nogui`

#### handler

Different Minecraft server has different kind of output, and event different kind of command. Server handlers are the modules to handle between all kind of servers and the interface for MCDR to control the server.

Handler determines the specific way to parse the standard output text of the server, and uses the correct command for server control.

Here is a table of current bulit-in handlers and their suitable server types

| Handler | Compatible server types |
|---|---|
| vanilla_handler | For Vanilla / Carpet / Fabric server |
| beta18_handler | For vanilla server in beta 1.8 version. Maybe it works for other beta versions but it's only tested in beta 1.8.1 |
| bukkit_handler | For Bukkit / Spigot server with Minecraft version below 1.14, and Paper server in all version |
| bukkit_handler_14 | For Bukkit / Spigot server with Minecraft version 1.14 and above |
| forge_handler | For Forge server |
| cat_server_handler | For [CatServer](https://github.com/Luohuayu/CatServer) server |
| bungeecord_handler | For Bungeecord. Please add `-Djline.terminal=jline.UnsupportedTerminal` before `-jar` in the start command for MCDR support. From [here](https://www.spigotmc.org/wiki/start-up-parameters/) |
| waterfall_handler | For Waterfall server |
| basic_handler | The handler that parse nothing and return the raw text from the server. Don't use this unless you want to use MCDR to lanuch non Minecraft related servers |

Option type: string

Default value: `vanilla_handler`

#### encoding / decoding

The encoding format used to encode message to the stdin of the server. 

Leave it blank for MCDR to auto detect the encoding. If it doesn't work (e.g. random characters in game) you needs to manually specify it depends on your os and language

Option type: string or null

Default value: ``

Example options: `utf8`, `gbk`

#### plugin_directories











