
Command
=======

Command is the most common way for users to interact with MCDR. MCDR consider all console input and player chat messages from the server as user inputs. For them, MCDR will try to parse the input as a command

Commands can be registered by MCDR itself and by plugins. This page only introduces about commands from MCDR. For plugin registered command, check `here <plugin_dev/command>`__

!!MCDR command
--------------

``!!MCDR`` commands is the way for users to control MCDR on console, or in game. All of these command requires permission level 3 (admin) to be executed.

Assuming you already have the permission to control MCDR, then you can enter ``!!MCDR`` to the console or in game chat and you will see the help message of MCDR

Status display
^^^^^^^^^^^^^^

``!!MCDR status`` displayer the status of MCDR. It will display the following contents:


* The version of MCDR
* The state of MCDR
* The state of the server
* The flag that displays if the server has started up
* If the server exists naturally by itself, or the server is stopped / killed by MCDR
* The state of rcon connection
* The amount of loaded plugin

The following status can only be seen by users with permission 4 (owner)


* The PID of the server. Notices that this PID is the pid of the bash program that the server is running in
* Info Queue load. If the server is spamming text the queue might be filled
* The current thread list

Hot reloads
^^^^^^^^^^^

``!!MCDR reload`` commands are the places to hot-reload things. Its short form is ``!!MCDR r``. Directly enter command ``!!MCDR reload`` will show the help message of the hot reload commands

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
^^^^^^^^^^^^^^^^^^^^^

``!!MCDR permission`` commands are used to manipulate player's permission. Its short form is ``!!MCDR perm``. Directly enter command ``!!MCDR perm`` will show the help message of the permission manipulation commands

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

Check the page `Permission <permission.md>`__ for more information about MCDR permission system

Plugin management
^^^^^^^^^^^^^^^^^

``!!MCDR plugin`` is the place for user to manipulate plugins. Its short form is ``!!MCDR plg``. Directly enter command ``!!MCDR plg`` will show the help message of the commands

Here's a table of the commands

.. list-table::
   :header-rows: 1

   * - Command
     - Short form
     - Function
   * - !!MCDR plugin list
     - !!MCDR plg list
     - List all plugins
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

Update checking
^^^^^^^^^^^^^^^

``!!MCDR checkupdate``, or ``!!MCDR cu``. Use it to manually check update from github

It will try to get the latest release version in github, and check if it's newer than the current version. If it is, it will show the update logs from the github release

!!help command
--------------

``!!help`` command is place to display the help messages of all commands. It works as an index of all commands

The content of this command can be registered by plugins, so a new user can easily browse all available commands that it can access

Any user is allowed to use this command, and MCDR will list all command help messages that the user has enough permission level to see

Without any plugin, you may see the result below after you entered the ``!!help`` command

.. code-block::

   MCDR command help message list
   !!MCDR: MCDR control command
   !!help: MCDR command help messages
