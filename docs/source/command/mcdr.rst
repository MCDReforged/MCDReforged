
!!MCDR command
==============

``!!MCDR`` commands is the way for users to control MCDR on console, or in game. All of these following commands require permission level 3 (admin) to be executed unless extra nodes exist

Assuming you already have the permission to control MCDR, then you can enter ``!!MCDR`` to the console or in game chat and you will see the help message of MCDR

If you only have permission level 1 (user) or above, then the version of MCDR will be displayed via ``!!MCDR`` command

Status display
--------------

``!!MCDR status`` displays the status of MCDR. It will display the following contents:


* The version of MCDR
* The state of MCDR
* The state of the server
* The flag that displays if the server has started up
* If MCDR will exit after the server stop, aka if the server exists naturally by itself, or the server is stopped / killed by MCDR
* The state of rcon connection
* The amount of loaded plugin

The following status can only be seen by users with permission 4 (owner)

* The PID of the server. Notices that this PID is the pid of the bash program that the server is running in. Additionally the pid tree will be showed so you can have a look at the process structure of your server
* Info queue load. If the server is spamming text the queue might be filled
* The current thread list

Hot reloads
-----------

``!!MCDR reload`` sub-commands are the places to hot-reload things. Its short form is ``!!MCDR r``. Directly enter command ``!!MCDR reload`` will show the help message of the hot reload commands

Here's a table of the commands

.. list-table::
   :header-rows: 1

   * - Command
     - Short form
     - Function
   * - !!MCDR reload
     - !!MCDR r
     - Show reload command help message
   * - !!MCDR reload plugin
     - !!MCDR r plg
     - Reload all **changed** plugins
   * - !!MCDR reload config
     - !!MCDR r cfg
     - Reload config file
   * - !!MCDR reload permission
     - !!MCDR r perm
     - Reload permission file
   * - !!MCDR reload all
     - !!MCDR r all
     - Reload everything above


Permission management
---------------------

``!!MCDR permission`` sub-commands are used to manipulate player's permission. Its short form is ``!!MCDR perm``. Directly enter command ``!!MCDR perm`` will show the help message of the permission manipulation commands

Here's a table of the commands

.. list-table::
   :header-rows: 1

   * - Command
     - Short form
     - Function
   * - !!MCDR permission
     - !!MCDR perm
     - Show permission command help message
   * - !!MCDR permission list [<level>]
     - !!MCDR perm list [<level>]
     - List all player's permission. Only list permission level [<level>] if [<level>] has set
   * - !!MCDR permission set <player> <level>
     - !!MCDR perm set <player> <level>
     - Set the permission level of <player> to <level>
   * - !!MCDR permission query <player>
     - !!MCDR perm q [<player>]
     - Query the permission level of <player>. If <player> is not set, query the permission level of the command sender
   * - !!MCDR permission remove <player>
     - !!MCDR perm remove <player>
     - Remove <player> from the permission database
   * - !!MCDR permission setdefault <level>
     - !!MCDR perm setd <level>
     - Set the default permission level to <level>


The <player> argument should be a string indicating the name of the player

The <level> argument should be a string or a integer indicating a permission level. It can be a string, the name of the permission, or a integer, the level of the permission

Examples:


* ``!!MCDR perm list 4``: List all players with permission level 4 (owner)
* ``!!MCDR permission set Steve admin``: Set the permission level of player Steve to 3 (admin)
* ``!!MCDR permission q Steve``: Query the permission level of player Steve. The value should be 3 (admin)

Check the :doc:`/permission` document for more information about MCDR permission system

Plugin management
-----------------

``!!MCDR plugin`` is the place for user to manipulate plugins. Its short form is ``!!MCDR plg``.
Directly enter command ``!!MCDR plg`` will show the help message of the commands

Local plugin management
^^^^^^^^^^^^^^^^^^^^^^^

Here's the commands that can be used to manipulate local installed plugins

.. list-table::
   :header-rows: 1

   * - Command
     - Short form
     - Function
   * - !!MCDR plugin list
     - !!MCDR plg list
     - List all installed plugins
   * - !!MCDR plugin info <plugin_id>
     - !!MCDR plg info <plugin_id>
     - Display the information of the plugin with id <plugin_id>
   * - !!MCDR plugin load <file_name>
     - !!MCDR plg load <file_name>
     - Load a plugin with file path <file_name>
   * - !!MCDR plugin enable <file_name>
     - !!MCDR plg enable <file_name>
     - Enable a plugin with file path <file_name>
   * - !!MCDR plugin reload <plugin_id>
     - !!MCDR plg reload <plugin_id>
     - Reload a plugin with id <plugin_id>
   * - !!MCDR plugin unload <plugin_id>
     - !!MCDR plg unload <plugin_id>
     - Unload a plugin with id <plugin_id>
   * - !!MCDR plugin disable <plugin_id>
     - !!MCDR plg disable <plugin_id>
     - Disable a plugin with id <plugin_id>
   * - !!MCDR plugin reloadall
     - !!MCDR plg ra
     - Load / Reload / Unloaded **all** not disabled plugins

The <plugin_id> argument is a string of the unique plugin id of the plugin you want to manipulate

The <file_name> argument is a string of the file name of the plugin file you want to load or enable

Example:

Let's say there's is a loaded plugin with id ``my_plugin`` and a disabled plugin in path ``plugins/another_plugin.py.disabled`` with id ``another_plugin``

Then you can do the following commands

.. code-block::

    !!MCDR plg info my_plugin
    !!MCDR plugin reload my_plugin
    !!MCDR plugin enable another_plugin.py.disabled
    !!MCDR plugin unload another_plugin
    !!MCDR plugin load another_plugin.py

These commands do the following things:


#. Query the information about the plugin with id ``my_plugin``
#. Reload the plugin with id ``my_plugin``
#. Enable and load the disabled plugin with file name ``another_plugin.py.disabled``. It has plugin id ``another_plugin``
#. Unload the plugin with id ``another_plugin``
#. Reload the plugin with file name ``another_plugin.py``. Note that since this plugin is not loaded, you can only use file name to specify it


Plugin catalogue access
^^^^^^^^^^^^^^^^^^^^^^^

The following commands provide operations based on the `https://mcdreforged.com/en/plugins <plugin catalogue>`__

browse
~~~~~~

Browse plugin catalogue. List with keyword or show details of plugin with given id

.. code-block:: text

    !!MCDR plugin browse [<keyword>] [(-i|--id) <plugin_id>]

Arguments:

- ``<keyword>``: The keyword for filtering
- ``<plugin_id>``: The plugin ID to show details of

Example usages:

- ``!!MCDR plugin browse``: List all plugins in the plugin catalogue
- ``!!MCDR plugin browse backup``: List plugins with keyword ``backup`` in the plugin catalogue
- ``!!MCDR plugin browse -i my_plugin``: Show details of plugin with ID ``my_plugin`` in the plugin catalogue

install
~~~~~~~

Install plugins that satisfy the given specifier(s)

.. code-block:: text

    !!MCDR plugin install <specifier> [(-t|--target) <target>] [-U|--upgrade] [-y|--yes|--confirm] [--dry-run] [--no-dependencies] [(-r|--requirement) <requirement_file>] ...

Arguments:

- ``<specifier>``: A plugin specifier that describes the plugins to be installed, can be provided for multiple times

    Format: ``${id}${requirement}``. The requirement syntax can be found :ref:`here <plugin_dev/metadata:dependencies>`.
    Examples:

    .. code-block:: text

        my_plugin
        my_plugin<1
        my_plugin>=1.0
        my_plugin^=2.0.1

    Additionally, if the requirement uses ``==`` to pin the plugin version, you can append a hash validator the end of the specifier string,
    to ensure the hash of the to-be-installed plugin file is expected

    .. code-block:: text

        my_plugin==3.0.0@0ec1e048c6
        my_plugin==3.0.0@0ec1e048c6a1737cce639ddc912d13870705fa109e2009321c64193fbc2e4e35
        my_plugin==3.0.0@sha256:0ec1e048c6a1737cce63
        my_plugin==3.0.0@sha256:0ec1e048c6a1737cce639ddc912d13870705fa109e2009321c64193fbc2e4e35

    With a hash validator, the specifier format now becomes ``${id}${requirement}@${hash_validator}``

    -   The ``hash_validator`` part can be ``${hash_method}:${hash_value}``, or just ``${hash_value}`` and use sha256
    -   The ``hash_method`` support ``sha256`` only
    -   The ``hash_value`` should be a hex string in length [10, 64]. It should be a prefix of the expected sha256 value

- ``<target>``: The plugin directory to install the plugins into. The default value is the first path in the :ref:`configuration:plugin_directories` list in MCDR config

    .. note::

        This argument only affects newly installed plugins

        For already existing plugins, their target installation directory will always be where the existing plugin is

- ``-U``, ``--upgrade``: An optional flag suggesting that if given plugin is already installed, then it will be upgrade if possible
- ``-y``, ``--yes``, ``--confirm``: An optional flag to skip the installation confirmation step
- ``--dry-run``: An optional flag for test run. If provided, no actual installation will be performed
- ``--no-dependencies``: An optional flag to ignore all dependencies relationships during plugin resolution. No indirect depended plugin and python packages will be installed
- ``-r``, ``--requirement``: Path to a requirement text file, where each line is a plugin specifier. Empty or #-prefixing lines will be ignored. Just like what ``pip install -r`` does

Example usages:

- ``!!MCDR plugin install my_plugin``: Install a plugin with ID ``my_plugin``, using the latest compatible version
- ``!!MCDR plugin install my_plugin<1.3``: Install a plugin with ID ``my_plugin``, using the latest compatible version, and the version should be less than ``1.3``
- ``!!MCDR plugin install my_plugin<1.3 another_plugin==1.0.0``: On the basis of the above example, install ``another_plugin`` with exact version ``1.0.0`` as well
- ``!!MCDR plugin install my_plugin==1.3@sha256:134b44beec``: Install ``my_plugin`` with version ``1.3``, and ensure the sha256 of the plugin file starts with ``134b44beec``
- ``!!MCDR plugin install -U my_plugin``: Install plugin ``my_plugin`` if it's not installed, or upgrade ``my_plugin`` to the latest compatible version
- ``!!MCDR plugin install -U -y *``: Upgrade all installed plugins to their latest compatible version. Confirmation check is skipped


Example output for a complete plugin installation (Note that ``my_plugin`` does not actually exist):

.. code-block:: text

    > !!MCDR plg install my_plugin
    [MCDR] [21:01:31] [PIM/INFO]: Resolving dependencies ...
    [MCDR] [21:01:31] [PIM/INFO]: Plugins to install (new 1, change 0, total 1):
    [MCDR] [21:01:31] [PIM/INFO]:
    [MCDR] [21:01:31] [PIM/INFO]:     my_plugin: N/A -> 1.2.0
    [MCDR] [21:01:31] [PIM/INFO]:
    [MCDR] [21:01:31] [PIM/INFO]: Python packages to install (2x):
    [MCDR] [21:01:31] [PIM/INFO]:
    [MCDR] [21:01:31] [PIM/INFO]:     foobar (request by my_plugin@1.2.0)
    [MCDR] [21:01:31] [PIM/INFO]:     bazlib (request by my_plugin@1.2.0)
    [MCDR] [21:01:31] [PIM/INFO]:
    [MCDR] [21:01:31] [PIM/INFO]: Enter !!MCDR confirm to confirm installation, or !!MCDR abort to abort
    > !!MCDR confirm
    [MCDR] [21:01:34] [PIM/INFO]: Installing 1 required python packages
    Example pip output ...
    Successfully installed foobar-1.9.4 bazlib-0.24.0
    [MCDR] [21:01:43] [PIM/INFO]: Downloading and installing 1 plugins
    [MCDR] [21:01:43] [PIM/INFO]: Downloading my_plugin@1.2.0: plugins/MyPlugin-v1.1.1.mcdr (example-sha256-hash)
    [MCDR] [21:01:45] [PIM/INFO]: Installing my_plugin@1.2.0 to plugins/MyPlugin-v1.1.1.mcdr
    [MCDR] [21:01:45] [PIM/INFO]: Installed 1 plugins, reloading MCDR
    [MCDR] [21:01:45] [PIM/INFO]: Plugin my_plugin@1.2.0 loaded
    [MCDR] [21:01:46] [PIM/INFO]: Installation done


checkupdate
~~~~~~~~~~~

Check if given plugins have updates

.. code-block:: text

    !!MCDR plugin (checkupdate|cu) [<plugin_id> ...]

Arguments:

- ``<plugin_id>``: ID of the plugin to check update for. Can be provided for multiple times. If not given, check update for all plugins

Example usages:

- ``!!MCDR plugin checkupdate``: Check update for **all** installed plugins
- ``!!MCDR plugin cu my_plugin another_plugin``: Check update for plugin ``my_plugin`` and ``another_plugin``

refreshmeta
~~~~~~~~~~~

Perform a re-fetch for the plugin catalogue meta cache

.. code-block:: text

    !!MCDR plugin refreshmeta

freeze
~~~~~~

Print a plugin freeze result, similar to ``pip freeze``

By default, only :ref:`packed plugins <plugin_dev/plugin_format:Packed Plugin>` will be shown,
since only packed plugins can be installed from the ``!!MCDR plugin install`` command

.. code-block:: text

    !!MCDR plg freeze [-a|--all] [--no-hash] [(-o|--output) <output_file>]

Arguments:

- ``-a``, ``-all``: Include all user installed plugins, including those non packed plugins
- ``--no-hash``: Exclude the hash prefix
- ``-o``, ``--output``: Write the freeze output to the given file.
  The output file can be used as the requirement file in the ``!!MCDR plugin install -r <requirement_file>`` command

Preference settings
-------------------

``!!MCDR preference`` sub-commands are used to control the preference of MCDR. It only requires permission level 1 (user) to operate

Here's a table of the commands

.. list-table::
   :header-rows: 1

   * - Command
     - Short form
     - Function
   * - !!MCDR preference
     - !!MCDR pref
     - Show preference command help message
   * - !!MCDR preference list
     - !!MCDR pref list
     - Display the preference list
   * - !!MCDR preference <pref_name>
     - !!MCDR pref <pref_name>
     - Display the details of preference <pref_name>
   * - !!MCDR preference <pref_name> set <value>
     - !!MCDR pref <pref_name> set <value>
     - Set the value of preference <pref_name> to <value>
   * - !!MCDR preference <pref_name> reset
     - !!MCDR pref <pref_name> reset
     - Reset preference <pref_name> to the default value

See :doc:`here </preference>` for more information about MCDR preference

Examples:

* ``!!MCDR pref set language zh_cn``: Set the value of preference ``language`` to ``zh_cn``

Check update
------------

``!!MCDR checkupdate``, or ``!!MCDR cu``. Use it to manually check update from github

It will try to get the latest release version in github, and check if it's newer than the current version. If it is, it will show the update logs from the github release

Server Control
--------------

``!!MCDR server`` sub-commands are used control the daemonized server

Here's a table of the commands

.. list-table::
   :header-rows: 1

   * - Command
     - Function
   * - !!MCDR server
     - Show server control command help message
   * - !!MCDR server start
     - Start the server
   * - !!MCDR server stop
     - Stop the server, but keep MCDR running
   * - !!MCDR server stop_exit
     - Stop the server and exit MCDR
   * - !!MCDR server exit
     - Exit MCDR. The server should already be stopped
   * - !!MCDR server restart
     - Restart the server
   * - !!MCDR server kill
     - Kill the server, and all of its child processes

These commands are also parts of the :doc:`ServerInterface API </code_references/ServerInterface>`

Debug
-----

``!!MCDR debug`` contains serval utilities for debugging MCDR or MCDR plugins.
They are mostly designed for developers, so you can skip this if you are a MCDR user

Thread Dump
^^^^^^^^^^^

Dump stack trace information of given threads. A easy way to figure out what are your threads doing

You can use ``#all`` as the thread name to dump all threads

Format::

    !!MCDR debug thread_dump [<thread_name>] [(-o|--output) <output_file>] [--name-only]

Arguments:

- ``thread_name``: Optional argument, the name of the thread to dump. If it's not provided, or its value is ``#all``, then all threads will be dumped
- ``--name-only``: Show thread names only. Do not output thread stacks
- ``-o``, ``--output``: Write the thread dump output to the given file for further inspection

Translation Test
^^^^^^^^^^^^^^^^

Query translation results by translation key, or dump all translations within given path

Format::

    !!MCDR debug translation get <translation_key>
    !!MCDR debug translation dump <json_path> [(-o|--output) <output_file>]

Arguments:

- ``-o``, ``--output``: Write the translation dump output to the given file for further inspection

Examples::

    !!MCDR debug translation get one.of.my.translation.key
    !!MCDR debug translation get server_interface.load_config_simple.succeed
    !!MCDR debug translation dump .
    !!MCDR debug translation dump mcdr_server -o mcdr_translation_dump.json
    !!MCDR debug translation dump mcdr_server.on_server_stop

Command Tree Display
^^^^^^^^^^^^^^^^^^^^

Dump command trees with :meth:`~mcdreforged.command.builder.nodes.basic.AbstractNode.print_tree` method

You can filter out command trees to be dumped with plugin id or root node name

Format::

    !!MCDR debug command_dump all [(-o|--output) <output_file>]
    !!MCDR debug command_dump plugin <plugin_id> [(-o|--output) <output_file>]
    !!MCDR debug command_dump node <literal_name> [(-o|--output) <output_file>]

Arguments:

- ``-o``, ``--output``: Write the command dump output to the given file for further inspection

Examples::

    !!MCDR debug command_dump all -o mcdr_command_dump.txt
    !!MCDR debug command_dump plugin my_plugin
    !!MCDR debug command_dump node !!MyCommand

