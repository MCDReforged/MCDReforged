PluginServerInterface
=====================

Derived from `ServerInterface <ServerInterface.html>`__, PluginServerInterface adds the ability for plugins to control the plugin itself on the basis of ServerInterface

Method
------

Plugin Registry
^^^^^^^^^^^^^^^

register_event_listener
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    def register_event_listener(self, event: Union[PluginEvent, str], callback: Callable, priority: int = 1000) -> None

Register an event listener for the current plugin

Parameter *event*: The id of the event, or a PluginEvent instance. It indicates the target event for the plugin to listen

Parameter *callback*: The callback listener method for the event

Parameter *priority*: The priority of the listener. It will be set to the default value 1000 if it's not specified

register_command
~~~~~~~~~~~~~~~~

.. code-block:: python

    def register_command(self, root_node: Literal) -> None

Register an event listener for the current plugin

Parameter *root_node*: The root node of your command tree. It should be a ``Literal`` node

register_help_message
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    def register_help_message(self, prefix: str, message: Union[Union[str, RTextBase], Dict[str, Union[str, RTextBase]]], permission: int = PermissionLevel.MINIMUM_LEVEL) -> None

Register a help message for the current plugin, which is used in !!help command

Parameter *prefix*: The help command of your plugin. When player click on the displayed message it will suggest this prefix parameter to the player. It's recommend to set it to the entry command of your plugin

Parameter *message*: A neat command description. It can be a str or a RText. Also it can be a dict maps from language to description message

Parameter *permission*: The minimum permission level for the user to see this help message. With default, anyone can see this message

register_translation
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    def register_translation(self, language: str, mapping: Dict[str, str]) -> None

Register a translation mapping for a specific language for the current plugin

Parameter *language*: The language of this translation

Parameter *mapping*: A dict which maps translation keys into translated text

Plugin Utils
^^^^^^^^^^^^

get_self_metadata
~~~~~~~~~~~~~~~~~

.. code-block:: python

    def get_self_metadata(self) -> Metadata

Return the metadata of the plugin itself

get_data_folder
~~~~~~~~~~~~~~~

.. code-block:: python

    def get_data_folder(self) -> str

Return a unified data directory path for the current plugin

The path of the folder will be ``config/plugin_id/`` where ``plugin_id`` is the id of the current plugin

If the directory does not exist, create it

Returns the path to the data directory

Example:

.. code-block:: python

    with open(os.path.join(server.get_data_folder(), 'my_data.txt'), 'w') as file_handler:
        write_some_data(file_handler)

open_bundled_file
~~~~~~~~~~~~~~~~~

.. code-block:: python

    def open_bundled_file(self, related_file_path: str) -> IO[bytes]

Open a file inside the plugin with readonly binary mode

Parameter *related_file_path*: The related file path in your plugin to the file you want to open

Returns a un-decoded bytes file-like object

Raises ``FileNotFoundError`` if the plugin is not a multi file plugin (that is, a solo plugin)

Example:

.. code-block:: python

    with server.open_bundled_file('message.txt') as file_handler:
        message = file_handler.read().decode('utf8')
    server.logger.info('A message from the file: {}'.format(message))

load_config_simple
~~~~~~~~~~~~~~~~~~

.. code-block:: python
    
    def load_config_simple(
			self, file_name: str = 'config.json', default_config: Optional = None, *,
			in_data_folder: bool = True, echo_in_console: bool = True, source_to_reply: Optional[CommandSource] = None, target_class: Optional[Type[SerializableType]] = None
		) -> Union[dict, SerializableType]

A simple method to load a dict or Serializable type config from a json file

Default config is supported. Missing key-values in the loaded config object will be filled using the default config

Parameter *file_name*: The name of the config file

Parameter *default_config*: A dict contains the default config. It's required when the config file is missing, or exception will be risen. If target_class is given and default_config is missing, the default values in target_class will be used when the config file is missing

Parameter *in_data_folder*: If True, the parent directory of file operating is the `data folder <#get-data-folder>`__ of the plugin

Parameter *echo_in_console*: If logging messages in console about config loading

Parameter *source_to_reply*: The `command source <CommandSource.html>`__ for replying logging messages

Parameter *target_class*: A class derived from `Serializable <../api.html#serializable>`__. When specified the loaded config data will be deserialized to a instance of target_class which will be returned as return value

Returns a dict contains the loaded and processed config

Example:

.. code-block:: python

    config = {
        'settingA': 1
        'settingB': 'xyz'
    }
    default_config = config.copy()

    def on_load(server: PluginServerInterface, prev_module):
        global config
        config = server.load_config_simple('my_config.json', default_config)

.. code-block:: python

    class Config(Serializable):
        settingA: int = 1
        settingB: str = 'xyz'

    config: Config

    def on_load(server: PluginServerInterface, prev_module):
        global config
        config = server.load_config_simple(target_class=Config)

Assuming that the plugin id is ``my_plugin``, then the config file will be in ``config/my_plugin/my_config.json``


save_config_simple
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    def save_config_simple(self, config: Union[dict, Serializable], file_name: str = 'config.json', *, in_data_folder: bool = True) -> None

A simple method to save your dict or Serializable type config as a json file

Parameter *config*: The config instance to be saved

Parameter *file_name*: The name of the config file

Parameter *in_data_folder*: If True, the parent directory of file operating is the data folder of the plugin

