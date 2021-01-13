# Plugin Event

Plugin events are the most important way for plugins to interact with the server and the console

When the server has trigger a specific event, it will list out all event listeners that have registered to this event, then MCDR will invoke the callback function of the listener with the given arguments

### MCDR Event List

#### General Info

- Event id: mcdr.general_info
- Callback arguments: ServerInterface, Info
- Default function name: on_info

#### User Info

- Event id: mcdr.user_info
- Callback arguments: ServerInterface, Info
- Default function name: on_user_info

#### Server Start

- Event id: mcdr.server_start
- Callback arguments: ServerInterface
- Default function name: on_server_start

#### Server Startup

- Event id: mcdr.server_startup
- Callback arguments: ServerInterface
- Default function name: on_server_startup

#### Server Stop

- Event id: mcdr.server_stop
- Callback arguments: ServerInterface, server_return_code
- Default function name: on_server_stop

#### MCDR Start

- Event id: mcdr.mcdr_start
- Callback arguments: ServerInterface
- Default function name: on_mcdr_start

#### MCDR Stop

- Event id: mcdr.mcdr_stop
- Callback arguments: ServerInterface
- Default function name: on_mcdr_stop

#### Player Joined

- Event id: mcdr.player_joined
- Callback arguments: ServerInterface, player_name, Info
- Default function name: 

#### Player Left

- Event id: mcdr.player_left
- Callback arguments: ServerInterface, player_name
- Default function name: 

#### Plugin Load

- Event id: mcdr.plugin_loaded
- Callback arguments: ServerInterface, prev_plugin_module
- Default function name: on_load

#### Plugin Unload

- Event id: mcdr.plugin_unloaded
- Callback arguments: ServerInterface
- Default function name: on_unload

#### Plugin Removed

- Event id: mcdr.plugin_removed
- Callback arguments: ServerInterface
- Default function name: on_removed

### Custom Event
