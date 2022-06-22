
MCDR Plugin
===========

What is a MCDR plugin
---------------------

A MCDR plugin is a single ``.py`` or ``.mcdr`` file or a directory with specific file structure located in plugin directories. See `here <plugin_format.html>`__ for more information about plugin format

The list of the plugin directory can be defined inside the `configuration file <../configure.html#plugin_directories>`__. At start up, MCDR will automatically load every plugin inside every plugin directory

Check the `example plugin repository <https://github.com/MCDReforged/MCDReforged-ExamplePlugin>`__ or the `plugin template repository <https://github.com/MCDReforged/MCDReforged-PluginTemplate>`__ for more references

Quick Start
-----------

Open one of the plugin directories of MCDR, create a file named ``HelloWorld.py``

.. code-block:: bash

    cd my_plugin_folder
    touch HelloWorld.py

open it and enter these code

.. code-block:: python

    PLUGIN_METADATA = {
        'id': 'hello_world',
        'version': '1.0.0',
        'name': 'My Hello World Plugin'
    }


    def on_load(server, old):
        server.logger.info('Hello world!')

Return to MCDR console, enter ``!!MCDR reload plugin``, and you should see the hello world message from your plugin

.. code-block::

    [TaskExecutor/INFO] [hello_world]: Hello world!

Great, you have successfully created your first plugin

Metadata
--------

The meta data field provides the basic information of the plugin. It's declared as a json object contains several key-value, e.g.:

.. code-block:: json

    {
        "id": "example_plugin",
        "version": "1.0.0",
        "name": "Example Plugin",
        "description": "Example plugin for MCDR",
        "author": "Fallen_Breath",
        "link": "https://github.com/MCDReforged/MCDReforged-ExamplePlugin",
        "dependencies": {
           "mcdreforged": ">=2.0.0-alpha.1"
        }
    }

Different `plugin format <plugin_format.html>`__ has different ways to declare its metadata, but the contents of metadata are the same

See the `metadata document <metadata.html>`__ for more information

Entrypoint
----------

Entrypoint is a module specifying what module MCDR will import when loading your plugin. It's the bridge between your plugin and MCDR

For `solo plugin <plugin_format.html#solo-plugin>`__ the entry point is the plugin itself. For `multi file plugin <plugin_format.html#multi-file-plugin>`__ the entrypoint is declared in metadata, with default value the id of the plugin, which is the ``__init__.py`` file in the folder named plugin id

For example:

.. code-block::

    MyPlugin.mcdr
        my_plugin/
            __init__.py
            source.py
        mcdreforged.plugin.json

For this multi file plugin, with default entrypoint value, MCDR will import the module ``my_plugin``, which will actually loads the ``__init__.py`` in ``my_plugin/`` folder inside the ``MyPlugin.mcdr`` file. ``on_load`` function inside the ``__init__.py`` will be registered as an event listener

If the entrypoint is set to ``my_plugin.source``, then MCDR will import ``my_plugin.source``, which will actually loads ``source.py`` in ``my_plugin/`` folder

The entrypoint module instance is also used in `ServerInterface.get_plugin_instance <classes/ServerInterface.html#get_plugin_instance>`__. The entrypoint module instance is also what the second parameter in `Plugin loaded <event.html#plugin-loaded>`__ event is

Plugin Registry
---------------

Plugin registry is a collection of things that plugin registered for. It will get cleaned up every time before the plugin gets loaded, so you'd better register them in `Plugin_Load <event.html#plugin-load>`__ event

Event listeners
^^^^^^^^^^^^^^^

There are 3 methods to register an event listener for you plugin

#. 
    Declare a function inside the global slope in the `entrypoint <#entrypoint>`__ module with the specific name. It's the legacy registering method to register a listener and it only works with events provided by MCDR. Check `here <event.html#default-event-listener>`__ for more detail

    For example, the widely-used function below is a default `Plugin Loaded <event.html#plugin-loaded>`__ event listener

    .. code-block:: python

        def on_load(server, prev):
            do_something()

#. 
    Manually invoke ``server.register_event_listener`` method to register an event listener. You can specify the callable object and the priority for the event listener

    Check `here <event.html#register-a-event-listener>`__ for more detail about event listener registering

    Here some examples about manually register event listeners

    .. code-block:: python

        def my_on_mcdr_general_info(server, info):
            pass

        def on_my_task_done(server, my_task_info, my_task_data):  # the 2nd and 3rd parameter is determined by the plugin that emits this event
            pass

        def on_load(server, prev):
            server.register_event_listener('mcdr.general_info', my_on_mcdr_general_info, priority=500)
            server.register_event_listener(MCDRPluginEvents.PLUGIN_UNLOADED, my_on_unload, priority=2000)
            server.register_event_listener('myplugin.task_done', on_my_task_done)

#.
    Use `@event_listener <api.html#event-listener>`__ decorator


Take a look at the reference of ``register_event_listener`` method in `PluginServerInterface <classes/PluginServerInterface.html#register-event-listener>`__ document for more detail

Command
^^^^^^^

Rather than manually parsing ``info.content`` inside user info event callback like ``on_user_info``, MCDR provides a command system for plugins to register their commands

Check the `command <command.html>`__ document for more detail about building a command tree

Assuming that you have already built a command tree with root literal node *root*, then you can use the following code to register your command tree in MCDR

.. code-block:: python

    server.register_command(root)

Take a look at the reference of ``register_command`` method in `PluginServerInterface <classes/PluginServerInterface.html#register-command>`__ document for more details of its usage

Help message
^^^^^^^^^^^^

Plugin can register its help message with ``server.register_help_message`` to MCDR, so that users can use `!!help command <../command.html#help-command>`__ to view the help messages of all commands

Take a look at the reference of ``register_help_message`` method in `PluginServerInterface <classes/PluginServerInterface.html#register-help-message>`__ document for more details of its usage

Translation
^^^^^^^^^^^

If your plugin needs to handle some message localization or translation things, you can let MCDR help you: register a translation via `register_translation <classes/PluginServerInterface.html#register-translation>`__ and use `tr <classes/ServerInterface.html#tr>`__ to get the translated string

See the `translation section <dev_tips.html#translation>`__ in dev tips for some suggestions about using translation

Import a plugin
---------------

During multi file plugin loading, MCDR will append the path of the multi file plugin to ``sys.path``. For packed plugin, it's path of the ``.mcdr`` file; For directory plugin, it's the path of the directory

Therefore, you can simply import other plugin by importing its plugin id using the ``import`` statement. It's also the recommended way to do that since it provides code hints and more information for your IDE

Apart from this, you can also use `get_plugin_instance <classes/ServerInterface.html#get_plugin_instance>`__ method to import the entry point of the plugin, and this is also **the only way to import a solo plugin**. For multi file plugin the result is the same as directly importing the plugin

.. code-block:: python

    import my_lib_plugin as libA
    libB = server.get_plugin_instance('my_lib_plugin')
    print(libA == libB)  # True

Don't forget to declare plugin dependency in your metadata, or MCDR will not guarantee a correct plugin loading order

