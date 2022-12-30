
ServerInterface
===============

:ref:`API package <api-package>` path: ``mcdreforged.api.types``

.. currentmodule:: mcdreforged.plugin.server_interface

.. autoclass:: ServerInterface

Utils
-----

.. autoattribute:: ServerInterface.MCDR
.. autoproperty:: ServerInterface.logger
.. automethod:: ServerInterface.get_instance
.. automethod:: ServerInterface.tr
.. automethod:: ServerInterface.rtr
.. automethod:: ServerInterface.as_basic_server_interface
.. automethod:: ServerInterface.as_plugin_server_interface

Server Control
--------------

.. automethod:: ServerInterface.start
.. automethod:: ServerInterface.stop
.. automethod:: ServerInterface.kill
.. automethod:: ServerInterface.wait_for_start
.. automethod:: ServerInterface.restart
.. automethod:: ServerInterface.stop_exit
.. automethod:: ServerInterface.exit
.. automethod:: ServerInterface.set_exit_after_stop_flag
.. automethod:: ServerInterface.is_server_running
.. automethod:: ServerInterface.is_server_startup
.. automethod:: ServerInterface.is_rcon_running
.. automethod:: ServerInterface.get_server_pid
.. automethod:: ServerInterface.get_server_pid_all
.. automethod:: ServerInterface.get_server_information

Text Interaction
----------------

.. automethod:: ServerInterface.execute
.. automethod:: ServerInterface.tell
.. automethod:: ServerInterface.say
.. automethod:: ServerInterface.broadcast
.. automethod:: ServerInterface.reply

Plugin Queries
--------------

.. automethod:: ServerInterface.get_plugin_metadata
.. automethod:: ServerInterface.get_plugin_file_path
.. automethod:: ServerInterface.get_plugin_instance
.. automethod:: ServerInterface.get_plugin_list
.. automethod:: ServerInterface.get_unloaded_plugin_list
.. automethod:: ServerInterface.get_disabled_plugin_list
.. automethod:: ServerInterface.get_all_metadata

Plugin Operations
-----------------

.. warning::
    All plugin manipulation will trigger a dependency check, which might cause unwanted plugin operations

    It's not suggested to trigger plugin operations during :ref:`on_load <event-plugin-load>` or :ref:`on_unload <event-plugin-unload>` plugin events.
    During these events, MCDR is in a process of an ongoing plugin operation, which is not suitable to triggered another plugin operation

    If you do trigger a plugin operation during :ref:`on_load <event-plugin-load>` or :ref:`on_unload <event-plugin-unload>` plugin events,
    MCDR will delay the new operations till the first operation finishes. In this delayed operation case, the return value of following APIs will always be false or None

.. automethod:: ServerInterface.load_plugin
.. automethod:: ServerInterface.enable_plugin
.. automethod:: ServerInterface.reload_plugin
.. automethod:: ServerInterface.unload_plugin
.. automethod:: ServerInterface.disable_plugin
.. automethod:: ServerInterface.refresh_all_plugins
.. automethod:: ServerInterface.refresh_changed_plugins
.. automethod:: ServerInterface.dispatch_event

Permission
----------

.. automethod:: ServerInterface.get_permission_level
.. automethod:: ServerInterface.set_permission_level

Command
-------

.. automethod:: ServerInterface.get_plugin_command_source
.. automethod:: ServerInterface.execute_command

Preference
----------

.. automethod:: ServerInterface.get_preference

Misc
----

.. automethod:: ServerInterface.is_on_executor_thread
.. automethod:: ServerInterface.rcon_query
.. automethod:: ServerInterface.get_mcdr_language
.. automethod:: ServerInterface.get_mcdr_config
.. automethod:: ServerInterface.schedule_task
