
Configuration
=============

The configuration file of MCDR is ``config.yml``. It's located and should be located in the working directory of MCDR

At startup, MCDR will try to load the configuration file. If the configuration file is not present, MCDR will generate a default config file and exit. Otherwise, MCDR will load the config file and compare its content with the default configuration file. If your configuration file has any missing options, MCDR will add default values to the end of your configuration file

The configuration file use `YAML <https://en.wikipedia.org/wiki/YAML>`__ format

You can use command ``!!MCDR reload config`` or its short form ``!!MCDR r cfg`` to reload the config file when MCDR is running

.. seealso::

    :ref:`command:Hot reloads` command, for more detail about hot reloads

List of options
---------------

Basic
^^^^^

language
~~~~~~~~

The language that MCDR will use to display information


* Option type: string
* Default value: ``en_us``
* Available options: ``en_us``, ``zh_cn``

working_directory
~~~~~~~~~~~~~~~~~

The working directory of the server. You should probably put all the files related to the server int this directory


* Option type: string
* Default value: ``server``

start_command
~~~~~~~~~~~~~

The console command to launch the server

Some examples:

If you want to launch a Minecraft server, you can:

.. code-block:: yaml

    start_command: java -Xms1G -Xmx2G -Dfile.encoding=UTF-8 -jar minecraft_server.jar nogui

If you have already written a startup script in the :ref:`working directory <configuration:working_directory>`, you can:

.. tab:: Windows

    .. code-block:: yaml

        start_command: start.bat

.. tab:: Linux

    .. code-block:: yaml

        start_command: ./start.sh

If there are some special character (e.g. ``"`` and ``\``) that yaml doesn't like in the command, you can either:

.. tab:: Windows

    .. code-block:: yaml

        # use "" to wrap the command and escape " and \
        start_command: "\"C:\\Program Files\\Java\\jdk-17.0.3.1\\bin\\java.exe\" -Xms1G -Xmx2G -Dfile.encoding=UTF-8 -jar minecraft_server.jar"

        # use '' to wrap the command
        start_command: '"C:\Program Files\Java\jdk-17.0.3.1\bin\java.exe" -Xms1G -Xmx2G -Dfile.encoding=UTF-8 -jar minecraft_server.jar'

        # use multi-line string
        start_command: |-
          "C:\Program Files\Java\jdk-17.0.3.1\bin\java.exe" -Xms1G -Xmx2G -Dfile.encoding=UTF-8 -jar minecraft_server.jar

.. tab:: Linux

    .. code-block:: yaml

        # use "" to wrap the command and escape " and \
        start_command: "\"/path/to my/java\" -Xms1G -Xmx2G -Dfile.encoding=UTF-8 -jar minecraft_server.jar"

        # use '' to wrap the command
        start_command: '"/path/to my/java" -Xms1G -Xmx2G -Dfile.encoding=UTF-8 -jar minecraft_server.jar'

        # use multi-line string
        start_command: |-
          "/path/to my/java" -Xms1G -Xmx2G -Dfile.encoding=UTF-8 -jar minecraft_server.jar

.. note::

    For Minecraft servers, you might want to add a ``-Dfile.encoding=UTF-8`` JVM property before the ``-jar`` argument, like the examples above

    See :ref:`configuration:encoding / decoding` section for more information of UTF-8 charset for Minecraft servers

* Option type: string
* Default value: ``java -Xms1G -Xmx2G -Dfile.encoding=UTF-8 -jar minecraft_server.jar nogui``

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
     - For Vanilla server in legacy versions, e.g. < 1.7, or even beta1.8. Tested in 1.6.4 and beta1.8.1.
   * - bukkit_handler
     - For Bukkit / Spigot server with Minecraft version below 1.14, and Paper / `Mohistmc <https://mohistmc.com>`__ server in all version.
   * - bukkit14_handler
     - For Bukkit / Spigot server with Minecraft version 1.14 and above
   * - forge_handler
     - For Forge server
   * - cat_server_handler
     - For `CatServer <https://github.com/Luohuayu/CatServer>`__ server
   * - bungeecord_handler
     - For Bungeecord. Please add ``-Djline.terminal=jline.UnsupportedTerminal`` before ``-jar`` in the start command for MCDR support. From `here <https://www.spigotmc.org/wiki/start-up-parameters/>`__
   * - waterfall_handler
     - For Waterfall server
   * - velocity_handler
     - For Velocity server
   * - basic_handler
     - The handler that parse nothing and return the raw text from the server. Don't use this unless you want to use MCDR to lanuch non Minecraft related servers.

* Option type: string
* Default value: ``vanilla_handler``

encoding / decoding
~~~~~~~~~~~~~~~~~~~

The codec format to encode messages to stdin / decode messages from stdout of the server

Leave it blank for MCDR to use the system encoding. If it doesn't work (e.g. random characters appear in the console),
you need to manually set them to the correct encoding / decoding methods used by the server

For Minecraft servers, if you are on an operating system that doesn't using UTF-8 as the default charset,
it's highly suggested to ensure all encoding / decoding use UTF-8 charset, due to the following facts:

1.  Python 3 uses UTF-8 to store strings
2.  Minecraft servers always use UTF-8 for reading stdin
3.  Minecraft servers use the default charset of the operating system for writing stdout / stderr / log files
4.  The default charset of your operating system might not be UTF-8.
    For example, Windows may use GBK as the default charset for Chinese users

.. mermaid::
    :alt: pipe
    :align: center

    sequenceDiagram
        participant MCDR
        participant pipe
        participant Minecraft
        MCDR->>pipe: send "hello" (encoding)
        pipe->>Minecraft: stdin (UTF-8)
        Minecraft-->>pipe: stdout/stderr (OS charset)
        pipe-->>MCDR: receive "world" (decoding)

Non-UTF-8 charset tends to cause annoying codec problems during encoding / decoding,
resulting in MCDR being unable to communicate normally with the server

To make everything related to the server use UTF-8, you can follow the steps below:

*   Ask MCDR to use UTF-8 to communicate with the Minecrate server,
    i.e. set both ``encoding`` and ``decoding`` in the MCDR configuration to ``utf8``

    .. code-block:: yaml

        encoding: utf8
        decoding: utf8

*   Make sure the JVM that launches Minecraft also uses UTF-8 as the default charset.
    You can achieve that with any of the following actions:

    *   (Recommend) Modify the start command for your server. Add a ``-Dfile.encoding=UTF-8`` JVM property before the ``-jar`` argument,
        just like the examples in the :ref:`configuration:start_command` sections

        .. code-block:: yaml

            start_command: java -Xms1G -Xmx2G -Dfile.encoding=UTF-8 -jar minecraft_server.jar
                                              ^^^^^^^^^^^^^^^^^^^^^

    *   Insert ``-Dfile.encoding=UTF-8`` into environment variable ``JAVA_TOOL_OPTIONS``

Then, the Minecraft server should run using UTF-8 as the charset for its standard IO streams,
and MCDR should be able communicate with the server perfectly

Of course, if you're sure that your operating system uses UTF-8 as the default character set,
then there's no need for any configuration. You can even leave these 2 options ``encoding``/ ``decoding`` blank to use the default system charset

* Option type: string or null
* Default value: ``utf8``, ``utf8``
* Examples: ``utf8``, ``gbk``

plugin_directories
~~~~~~~~~~~~~~~~~~

The list of directory path where MCDR will search for plugins to load

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

advanced_console
~~~~~~~~~~~~~~~~

Advance console switch powered by `prompt-toolkit <https://pypi.org/project/prompt-toolkit/>`__

Set it to false if you need to redirect the stdin/stdout of MCDR or just don't like it


* Option type: boolean
* Default value: ``true``

Advanced
^^^^^^^^

Configuration options for advanced users

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

A list of custom :doc:`/customize/handler` classes. The classed need to be subclasses of :class:`~mcdreforged.handler.abstract_server_handler.AbstractServerHandler`

Then you can use the name of your handler in the :ref:`configuration:handler` option above to use your handler

The name of a handler is defined in the :meth:`~mcdreforged.handler.abstract_server_handler.AbstractServerHandler.get_name` method


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

A list of custom :doc:`/customize/reactor` classes to handle the info instance. The classed need to be subclasses of :class:`~mcdreforged.info_reactor.abstract_info_reactor.AbstractInfoReactor`

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

.. _config-watchdog_threshold:

watchdog_threshold
~~~~~~~~~~~~~~~~~~

The required time interval in second for :doc:`/plugin_dev/watchdog` to consider the task executor thread is not responding. Set it to 0 to disable :doc:`/plugin_dev/watchdog`

* Option type: int or float
* Default value:

.. code-block:: yaml

    watchdog_threshold: 10

handler_detection
~~~~~~~~~~~~~~~~~~

By default, MCDR will start a handler detection on MCDR startup for a while,
to detect possible configuration mistake of the :ref:`configuration:handler` option

Set it to false to disable the handler detection for a few less performance loss after MCDR startup, mostly for profiling MCDR

* Option type: boolean
* Default value:

.. code-block:: yaml

    handler_detection: true

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
