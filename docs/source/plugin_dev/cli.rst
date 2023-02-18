
Command Line Interface
======================

MCDR also provides some useful tool kits via command line interface (CLI). The usage is simple: Add some arguments at the end of the command you launch MCDR

Have a try to display CLI help messages using following command

.. code-block::

    python -m mcdreforged -h

The CLI command format is:

.. code-block::

     mcdreforged [global args] <sub_command> [sub_command args]

Global Arguments
----------------

* ``-q``, ``--quiet``: Disable CLI output
* ``-V``, ``--version``: Print MCDR version and exit

.. versionadded:: v2.8.0
    The ``-V`` and ``--version`` arguments

Sub Commands
------------

start
^^^^^

.. code-block::

    python -m mcdreforged start [-h]

The same as ``python -m mcdreforged``, it launches MCDR

init
^^^^

.. code-block::

    python -m mcdreforged init [-h]

Prepare the working environment of MCDR

Create commonly used folders and generate default configuration and permission files, including:

* logs/
* configs/
* plugins/
* server/
* config.yml
* permission.yml

gendefault
^^^^^^^^^^

.. code-block::

    python -m mcdreforged gendefault [-h]

Generate default configuration and permission files at current working directory

Note that it will overwrite existing files

pack
^^^^

.. code-block::

    python -m mcdreforged pack [-h] [-i INPUT] [-o OUTPUT] [-n NAME]

Pack up your plugin source codes / resources files, from a batch of files, to a ``.mcdr`` :ref:`packed plugin file <plugin_dev/plugin_format:Packed Plugin>`

The packing is based on the ``mcdreforged.plugin.json`` metadata file in the input directory. It will pack and only pack the following files/folders into the packed plugin:

* Folder named by the plugin id
* File ``mcdreforged.plugin.json``
* File ``requirements.txt``, if it exists
* Files or folders listed in the :ref:`plugin_dev/metadata:resources` field in metadata


During plugin packing, all directory with name ``__pycache__`` will be ignored

input
"""""

    ``-i INPUT``, ``--input INPUT``

    The input directory which the plugin is in

    For example, if you have following file structure

    .. code-block::

        work_place/
           my_plugin/
               __init__.py
               my_lib.py
           mcdreforged.plugin.json
           requirements.txt

    Then the ``work_place/`` folder would be the input directory

    default: current directory

output
""""""

    ``-o OUTPUT``, ``--output OUTPUT``

    The output directory to store the generated packed plugin

    default: current directory

name
""""

    ``-n NAME``, ``--name NAME``

    A specific name for the output packed plugin file

    If not given it will use the :ref:`plugin_dev/metadata:archive_name` field in plugin metadata

    If it's still not specific, A default name format will be used

    You can use formatter in your name string. String like ``{arg_name}`` in name will be replaced automatically. Use ``{{`` or ``}}`` for single ``{`` or ``}``

    * ``id``: The plugin id
    * ``version``: The version of the plugin

    For example, with ``id=my_plugin`` and ``version=1.2.3``, the following formatting will happen

    * ``MyCustomPlugin-release`` -> ``MyCustomPlugin-release``
    * ``MyCustomPlugin-v{version}`` -> ``MyCustomPlugin-v1.2.3``
    * ``{id}_{version}`` -> ``my_plugin_1.2.3``

    If file extension is included in the name and the file extension is a valid :ref:`plugin_dev/plugin_format:Packed Plugin` extension (``.mcdr`` or ``.pyz``),
    then the included file extension will be used. Otherwise the default ``.mcdr`` file extension will be appended to the end

