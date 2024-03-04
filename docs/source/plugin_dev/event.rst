
Plugin Event
============

Plugin events are the most important way for plugins to interact with the server and the console

When the server has trigger a specific event, it will list out all event listeners that have registered to this event,
then MCDR will invoke the callback function of the listener with the given arguments

Event Listeners have a priority value. The default priority is ``1000``.
Plugins can specify the priority when they register an event listener manually.
MCDR will execute event listeners in ascending order according to the priority

Register a event listener
-------------------------

See :ref:`plugin_dev/basic:Event listeners` section in :doc:`/plugin_dev/basic` document

MCDR Event
----------

Default Event Listener
^^^^^^^^^^^^^^^^^^^^^^

All of the MCDR events have an attribute called "Default function name".
If your plugin declare a function in the global slope of the plugin file,
with the same name to the "Default function name",
the function will be automatically registered as a listener to the specific event.

The priority of these event listeners are always the default priority (``1000``)

MCDR Event List
^^^^^^^^^^^^^^^

To help understand, some MCDR events can be sorted into 3 lifecycle flows:

* Plugin lifecycle: :ref:`plugin_dev/event:Plugin Loaded` -> :ref:`plugin_dev/event:Plugin Unloaded`
* Server lifecycle: :ref:`plugin_dev/event:Server Start` -> :ref:`plugin_dev/event:Server Startup` -> :ref:`plugin_dev/event:Server Stop`
* MCDR lifecycle: :ref:`plugin_dev/event:MCDR Start` -> :ref:`plugin_dev/event:MCDR Stop`

.. _event-plugin-load:

Plugin Loaded
~~~~~~~~~~~~~

Plugin load event gets triggered once when a plugin is loaded. Plugins are supposed to register some event listeners,
commands and help messages as well as initialize their fields here

.. code-block:: python

    def on_load(server: PluginServerInterface, prev_module):
        server.register_command(...)
        server.register_event_listener(...)
        server.register_help_message(...)

If it's a plugin reload, ``prev_module`` argument indicates the previous plugin instance module,
otherwise if it's the first time to load the plugin, prev_module is None.
With this parameter plugin can easily inherit information from the previous plugin instance.
Here's an example:

.. code-block:: python

    def on_load(server: PluginServerInterface, prev_module):
        global reload_counter
        if prev_module is not None:
            reload_counter = prev_module.reload_counter + 1
        else:
            reload_counter = 0

Since it's the first event in the lifecycle of a plugin, this event can only be registered with default event listener,
so the ``on_load`` function is the entry spot of your plugin

Note: You should not dispatch custom events in the ``on_load`` function or it will do nothing.
The event listener storage of MCDR has not been initialized yet

:Event id: ``mcdr.plugin_loaded``
:Callback arguments: :class:`~mcdreforged.plugin.si.server_interface.PluginServerInterface`, :class:`Any` (previous module)
:Default function name: ``on_load``

.. _event-plugin-unload:

Plugin Unloaded
~~~~~~~~~~~~~~~

This event gets dispatched when MCDR unload the plugin instance. It can be caused by a plugin reload or a plugin unload

Also, this event will be dispatched during MCDR stopping, so it's a good place for you to do some cleanup

:Event id: ``mcdr.plugin_unloaded``
:Callback arguments: :class:`~mcdreforged.plugin.si.server_interface.PluginServerInterface`
:Default function name: ``on_unload``

.. _event-general-info:

General Info
~~~~~~~~~~~~

A new line of text is output from the stdout of the server, or a text is input from the console.
MCDR has already parsed the text into an :class:`~mcdreforged.info_reactor.info.Info` object. In this event plugin can response to the info

Here's an example

.. code-block:: python

    def on_info(server: PluginServerInterface, info: Info):
        if not info.is_user and re.fullmatch(r'Starting Minecraft server on \S*', info.content):
            server.logger.info('Minecraft is starting at address {}'.format(info.content.rsplit(' ', 1)[1]))


:Event id: ``mcdr.general_info``
:Callback arguments: :class:`~mcdreforged.plugin.si.server_interface.PluginServerInterface`, :class:`~mcdreforged.info_reactor.info.Info`
:Default function name: ``on_info``

.. _event-user-info:

User Info
~~~~~~~~~

User Info event is very similar to General Info event, but it only gets triggered when the info is sent by a user, more precisely,
:meth:`info.is_user<mcdreforged.info_reactor.info.Info.is_user>` is ``True``

If you want a simple way to handle user input, you can use this event

Here's an example

.. code-block:: python

    def on_user_info(server: PluginServerInterface, info: Info):
        if info.content == 'Restart the server!':
            server.reply(info, 'Roger that. Server restarting...')
            server.restart()

If you want to have a not-simple command system, rather than parsing them manually in User Info event,
I will suggest you to register a command tree for you plugin. See the :ref:`command registering <plugin_dev/basic:command>` doc


:Event id: ``mcdr.user_info``
:Callback arguments: :class:`~mcdreforged.plugin.si.server_interface.PluginServerInterface`, :class:`~mcdreforged.info_reactor.info.Info`
:Default function name: ``on_user_info``

.. _event-server-start:

Server Start
~~~~~~~~~~~~

The server process is just started by MCDR


:Event id: ``mcdr.server_start``
:Callback arguments: :class:`~mcdreforged.plugin.si.server_interface.PluginServerInterface`
:Default function name: ``on_server_start``

.. _event-server-startup:

Server Startup
~~~~~~~~~~~~~~

The server has fully started up. For example, a vanilla Minecraft server outputs ``Done (1.0s)! For help, type "help"``


:Event id: ``mcdr.server_startup``
:Callback arguments: :class:`~mcdreforged.plugin.si.server_interface.PluginServerInterface`
:Default function name: ``on_server_startup``

.. _event-server-stop:

Server Stop
~~~~~~~~~~~

The server process stops. You can do something depends on the process return code

MCDR will wait until all events finished their callbacks to continue executing

Example:

.. code-block:: python

    def on_server_stop(server: PluginServerInterface, server_return_code: int):
        if server_return_code != 0:
            server.logger.info('Is it a server crash?')


:Event id: ``mcdr.server_stop``
:Callback arguments: :class:`~mcdreforged.plugin.si.server_interface.PluginServerInterface`, :class:`int`
:Default function name: ``on_server_stop``

.. _event-mcdr-start:

MCDR Start
~~~~~~~~~~

The MCDR is starting. Only plugins which is loaded with MCDR is able to receive this event


:Event id: ``mcdr.mcdr_start``
:Callback arguments: :class:`~mcdreforged.plugin.si.server_interface.PluginServerInterface`
:Default function name: ``on_mcdr_start``

.. _event-mcdr-stop:

MCDR Stop
~~~~~~~~~

The MCDR is stopping. Time to do some clean up

MCDR will wait until all events finished their callbacks to continue executing

Watchdog is disabled during this event dispatching, so you can safely block MCDR here to wait until your cleanup codes finishes


:Event id: ``mcdr.mcdr_stop``
:Callback arguments: :class:`~mcdreforged.plugin.si.server_interface.PluginServerInterface`
:Default function name: ``on_mcdr_stop``

.. _event-player-joined:

Player Joined
~~~~~~~~~~~~~

A player just joined the game. MCDR only parses the name of the player to a string, plugin can use the info instance for more custom information parsing

Example:

.. code-block:: python

    def on_player_joined(server: PluginServerInterface, player: str, info: Info):
        server.say('Welcome {}'.format(player))


:Event id: ``mcdr.player_joined``
:Callback arguments: :class:`~mcdreforged.plugin.si.server_interface.PluginServerInterface`, :class:`str`, :class:`~mcdreforged.info_reactor.info.Info`
:Default function name: ``on_player_joined``

.. _event-player-left:

Player Left
~~~~~~~~~~~

A player just left the game. Plugin can do cleanups for player related objects


:Event id: ``mcdr.player_left``
:Callback arguments: :class:`~mcdreforged.plugin.si.server_interface.PluginServerInterface`, :class:`str`
:Default function name: ``on_player_left``

Custom Event
------------

Besides MCDR itself, plugins can also dispatch its own event. All you need to do is invoking
:meth:`ServerInterface.dispatch_event<mcdreforged.plugin.si.server_interface.ServerInterface.dispatch_event>` api with the event and some arguments

Customizing event is a good way to broadcast a message between plugins. It's also a good indirectly way for your plugin to react to requests from other plugins 
