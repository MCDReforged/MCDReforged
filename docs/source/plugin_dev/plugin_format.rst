
Plugin Format
=============

There are 3 types of valid format of a MCDR plugin, each of them has its own advantages and disadvantages depending on the user cases

See `this repository <https://github.com/MCDReforged/MCDReforged-ExamplePlugin>`__ for examples of all plugin formats

Plugin format inheriting tree:

* Solo Plugin
* Packed Plugin (Abstract)

    * Zipped Plugin
    * Directory Plugin


Solo Plugin
-----------

Solo Plugin consists of a single python ``.py`` source file. It's the plugin format which aims for easy to write and rapid development

Being restricted with the one-file-only file format, some features are missing in solo plugin:

1. Python requirement check is not supported
2. Directly import from other plugin is not supported. Other plugin can only use `get_plugin_instance <classes/ServerInterface.html#get-plugin-instance>`__ to access your plugin
3. Cannot be added to MCDR plugin catalogue

When you only want to create a simple plugin as fast as possible, creating a solo plugin is always a good choice

Packed Plugin
-------------

Packed plugin is the collective name for the following two plugin format, `zipped plugin <#zipped-plugin>`__ and `directory plugin <#directory-plugin>`__

The biggest difference between packed plugin and solo plugin is that, it can consist of multiple files, rather than being limited into 1 single ``.py`` file. Therefore, more features are supported in a packed plugin which make it easier to create a general plugin

Zipped Plugin
-------------

Zipped plugin is a zip type compressed file with file extension name ``.mcdr``. It's the recommended plugin format for distribution

A minimum zipped plugin consists of the following files at its zip root

* ``mcdreforged.plugin.json``, contains the metadata of the plugin
* a valid python package with your plugin id

Here's an example file tree of a minimum zipped plugin with plugin id ``my_plugin``:

::

   MyPlugin.mcdr
       my_plugin/
           __init__.py
       mcdreforged.plugin.json

Optionally, a zipped plugin can have some other useful files that will be recognized by MCDR:

* ``requirements.txt``, indicating the python package requirement of your plugin. It'll be checked before plugin loading
* ``lang/``, a folder storing translation files in json (``.json``) or yaml (``.yml``) format. MCDR will automatically load and register translation files in this folder

You can include any other files or folders inside your zipped plugin. You can access them via `open_bundled_file <classes/ServerInterface.html#open-bundled-file>`__ method in `ServerInterface <classes/ServerInterface.html>`__

Here's an example file tree of a valid zipped plugin with more possible files:

::

   MyPlugin.mcdr
       my_plugin/
           __init__.py
           my_lib.py
       my_data/
           default_config.json
           some_data.txt
       lang/
           en_us.json
           zh_cn.json
       mcdreforged.plugin.json
       requirements.txt


Directory Plugin
----------------

Directory plugin has exactly the same file structure as `zipped plugin <#zipped-plugin>`__. The only difference is that all files of a directory plugins are inside a directory instead of a ``.mcdr`` zip file

Directory plugin is mostly used for debug purpose inside the plugin directory of MCDR

Here's an example file tree of a directory plugin:

::

   MyPlugin/
       my_plugin/
           __init__.py
           my_lib.py
       mcdreforged.plugin.json
       requirements.txt

Directory plugin will always be treated as "modified" during ``!!MCDR reload plugin`` `hot reload <../command.html#hot-reloads>`__ command
