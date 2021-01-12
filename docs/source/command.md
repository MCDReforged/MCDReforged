# Command

Command is the most common way for users to interact with MCDR. MCDR consider all console input and player chat messages from the server as user inputs. For them, MCDR will try to parse the input as a command

Commands can be registered by MCDR itself and by plugins. This page only introduces about commands from MCDR. For plugin registered command, check [todo](todo)

## !!MCDR command

`!!MCDR` commands is the way for users to control MCDR on console, or in game. All of these command requires permission level 3 (admin) to be executed.

Assuming you already have the permission to control MCDR, then you can enter `!!MCDR` to the console or in game chat and you will see the help message of MCDR

### Status display

`!!MCDR status` displayer the status of MCDR. It will display the following contents:

- The version of MCDR
- The state of MCDR
- The state of the server
- The flag that displays if the server has started up
- If the server exists naturally by itself, or the server is stopped / killed by MCDR
- The state of rcon connection
- The amount of loaded plugin

The following status can only be seen by users with permission 4 (owner)

- The PID of the server. Notices that this PID is the pid of the bash program that the server is running in
- Info Queue load. If the server is spamming text the queue might be filled
- The current thread list


### Hot reloads

`!!MCDR reload` commands are the places to hot-reload things. Its short form is `!!MCDR r`.
 
Directly enter command `!!MCDR reload` will show the help message of the hot reload commands

Here's a table of the commands

| Command | Short form | Function |
|---|---|---|
| !!MCDR reload | !!MCDR r | Show reload command help message |
| !!MCDR reload plugin | !!MCDR r plg | Reload all **changed** plugins  |
| !!MCDR reload config | !!MCDR r cfg | Reload config file |
| !!MCDR reload permission | !!MCDR r perm | Reload permission file |
| !!MCDR reload all | !!MCDR r all | Reload everything above |


### Permission management

`!!MCDR permission` commands are used to manipulate player's permission. Its short form is `!!MCDR perm`.
 
Directly enter command `!!MCDR perm` will show the help message of the permission manipulation commands

Here's a table of the commands

| Command | Short form | Function |
|---|---|---|
| !!MCDR permission | !!MCDR perm | Show permission command help message |
| !!MCDR permission list \[\<level\>\] | !!MCDR perm list \[\<level\>\] | List all player's permission. Only list permission level \[\<level\>\] if \[\<level\>\] has set |
| !!MCDR permission set \<player\> \<level\> | !!MCDR perm set \<player\> \<level\> | Set the permission level of \<player\> to \<level\> |
| !!MCDR permission remove \<player\> | !!MCDR perm remove \<player\> | Remove \<player\> from the permission database |
| !!MCDR permission setdefault \<level\> | !!MCDR perm setd \<level\> | Set the default permission level to \<level\> |

The \<player\> argument should be a string indicating the name of the player

The \<level\> argument should be a string or a integer indicating a permission level. It can be a string, the name of the permission, or a integer, the level of the permission

Examples:

- `!!MCDR perm list 4`: List all players with permission level 4 (owner)
- `!!MCDR set Steve admin`: Set the permission level of player Steve to 3 (admin)

Check the page [Permission](/permission.html) for more information about MCDR permission system

### Plugin management

| Command | Short form | Function |
|---|---|---|
| !!MCDR permission | !!MCDR perm | Show permission command help message |
| !!MCDR permission list \[\<level\>\] | !!MCDR perm list \[\<level\>\] | List all player's permission. Only list permission level \[\<level\>\] if \[\<level\>\] has set |
| !!MCDR permission set \<player\> \<level\> | !!MCDR perm set \<player\> \<level\> | Set the permission level of \<player\> to \<level\> |
| !!MCDR permission remove \<player\> | !!MCDR perm remove \<player\> | Remove \<player\> from the permission database |
| !!MCDR permission setdefault \<level\> | !!MCDR perm setd \<level\> | Set the default permission level to \<level\> |
| !!MCDR plugin list | !!MCDR plg list | List all plugins |
| !!MCDR plugin load \<plugin\> | !!MCDR plg load \<plugin\> | Load / Reload a plugin named \<plugin\> |
| !!MCDR plugin enable \<plugin\> | !!MCDR plg enable \<plugin\> | Enable a plugin named \<plugin\> |
| !!MCDR plugin disable \<plugin\> | !!MCDR plg disable \<plugin\> | Disable a plugin named \<plugin\> |
| !!MCDR plugin reloadall | !!MCDR plg ra | Load / Reload / Unloaded every plugins |
| !!MCDR plugin checkupdate | !!MCDR plg cu | Check update from Github |

## !!help command

`!!help` command is place to display the help messages of all command. It works as an index of all commands

The content of this command can be registered by plugins, so a new user can easily browse all available commands that it can access

Any user is allowed to use this command, and MCDR will list all command help messages that the user has enough permission level to see
