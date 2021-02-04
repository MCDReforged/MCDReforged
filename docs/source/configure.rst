
Configure
=========

The configure file of MCDR is ``config.yml``. It's located and should be located in the working directory of MCDR

At startup, MCDR will try to load the configure file. If the configure file is not present, MCDR will generate a default config file and exit. Otherwise, MCDR will load the config file and compare its content with the default configure file. If your configure file has any missing options, MCDR will add default values to the end of your configure file

The configure file use `YAML <https://en.wikipedia.org/wiki/YAML>`__ format

You can use command ``!!MCDR reload config`` or its short form ``!!MCDR r cfg`` to reload the config file when MCDR is running. Check the `here <command.html#hot-reloads>`__ for more detail about hot reloads

List of options
---------------

Basic
^^^^^

language
~~~~~~~~

The language that MCDR will use to display information


* Option type: string
* Default value: ``en_us``
* Available options: ``en_us``\ , ``zh_cn``

working_directory
~~~~~~~~~~~~~~~~~

The working directory of the server. You should probably put all the files related to the server int this directory


* Option type: string
* Default value: ``server``

start_command
~~~~~~~~~~~~~

The console command to launch the server

Some examples:


* ``java -Xms1G -Xmx2G -jar minecraft_server.jar nogui``\ , if you want to launch a Minecraft server
* 
  ``./start.sh``\ , if you have already written a startup script in the working directory

* 
  Option type: string

* Default value: ``java -Xms1G -Xmx2G -jar minecraft_server.jar nogui``

handler
~~~~~~~

Different Minecraft server has different kind of output, and event different kind of command. Server handlers are the modules to handle between all kind of servers and the interface for MCDR to control the server

Handler determines the specific way to parse the standard output text of the server, and uses the correct command for server control

Here is a table of current built-in handlers and their suitable server types

.. list-table::
   :header-rows: 1

   * - Handler
     - Compatible server types
   * - vanilla_handler
     - For Vanilla / Carpet / Fabric server
   * - beta18_handler
     - For vanilla server in beta 1.8 version. Maybe it works for other beta versions but it's only tested in beta 1.8.1.
   * - bukkit_handler
     - For Bukkit / Spigot server with Minecraft version below 1.14, and Paper server in all version.
   * - bukkit_handler_14
     - For Bukkit / Spigot server with Minecraft version 1.14 and above
   * - forge_handler
     - For Forge server
   * - cat_server_handler
     - For `CatServer <https://github.com/Luohuayu/CatServer>`__ server
   * - bungeecord_handler
     - For Bungeecord. Please add ``-Djline.terminal=jline.UnsupportedTerminal`` before ``-jar`` in the start command for MCDR support. From `here <https://www.spigotmc.org/wiki/start-up-parameters/>`__
   * - waterfall_handler
     - For Waterfall server
   * - basic_handler
     - The handler that parse nothing and return the raw text from the server. Don't use this unless you want to use MCDR to lanuch non Minecraft related servers.



* Option type: string
* Default value: ``vanilla_handler``

encoding / decoding
~~~~~~~~~~~~~~~~~~~

The encoding format used to encode message to the stdin of the server. 

Leave it blank for MCDR to auto detect the encoding. If it doesn't work (e.g. random characters in game) you needs to manually specify it depends on your os and language


* Option type: string or null
* Default value: `` ``
* Examples: ``utf8``\ , ``gbk``

plugin_directories
~~~~~~~~~~~~~~~~~~

The list of directory path where MCDR will search for plugin to load

MCDR also **adds these directories into ``sys.path``** so plugins can import packages inside plugin folders directly


* Option type: a list of string
* Default value: 

.. code-block:: yaml

   plugin_directories:
   - plugins


* Example:

.. code-block:: yaml

   plugin_directories:
   - plugins
   - path/to/my/plugin/directory
   - another/plugin/directory

rcon
~~~~

The setting for `rcon <https://wiki.vg/RCON>`__. If rcon is enabled, MCDR will start a rcon client to connect to the server after server rcon has started up. Then plugins can use rcon to query command from the server

rcon.enable
"""""""""""

The switch of rcon


* Option type: boolean
* Default value: ``false``

rcon.address
""""""""""""

The address of the rcon server


* Option type: string
* Default value: ``127.0.0.1``

rcon.port
"""""""""

The port of the rcon server


* Option type: integer
* Default value: ``25575``

rcon.password
"""""""""""""

The password to connect to the rcon server


* Option type: string
* Default value: ``password``

check_update
~~~~~~~~~~~~

If set to true, MCDR will detect if there's a new version every 24h


* Option type: boolean
* Default value: ``true``

Advance
^^^^^^^

Configure options for advance users

disable_console_thread
~~~~~~~~~~~~~~~~~~~~~~

When set to true, MCDR will not start the console thread for handling console command input

Don't change it to true unless you know what you are doing


* Option type: boolean
* Default value: ``false``

disable_console_color
~~~~~~~~~~~~~~~~~~~~~

When set to true, MCDR will removed all console font formatter codes in before any message gets printed onto the console


* Option type: boolean
* Default value: ``false``

custom_handlers
~~~~~~~~~~~~~~~

A list of custom `server handler <customize/handler.html>`__ classes. The classed need to be subclasses of ``AbstractServerHandler``

Then you can use the name of your handler in the `handler <#handler>`__ option above to use your handler

The name of a handler is defined in the get_name method


* Option type: a list of string, or null
* Default value: 

.. code-block:: yaml

   custom_handlers:


* Example:

.. code-block:: yaml

   custom_handlers:
   - my.customize.handler.MyHandler

In this example the custom handler package path is ``my.custom.handler`` and the class is name ``MyHandler``

custom_info_reactors
~~~~~~~~~~~~~~~~~~~~

A list of custom `info reactor <customize/reactor.html>`__ classes to handle the info instance. The classed need to be subclasses of ``AbstractInfoReactor``

All custom info reactors will be registered to the reactor list to process information from the server


* Option type: a list of string, or null
* Default value: 

.. code-block:: yaml

   custom_info_reactors:


* Example:

.. code-block:: yaml

   custom_info_reactors:
   - my.customize.reactor.MyInfoReactor

In this example the custom reactor package path is ``my.custom.reactor`` and the class name is ``MyInfoReactor``

debug
~~~~~

Debug logging switches. Set ``all`` to true to enable all debug logging, or set the specific option to enable specific debug logging


* Default value: 

.. code-block:: yaml

   debug:
     all: false
     mcdr: false
     handler: false
     reactor: false
     plugin: false
     permission: false
     command: false
