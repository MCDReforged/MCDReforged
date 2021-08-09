
Some tips to plugin development
===============================

The following tips are useful to 

Help message
------------

Use ``server.register_help_message()`` to add some necessary tips for your plugin, so the player can use ``!!help`` command to know about your plugin

Of course if your plugin is supposed to only be used by player with enough permission level, specify the *permission* argument when registering

Event listening
---------------

If you don't care about info from non-user source, listen to `User Info event <event.html#user-info>`__ instead of `General Info event <event.html#general-info>`__, which can improve MCDR's performance when the server is spamming with non-user info (e.g. Pasting schematic with Litematica mod) in the console

If you only care about commands from users, instead of listening to `User Info event <event.html#user-info>`__, you can `register a command tree <command.html>`__ to MCDR. It's much more efficient than handling yourself inside `User Info event <event.html#user-info>`__

`MCDR Stop event <event.html#mcdr-stop>`__ allows you to have as many time as you want to save your data. Be carefully, don't enter an endless loop, MCDR is waiting for you to exit

Multi-threading
---------------

If you want to do some tasks in your plugin that might take some time to finished, such as network querying or massive file operation, it's recommended to execute your code into a separated thread instead of directly executing them into your event listener function. Otherwise it might block the pending task execution

For easier use there's a decorator named `new_thread <api.html#new_thread>`__ to help you make your function run in another thread asynchronously

User config, data and log files
-------------------------------

If you want to store some user configure or user data file, it's recommend to store them inside the ``config`` folder rather than store them inside the plugin folder

The reason is that user might have their plugins be placed in another directory or even have multiple MCDR instances to load a same plugin collection directory, by a configure option named `plugin_directories <../configure.html#plugin-directories>`__

If you store your configure or data inside the plugin folder, you can't distinguish which MCDR instance the configuration file belongs to. You can either store them inside the ``config`` folder directly or a inner folder inside the ``config`` folder like ``config/my_plugin/``, so the user data can be dedicated for the MCDR instance that loads your plugin

For logging files, store them inside ``logs/`` folder is a good idea

External packages
-----------------

Some times you plugin needs some external resource files or requires some other ``.py`` codes as libraries. For these, you can place them inside a custom package in the plugin folder

For example, if the plugin folder is ``plugins/``, then you can have the following file structure:

.. code-block::

   plugins/
    ├─ my_plugin/
    │   ├─ __init__.py
    │   ├─ a_useful_library.py
    │   ├─ my_resources.dat
    │   └─ ...
    ├─ MyPlugin.py
    └─ ...

Then your plugin ``MyPlugin.py`` can directly import your library or resource files by ``from my_plugin import a_useful_library``

Don't worry, MCDR has already `appended all plugin directories into the ``sys.path`` <../configure.html#plugin-directories>`__ so import your package inside the plugin folder directly

Misc
----

* The current working directory is the folder where MCDR is in. **DO NOT** change it since that will mess up everything
* For the ``Info`` parameter in `General Info event <event.html#general-info>`__ etc., don't modify it, just use its public methods and read its properties
* If you want to import other plugin, use ``server.get_plugin_instance()`` instead of directly importing, so the plugin instance you get is the same as the one MCDR uses
