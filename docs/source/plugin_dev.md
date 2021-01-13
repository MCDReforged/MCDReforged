# Plugin Development

## What is a MCDR plugin

An MCDR plugin is a python source file with `.py` file extension located in plugin directories. The list of the plugin directory can is defined inside the [configure file](configure.html#plugin_directories)

At start up, MCDR will automatically load every plugin inside this folder

There is a sample plugin named `SamplePlugin.py` in the `plugins/` folder in source and you can check its content for reference

## Quick Start

Open one of the plugin directories of MCDR, create a file named `HelloWorld.py`

```bash
cd my_plugin_folder
touch HelloWorld.py
```

open it and enter these code

```python
PLUGIN_METADATA = {
    'id': 'hello_world',
    'version': '1.0.0',
    'name': 'My Hello World Plugin'
}


def on_load(server, old):
    server.logger.info('Hello world!')

```

Return to MCDR console, enter `!!MCDR reload plugin`, and you should see the hello world message from your plugin

```
[TaskExecutor/INFO] [My Hello World Plugin]: Hello world!
```

Great, you have successfully created your first plugin

## Metadata

The meta data field provides the basic information of the plugin. As you can see in the [Quick Start](#Quick-Start) section above, meta data is declared in the global scope. It's a dict contains several key-value with the name `PLUGIN_METADATA`

Here's a metadata field with all possible key-values

```python
PLUGIN_METADATA = {
	'id': 'my_plugin_id',
	'version': '1.0.0',
	'name': 'My Plugin',  # RText is allowed
	'description': 'A plugin to do something cool',  # RText is allowed
	'author': 'myself',
	'link': 'https://github.com',
	'dependencies': {
		'mcdreforged': '>=1.0.0',
		'an_important_api': '*'
	}
}
```

If a plugin doesn't not declare the meta data field, a warning will arise in the console and the fallback values will be used

### id

Id, or plugin id, is the identity string of your plugin. It should consist of lowercase letters, numbers and underscores with a length of 1 to 64

Here's some available plugin ids:

- my_plugin
- anotherhelper123
- \_\_a_cool_plugin__

But the following ids are not allowed:

- MyPlugin
- another-helper-123
- a cool plugin

MCDR uses plugin id to distinguish between different plugins and check the dependencies. All loaded plugin in MCDR contain different plugin ids. If a newly loaded plugin has a plugin id exactly the same with an existed plugin, the new plugin will fail to load

Choose your plugin id wisely. It's highly suggested to keep your plugin id not changed after release your plugin

- Field key: `id`
- Value type: str
- Fallback value: the file name without the `.py` extension

### version

The version value indicates the version of your value. It's mostly in [semver](https://semver.org/) format but it has less restriction such as you can have the core version with any length

Here's some available version:

- 1.0.0
- 2.0
- 1.2.3-pre4
- 1.8.9-rc.8
- 1.14.1-beta.4+build.54

Following [semver](https://semver.org/) format for you version string is a good idea. It's easier to maintain and for people to understand

- Field key: `version`
- Value type: str
- Fallback value: `0.0.0`

### name

The name of your plugin. Give your plugin with a nice name with any kinds of characters. RText is allowed here

Try not to make the name too long. For more details of your plugin, you can put them into the `description`

- Field key: `name`
- Value type: str or RTextBase
- Fallback value: The plugin id

### description

The description of you plugin. Put the details of your plugin here. Rtext is allowed too

This field is optional, you can just ignore it if you are lazy

- Field key: `description`
- Value type: str or RTextBase
- Fallback value: None

### author

The authors of the plugins. If there's only a single author, you can also use a string instead of a list of string

This field is optional, you can just ignore it if you are lazy

- Field key: `author`
- Value type: str or List\[str]
- Fallback value: None

### link

The link of your project. You can put a link to the github repository of your plugin here. It should be an available url

This field is optional, you can just ignore it if you are lazy

- Field key: `link`
- Value type: str
- Fallback value: None

### dependencies

A dict of dependencies you plugin relies on. It's a dict contains several key-value pairs. The key is the id of the plugin that your plugin is relies on, and the value is the version requirement of the plugin that your plugin is relies on

If your plugin has requirement to the version of MCDR, use `mcdreforged` as the plugin id

A version requirement is a string than contains several criterions of the version. Criterions are divided by space character, each criterion is made up of an operator and a base version string. Wildcard is allowed when describing the base version

List of the operators:

| Operator | Example Requirement | Explanation | Accepted Examples | Unaccepted Examples |
| --- | --- | --- | --- | --- |
| \>= | \>=1.2.3 | The target version should be equal to or newer than 1.2.3 | 1.2.3, 1.3.0 | 1.2.0 |
| \> | \>1.2.3 | The target version should be newer than 1.2.3 | 1.2.4, 1.3.0 | 1.2.0, 1.2.3 |
| <= | <=1.2.3 | The target version should be equal to or older than 1.2.3 | 1.2.3, 1.1.0 | 1.2.4, 2.0.0 |
| < | <1.2.3 | The target version should be older than 1.2.3 | 1.1.0 | 1.2.3, 1.5 |
| = | =1.2.3 | The target version should equal to 1.2.3 | 1.2.3 | 1.2, 1.2.4 |
|   | 1.2.3 | If the operator is not specified, `=` is used as default. In this case the target version should equal to 1.2.3 | 1.2.3 | 1.2, 1.2.4 |
| ^ | ^1.2.3 | The target version should be equal to or newer than 1.2.3, and the first version segment of the target version should be equal to the base version | 1.2.3, 1.2.4, 1.4.4 | 1.0.0, 2.0.0 |
| ~ | ~1.2.3 | The target version should be equal to or newer than 1.2.3, and the first and the second version segment of the target version should be equal to the base version | 1.2.3, 1.2.4 | 1.0.0, 1.4.4, 2.0.0 |

Check [here](https://docs.npmjs.com/about-semantic-versioning) for more detail to the version requirement

If there are multiple declared criterions, the target version is accepted only when it's accepted by all criterions

Here a dependencies example:

```python
'dependencies': {
    'mcdreforged': '>=1.0.0 <2.0',
    'my_library': '>=1.0.0',
    'an_important_api': '*',
    'another_api': '1.0.*'
}
```

MCDR will make sure only when all dependency requirements are satisfied your plugin will get loaded successfully. Missing dependency, dependency version not match or dependency loop will result in a dependency check failure

This field is optional, you can just ignore it if your plugin doesn't have any dependency

- Field key: `dependencies`
- Value type: Dict\[str, str]
- Fallback value: None

## Event

Events are the most important way for plugins to interact with the server and the console

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

## Custom Event

## Life Cycle

Knowing the whole lifecycle of the plugin can help you understand more about MCDR plugins

## Registry

### Event listeners

There are several ways to register an event listener for you plugin. You can either 

### Command

Rather than manually parsing `info.content` inside user info event callback like `on_user_info`, MCDR provides a command system for plugins to register their commands

### Help message
