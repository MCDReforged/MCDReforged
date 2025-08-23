
Configuration
=============

The configuration file of MCDR is ``config.yml``. It's located and should be located in the working directory of MCDR

At startup, MCDR will try to load the configuration file. If the configuration file is not present, MCDR will generate a default config file and exit. Otherwise, MCDR will load the config file and compare its content with the default configuration file. If your configuration file has any missing options, MCDR will add default values to the end of your configuration file

The configuration file use `YAML <https://en.wikipedia.org/wiki/YAML>`__ format

You can use command ``!!MCDR reload config`` or its short form ``!!MCDR r cfg`` to reload the config file when MCDR is running

.. seealso::

    :ref:`command/mcdr:Hot reloads` command, for more detail about hot reloads

Basic Configuration
-------------------

Basic configs of MCDR

language
^^^^^^^^

The language that MCDR will use to display information


* Option type: :external:class:`str`
* Default value: ``en_us``
* Available options: ``en_us``, ``zh_cn``, ``zh_tw``

Server configuration
--------------------

Configs for the server that MCDR starts and controls

working_directory
^^^^^^^^^^^^^^^^^

The working directory of the server. You should probably put all the files related to the server int this directory


* Option type: :external:class:`str`
* Default value: ``server``

start_command
^^^^^^^^^^^^^

The console command to launch the server. It can be a string or a list of string

* (shell mode) If it's a string, the command will be executed as a shell command in a shell environment.
  It's the suggested way to use due to its simpleness

    .. code-block:: yaml

        start_command: echo Hello world from MCDReforged

* (exec mode) If it's a list of strings, the command will be executed directly using exec.
  It's useful when you want the server process directly managed by MCDR (MCDR - server),
  instead of having a shell process in the middle of the process chain (MCDR - shell - server)

    .. tab:: Flatten

        .. code-block:: yaml

            start_command:
              - echo
              - Hello world from MCDReforged

    .. tab:: Inline

        .. code-block:: yaml

            start_command: ['echo', 'Hello world from MCDReforged']

    .. versionadded:: v2.13.0

.. seealso::

    The *args* argument of the constructor of class :external:class:`subprocess.Popen`

If you want to launch a Minecraft server, here are some useful examples. Both of them use a single string as the value,
which mean the server will be started in shell mode:

.. code-block:: yaml

    start_command: java -Xms1G -Xmx2G -jar minecraft_server.jar nogui

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
        start_command: "\"C:\\Program Files\\Java\\jdk-17.0.3.1\\bin\\java.exe\" -Xms1G -Xmx2G -jar minecraft_server.jar"

        # use '' to wrap the command
        start_command: '"C:\Program Files\Java\jdk-17.0.3.1\bin\java.exe" -Xms1G -Xmx2G -jar minecraft_server.jar'

        # use multi-line string
        start_command: |-
          "C:\Program Files\Java\jdk-17.0.3.1\bin\java.exe" -Xms1G -Xmx2G -jar minecraft_server.jar

.. tab:: Linux

    .. code-block:: yaml

        # use "" to wrap the command and escape " and \
        start_command: "\"/path/to my/java\" -Xms1G -Xmx2G -jar minecraft_server.jar"

        # use '' to wrap the command
        start_command: '"/path/to my/java" -Xms1G -Xmx2G -jar minecraft_server.jar'

        # use multi-line string
        start_command: |-
          "/path/to my/java" -Xms1G -Xmx2G -jar minecraft_server.jar

.. note::

    For Minecraft servers, you might want to add some JVM properties like ``-Dfile.encoding=UTF-8`` before the ``-jar`` argument to ensure a UTF-8 charset environment

    See :ref:`configuration:encoding, decoding` section for more information of UTF-8 charset for Minecraft servers

* Option type: :external:class:`str` or ``List[str]``
* Default value: ``echo Hello world from MCDReforged``

handler
^^^^^^^

Different Minecraft server has different kind of output, and event different kind of command. Server handlers are the modules to handle between all kind of servers and the interface for MCDR to control the server

Handler determines the specific way to parse the standard output text of the server, and uses the correct command for server control

Here is a table of current built-in handlers and their suitable server types

.. list-table::
   :header-rows: 1

   * - Handler
     - Compatible server types
   * - vanilla_handler
     - For Vanilla / Carpet / Fabric server. Use this if your server is vanilla enough
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
   * - arclight_handler
     - For `Arclight <https://github.com/IzzelAliz/Arclight>`__ server. Tested with `arclight-forge-1.20.1-1.0.1.jar`
   * - bungeecord_handler
     - For Bungeecord. Please add ``-Djline.terminal=jline.UnsupportedTerminal`` before ``-jar`` in the start command for MCDR support. From `here <https://www.spigotmc.org/wiki/start-up-parameters/>`__
   * - waterfall_handler
     - For Waterfall server
   * - velocity_handler
     - For Velocity server
   * - basic_handler
     - The handler that parse nothing and return the raw text from the server. Don't use this unless you want to use MCDR to lanuch non Minecraft related servers.

* Option type: :external:class:`str`
* Default value: ``vanilla_handler``

encoding, decoding
^^^^^^^^^^^^^^^^^^

The codec format to encode messages to stdin / decode messages from stdout of the server

Leave it blank for MCDR to use the system encoding. If it doesn't work (e.g. random characters appear in the console),
you need to manually set them to the correct encoding / decoding methods used by the server

For vanilla Minecraft servers, if you are on an operating system that doesn't using UTF-8 as the default charset,
it's highly suggested to ensure all encoding / decoding use UTF-8 charset, due to the following facts:

*   Python 3 uses UTF-8 to store strings
*   Vanilla Minecraft servers always use UTF-8 for reading stdin
*   Vanilla Minecraft servers use the default charset of the operating system for writing stdout / stderr / log files
*   The default charset of your operating system might not be UTF-8.
    For example, Windows may use GBK as the default charset for Chinese users
*   Non-UTF-8 charset tends to cause annoying codec problems during encoding / decoding,
    resulting in MCDR being unable to communicate normally with the server

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

To make everything related to the server use UTF-8, you can follow the steps below:

#.  Ask MCDR to use UTF-8 to communicate with the Minecraft server,
    i.e. set both ``encoding`` and ``decoding`` in the MCDR configuration to ``utf8``

    .. code-block:: yaml

        encoding: utf8
        decoding: utf8

#.  Make sure the JVM that launches Minecraft also uses UTF-8 as the default charset.
    To achieve that, you can apply the following JVM properties for the Minecraft process

        .. tab:: Java >= 19

            .. code-block:: bash

                -Dfile.encoding=UTF-8 -Dstdout.encoding=UTF-8 -Dstderr.encoding=UTF-8

            If you are using a Long-Term-Support Java version (e.g. 8, 11, 17, 21), you can always use this as a universal Java UTF-8 solution
            no matter what your Java version is. Those unrecognized system properties ``stdout.encoding`` and ``stderr.encoding`` are harmless

            See also: The "Explanation of the above JVM properties" section below

        .. tab:: Java 18

            .. code-block:: bash

                -Dfile.encoding=UTF-8 -Dsun.stdout.encoding=UTF-8 -Dsun.stderr.encoding=UTF-8

            Notes that ``-Dsun.stdout.encoding`` and ``-Dsun.stderr.encoding`` are unspecified API.
            See also: `JEP 400 <https://openjdk.org/jeps/400>`__

        .. tab:: Java <= 17

            .. code-block:: bash

                -Dfile.encoding=UTF-8

    To apply the JVM properties, you can:

    *   (Recommend) Modify the start command for your server. Add the following arguments before the ``-jar`` argument

        .. code-block:: yaml

            start_command: java -Xms1G -Xmx2G -Dfile.encoding=UTF-8 -Dstdout.encoding=UTF-8 -Dstderr.encoding=UTF-8 -jar minecraft_server.jar
            #                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^ insert these ^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    *   Insert the arguments you need into environment variable ``JAVA_TOOL_OPTIONS``, in case you can't modify the server start command

        .. code-block:: bash

            export JAVA_TOOL_OPTIONS="-Dfile.encoding=UTF-8 -Dstdout.encoding=UTF-8 -Dstderr.encoding=UTF-8"

Then, the Minecraft server should run using UTF-8 as the charset for its standard IO streams,
and MCDR should be able communicate with the server perfectly

Of course, if you're sure that your operating system uses UTF-8 as the default character set,
then there's no need for any configuration. You can even leave these 2 options ``encoding``/ ``decoding`` blank to use the default system charset

If you server has mixed encoding output, you can provide multiple decoding method by supplying a list of string as the value,
In this case, MCDR will try all decoding methods one by one until one succeeds

* Example scenario: In Windows, the shell outputs with OS-charset (let's say GBK), and the server outputs with UTF-8
* Example solution: ``decoding: ['utf8', 'gbk']``

**encoding**

* Option type: ``Optional[str]``
* Default value: ``utf8``
* Examples: ``utf8``, ``gbk``

**decoding**

* Option type: ``Optional[str]`` or ``List[str]``
* Default value: ``utf8``
* Examples: ``utf8``, ``gbk``, ``['utf8', 'gbk']``

.. dropdown:: Explanation of the above JVM properties

    For Minecraft server, it has 2 common way to print stuffs to stdout / stderr:

    **(a) Log with log4j**

        Vanilla Minecraft server uses the log4j library for logging.
        It configures log4j to use ``ConsoleAppender`` for logging messages to stdout,
        which eventually uses ``Charset.defaultCharset()`` to get the default charset

        UTF-8 solution for this case: ``-Dfile.encoding=UTF-8``

    **(b) Print with System.out or System.err**

        Sometimes Minecraft server might directly print stuffs into stdout / stderr.
        In this case, we need to ensure both of ``System.out`` and ``System.err`` use UTF-8 charset as the encoding method

        UTF-8 solution for this case:

        .. list-table::
            :header-rows: 1

            * - Java Version
              - JVM args to ensure UTF-8
            * - <= 1.17
              - ``-Dfile.encoding=UTF-8``
            * - 1.18
              - ``-Dsun.stdout.encoding=UTF-8 -Dsun.stderr.encoding=UTF-8`` (unspecified API)
            * - >= 1.19
              - ``-Dstdout.encoding=UTF-8 -Dstderr.encoding=UTF-8``

        See also:

        *   `JEP 400: UTF-8 by Default <https://openjdk.org/jeps/400>`__
        *   https://bugs.openjdk.org/browse/JDK-8285492

rcon
^^^^

The setting for `rcon <https://wiki.vg/RCON>`__. If rcon is enabled, MCDR will start a rcon client to connect to the server after server rcon has started up. Then plugins can use rcon to query command from the server

To configure rcon to work with MCDR, search for these lines in your ``server.properties`` of your Minecraft server:

.. code-block:: properties

    enable-rcon=false
    rcon.password=
    rcon.port=25575

Make them the same value as the MCDR configurations.

rcon.enable
"""""""""""

The switch of rcon


* Option type: :external:class:`bool`
* Default value: ``false``

rcon.address
""""""""""""

The address of the rcon server


* Option type: :external:class:`str`
* Default value: ``127.0.0.1``

rcon.port
"""""""""

The port of the rcon server


* Option type: :external:class:`int`
* Default value: ``25575``

rcon.password
"""""""""""""

The password to connect to the rcon server


* Option type: :external:class:`str`
* Default value: ``password``


Plugin configuration
--------------------

MCDR plugin related configs

plugin_directories
^^^^^^^^^^^^^^^^^^

The list of directory path where MCDR will search for plugins to load

* Option type: ``List[str]``
* Default value:

.. code-block:: yaml

    plugin_directories:
      - plugins


* Example:

.. code-block:: yaml

    plugin_directories:
      - plugins
      - path/to/my/plugin/directory
      - /another/plugin/directory

catalogue_meta_cache_ttl
^^^^^^^^^^^^^^^^^^^^^^^^

The cache TTL of a fetched plugin catalogue meta

MCDR will use the cached meta as the data source for catalogue plugin operations within the TTL

* Option type: :external:class:`float`
* Default value: ``1200`` (20 min)

catalogue_meta_fetch_timeout
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The timeout in seconds for a plugin catalogue meta fetch

* Option type: :external:class:`float`
* Default value: ``15``

catalogue_meta_url
^^^^^^^^^^^^^^^^^^

Override the URL pointing to the "everything.json" or "everything_slim.json" file,
which is used to fetch the plugin catalogue meta

If it ends with ".gz" (gzip) or ".xz" (lzma), corresponding decompression operation will be applied

If not provided, the url will be ``https://api.mcdreforged.com/catalogue/everything_slim.json.xz``

Example value (using the original url from raw.githubusercontent.com):

.. code-block:: yaml

    catalogue_meta_url: 'https://raw.githubusercontent.com/MCDReforged/PluginCatalogue/meta/everything_slim.json.xz'

* Option type: ``Optional[str]``
* Default value: *empty*

plugin_download_url
^^^^^^^^^^^^^^^^^^^

.. note::

    A to-be-downloaded plugin file from the plugin catalogue is a valid GitHub release asset

Plugin file download override. Should be a valid python :external:meth:`str.format` string

Available variables:

* ``{url}``: The original GitHub asset download url
* ``{repos_owner}``: The name of the owner of the GitHub repository
* ``{repos_name}``: The name of the GitHub repository
* ``{tag}``: Name of the git tag associated with the release
* ``{asset_name}``: Name of the asset file, i.e. name of the plugin file
* ``{asset_id}``: The GitHub asset ID

As an example, to use `ghproxy <https://ghfast.top/>`__, you can set it to:

.. code-block:: yaml

    plugin_download_url: 'https://ghfast.top/{url}'

Another example of a manual concatenation of the GitHub release asset default url. It's useless, but a good example to demonstrate how this work:

.. code-block:: yaml

    plugin-download_url: 'https://github.com/{repos_owner}/{repos_name}/releases/download/{tag}/{asset_name}'

If not provided, the origin GitHub asset download url will be directly used

* Option type: ``Optional[str]``
* Default value: *empty*

plugin_download_timeout
^^^^^^^^^^^^^^^^^^^^^^^

The timeout in seconds for a plugin file download

* Option type: :external:class:`float`
* Default value: ``15``

plugin_pip_install_extra_args
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Extra arguments passed to the pip subprocess for installing required python packages during plugin installation

.. code-block:: yaml

    plugin_pip_install_extra_args: -i https://pypi.tuna.tsinghua.edu.cn/simple --proxy http://localhost:8080

* Option type: ``Optional[str]``
* Default value: *empty*

Misc configuration
------------------

Miscellaneous configs of MCDR

check_update
^^^^^^^^^^^^

If set to true, MCDR will detect if there's a new version every 24h

* Option type: :external:class:`bool`
* Default value: ``true``

advanced_console
^^^^^^^^^^^^^^^^

Advance console switch powered by `prompt-toolkit <https://pypi.org/project/prompt-toolkit/>`__

Set it to false if you need to redirect the stdin/stdout of MCDR or just don't like it


* Option type: :external:class:`bool`
* Default value: ``true``

http_proxy, https_proxy
^^^^^^^^^^^^^^^^^^^^^^^

HTTP(s) proxy setting for all external HTTP requests in MCDR

It's suggested to set value for http_proxy and https_proxy at the same time

Example values::

    http_proxy: 'http://127.0.0.1:1081'
    https_proxy: 'http://127.0.0.1:1081'

    http_proxy: 'http://user:pass@192.168.0.1:8888'
    https_proxy: 'http://user:pass@192.168.0.1:8888'

* Option type: ``Optional[str]``
* Default value: *empty*

telemetry
^^^^^^^^^

The telemetry switch

MCDR collects anonymous telemetry data on some basic information about MCDR and the runtime environment, for the purpose of improving MCDR.
The collected telemetry data do not contain any personal information, and are not sold or used for advertising purposes

If you simply don't want MCDR to report any telemetry data, you can disable it by setting the option value to false

.. seealso::

    :doc:`/telemetry` document


* Option type: :external:class:`bool`
* Default value: ``true``. ``false`` if environment variable ``MCDREFORGED_TELEMETRY_DISABLED`` is set to ``true``


Advanced configuration
----------------------

Configuration options for advanced users

disable_console_thread
^^^^^^^^^^^^^^^^^^^^^^

When set to true, MCDR will not start the console thread for handling console command input

Don't change it to true unless you know what you are doing


* Option type: :external:class:`bool`
* Default value: ``false``

disable_console_color
^^^^^^^^^^^^^^^^^^^^^

When set to true, MCDR will removed all console font formatter codes in before any message gets printed onto the console


* Option type: :external:class:`bool`
* Default value: ``false``

custom_handlers
^^^^^^^^^^^^^^^

A list of custom :doc:`/customize/handler` classes. The classed need to be subclasses of :class:`~mcdreforged.handler.abstract_server_handler.ServerHandler`

Then you can use the name of your handler in the :ref:`configuration:handler` option above to use your handler

The name of a handler is defined in the :meth:`~mcdreforged.handler.abstract_server_handler.ServerHandler.get_name` method


* Option type: ``Optional[List[str]]``
* Default value: 

.. code-block:: yaml

    custom_handlers:


* Example:

.. code-block:: yaml

    custom_handlers:
      - handlers.my_handler.MyHandler

In this example the custom handler package path is ``handlers.my_handler`` and the class is name ``MyHandler``

custom_info_reactors
^^^^^^^^^^^^^^^^^^^^

A list of custom :doc:`/customize/reactor` classes to handle the info instance. The classed need to be subclasses of :class:`~mcdreforged.handler.abstract_server_handler.ServerHandler`

All custom info reactors will be registered to the reactor list to process information from the server


* Option type: ``Optional[List[str]]``
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
^^^^^^^^^^^^^^^^^^

The required time interval in second for :doc:`/plugin_dev/watchdog` to consider the task executor thread is not responding. Set it to 0 to disable :doc:`/plugin_dev/watchdog`

* Option type: :external:class:`int` or :external:class:`float`
* Default value:

.. code-block:: yaml

    watchdog_threshold: 10

handler_detection
^^^^^^^^^^^^^^^^^^

By default, MCDR will start a handler detection on MCDR startup for a while,
to detect possible configuration mistake of the :ref:`configuration:handler` option

Set it to false to disable the handler detection for a few less performance loss after MCDR startup, mostly for profiling MCDR

* Option type: :external:class:`bool`
* Default value:

.. code-block:: yaml

    handler_detection: true

Debug configuration
-------------------

Configurations for debugging MCDR

debug
^^^^^

Debug logging switches. Set ``all`` to true to enable all debug logging, or set the specific option to enable specific debug logging


* Default value: 

.. code-block:: yaml

    debug:
      all: false
      mcdr: false
      process: false
      handler: false
      reactor: false
      plugin: false
      permission: false
      command: false
      telemetry: true

write_server_output_to_log_file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When enabled, server outputs will be logged to both the console and the MCDR log file (``MCDR.log``),
which might be useful for debugging MCDR

* Option type: :external:class:`bool`
* Default value:

.. code-block:: yaml

    write_server_output_to_log_file: false
