
MCDR Plugin
===========

What is a MCDR plugin
---------------------

An MCDR plugin is a python source file with ``.py`` file extension located in plugin directories. The list of the plugin directory can be defined inside the `configure file <../configure.html#plugin_directories>`__

At start up, MCDR will automatically load every plugin inside the plugin directories. Additionally, MCDR will append all the plugin directories into ``sys.path``, so plugins can import modules placed inside the plugin folders directly

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

Different `plugin format <plugin_format.rst>`__ has different ways to declare its metadata, but the contents of metadata are the same

See the `metadata document <metadata.rst>`__ for more information


Plugin Registry
---------------

Plugin registry is a collection of things that plugin registered for. It will get cleaned up every time before the plugin gets loaded, so you'd better register them in `Plugin_Load <event.html#plugin-load>`__ event

Event listeners
^^^^^^^^^^^^^^^

There are 2 methods to register an event listener for you plugin


#. 
   Declare a function inside the global slope with the specific name. It's the legacy registering method to register a listener and it only works with events provided by MCDR. Check `here <event.html#default-event-listener>`__ for more detail

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
           server.register_event_listener('mcdr.general_info', my_on_mcdr_general_info, priority=500)  # TODO: use better event identifier
           server.register_event_listener('myplugin.task_done', on_my_task_done)  # TODO: use better event identifier

Take a look at the reference of ``register_event_listener`` method in `ServerInterface <classes/ServerInterface.html#register-event-listener>`__ document for more detail

Command
^^^^^^^

Rather than manually parsing ``info.content`` inside user info event callback like ``on_user_info``, MCDR provides a command system for plugins to register their commands

Check the `command <command>`__ document for more detail about building a command tree

Assuming that you have already built a command tree with root literal node *root*, then you can use the following code to register your command tree in MCDR

.. code-block:: python

    server.register_command(root)

Take a look at the reference of ``register_command`` method in `ServerInterface <classes/ServerInterface.html#register-command>`__ document for more details of its usage

Help message
^^^^^^^^^^^^

Plugin can register its help message with ``server.register_help_message`` to MCDR, so that users can use `!!help command <../command.html#help-command>`__ to view the help messages of all commands

Take a look at the reference of ``register_help_message`` method in `ServerInterface <classes/ServerInterface.html#register-help-message>`__ document for more details of its usage
