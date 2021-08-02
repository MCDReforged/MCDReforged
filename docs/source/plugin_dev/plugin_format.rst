
Plugin Format
=============

A MCDR plugin is a


Solo Plugin
-----------

Solo Plugin consists of a single python ``.py`` source file. It's the plugin format which aims for easy to write and rapid development

The metadata of a solo plugin is declared in the global scope of the source file. It's a dict contains several key-value with the name ``PLUGIN_METADATA``

Here's a example:

.. code-block:: python

   PLUGIN_METADATA = {
       'id': 'my_plugin_id',
       'version': '1.0.0',
       'name': 'My Plugin',
       'description': 'A plugin to do something cool',
       'author': 'myself',
       'link': 'https://github.com',
       'dependencies': {
           'mcdreforged': '>=1.0.0',
           'an_important_api': '*'
       }
   }

Being restricted with the one-file-only file format, some features are missing in solo plugin:

1. Python requirement check is not supported
2. Directly import from other plugin is not supported. Other plugin can only use `get_plugin_instance <classes/ServerInterface.html#get_plugin_instance>`__ to access your plugin
3. Cannot be added to MCDR plugin catalogue

When you only want to create a simple plugin as fast as possible, creating a solo plugin is always a good choice

Packed Plugin
-------------

Packed plugin is a zip type compressed file with file extension name ``.mcdr``. It's the recommand plugin format for general plugin


Directory Plugin
----------------
-