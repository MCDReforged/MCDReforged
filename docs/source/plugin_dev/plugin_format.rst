
Plugin Format
=============

There are 3 types of valid format of a MCDR plugin, each of them has its own advantages and disadvantages depending on the user cases

See `this repository <https://github.com/MCDReforged/MCDReforged-ExamplePlugin>`__ for examples of all plugin formats

Plugin format inheriting tree:

* Solo Plugin
* Multi file Plugin (Abstract)

    * Packed Plugin
    * Directory Plugin

.. _plugin-format-solo:

Solo Plugin
-----------

Solo Plugin consists of a single python ``.py`` source file. It's the plugin format which aims for easy to write and rapid development

Being restricted with the one-file-only file format, some features are missing in solo plugin:

1. Python requirement check is not supported
2. Directly import from other plugin is not supported. Other plugin can only use
   :meth:`~mcdreforged.plugin.server_interface.ServerInterface.get_plugin_instance` to access your plugin
3. Cannot be added to MCDR plugin catalogue

When you only want to create a simple plugin as fast as possible, creating a solo plugin is always a good choice

Example file tree that contains a single solo plugin:

::

    my_mcdr_server/plugins/
     └─ MyPlugin.py

Multi file Plugin
-----------------

Multi file plugin is the collective name for the following two plugin format, :ref:`plugin_dev/plugin_format:Packed Plugin` and :ref:`plugin_dev/plugin_format:Directory Plugin`

The biggest difference between multi file plugin and solo plugin is that, it can consist of multiple files,
rather than being limited into 1 single ``.py`` file. Therefore, more features are supported in a multi file plugin which make it easier to create a general plugin

Packed Plugin
-------------

Packed plugin is a zip type compressed file with file extension name ``.mcdr`` or ``.pyz``. It's the recommended plugin format for distribution

A minimum packed plugin consists of the following files at its zip root

* ``mcdreforged.plugin.json``, contains the metadata of the plugin
* a valid python package with your plugin id

Here's an example file tree of a minimum packed plugin with plugin id ``my_plugin``:

::

    my_mcdr_server/plugins/
     └─ MyPlugin.mcdr
         ├─ my_plugin/
         │   └─ __init__.py
         └─ mcdreforged.plugin.json

Optionally, a packed plugin can have some other useful files that will be recognized by MCDR:

* ``requirements.txt``, indicating the python package requirement of your plugin. It'll be checked before plugin loading
* ``lang/``, a folder storing translation files in json (``.json``) or yaml (``.yml``) format. MCDR will automatically load and register translation files in this folder

You can include any other files or folders inside your packed plugin.
You can access them via :meth:`~mcdreforged.plugin.server_interface.PluginServerInterface.open_bundled_file` method
in :class:`~mcdreforged.plugin.server_interface.ServerInterface`

Here's an example file tree of a valid packed plugin with more possible files:

::

    my_mcdr_server/plugins/
     └─ MyPlugin.mcdr
         ├─ my_plugin/
         │   ├─ __init__.py
         │   └─ my_lib.py
         ├─ my_data/
         │   ├─ default_config.json
         │   └─ some_data.txt
         ├─ lang/
         │   ├─ en_us.json
         │   └─ zh_cn.json
         ├─ mcdreforged.plugin.json
         └─ requirements.txt

In addition to ``.mcdr`` file extension, the python :external:doc:`zip app <library/zipapp>` file extension ``.pyz`` is also valid for a packed plugin.

Although it's not as obvious to be a MCDR plugin as ``.mcdr``, but for those plugins who provide the functionality to run in command line outside MCDR environment,
using `.pyz` extension can explicitly show that they support command line operation


Directory Plugin
----------------

Directory plugin has exactly the same file structure as :ref:`plugin_dev/plugin_format:Packed Plugin`.
The only difference is that all files of a directory plugins are inside a directory instead of a ``.mcdr`` zip file

Directory plugin is mostly used for debug purpose inside the plugin directory of MCDR

Here's an example file tree of a directory plugin:

::

    my_mcdr_server/plugins/
     └─ MyPlugin/
         ├─ my_plugin/
         │   ├─ __init__.py
         │   └─ my_lib.py
         ├─ mcdreforged.plugin.json
         └─ requirements.txt

Directory plugin will always be treated as "modified" during ``!!MCDR reload plugin`` :ref:`command:Hot reloads` command


Linked Directory Plugin
-----------------------

Linked directory plugin is a specialized form of directory plugin, primarily designed for MCDR plugin developers

It functions similarly to a symbolic link (symlink) that links to a regular :ref:`plugin_dev/plugin_format:Directory Plugin`.
Compared to a real symlink, it is easier to create and offers better isolation.

To create a linked directory plugin, imply create a directory that includes a file named ``mcdreforged.linked_directory_plugin.json``:

::

    my_mcdr_server/plugins/
     └─ MyLinkedDirectoryPlugin/
         └─ mcdreforged.linked_directory_plugin.json

The ``mcdreforged.linked_directory_plugin.json`` file contains an object with a sole key ``target``,
which specifies the path to the actual directory plugin to be loaded:


.. code-block:: json

    {
        "target": "/path/to/the/target/directory/plugin/"
    }

The file structure of the target directory plugin appears as follows:

::

    /path/to/the/target/directory/plugin/
     ├─ my_plugin/
     │   ├─ __init__.py
     │   └─ my_lib.py
     ├─ mcdreforged.plugin.json
     └─ requirements.txt
