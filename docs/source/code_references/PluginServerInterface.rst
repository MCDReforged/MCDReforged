
PluginServerInterface
=====================

:ref:`API package <api-package>` path: ``mcdreforged.api.types``

.. currentmodule:: mcdreforged.plugin.server_interface

.. autoclass:: PluginServerInterface

Plugin Registry
---------------

.. automethod:: PluginServerInterface.register_event_listener
.. automethod:: PluginServerInterface.register_command
.. automethod:: PluginServerInterface.register_help_message
.. automethod:: PluginServerInterface.register_translation

Plugin Utils
------------

.. automethod:: PluginServerInterface.get_self_metadata
.. automethod:: PluginServerInterface.get_data_folder
.. automethod:: PluginServerInterface.open_bundled_file
.. automethod:: PluginServerInterface.load_config_simple
.. automethod:: PluginServerInterface.save_config_simple
