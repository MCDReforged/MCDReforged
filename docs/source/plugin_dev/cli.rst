
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

Create commonly used folders and generate default configure and permission files, including:

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

Generate default configure and permission files at current working directory

Note that it will overwrite existing files

pack
^^^^

.. code-block::

    python -m mcdreforged pack [-h] [-i INPUT] [-o OUTPUT] [-n NAME]

Pack up your plugin source codes / resources files, from a batch of files, to a ``.mcdr`` packed plugin file

The packing is based on the ``mcdreforged.plugin.json`` metadata file in the input directory. It will pack and only pack the following files/folders into the packed plugin:

* Folder named by the plugin id
* File ``mcdreforged.plugin.json``
* File ``requirements.txt``, if it exists
* Files or folders listed in the `resources <metadata.html#resources>`__ field in metadata


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

    If not given it will use the `archive_name <metadata.html#archive-name>`__ field in plugin metadata

    If it's still not specific, A default name format will be used

    You can use formatter in your name string. String like ``{arg_name}`` in name will be replaced automatically. Use ``{{`` or ``}}`` for single ``{`` or ``}``

    * ``id``: The plugin id
    * ``version``: The version of the plugin

    For example, with ``id=my_plugin`` and ``version=1.2.3``, the following formatting will happen

    * ``MyCustomPlugin-release`` -> ``MyCustomPlugin-release``
    * ``MyCustomPlugin-v{version}`` -> ``MyCustomPlugin-v1.2.3``
    * ``{id}_{version}`` -> ``my_plugin_1.2.3``

    If file extension is included in the name and the file extension is a valid `packed plugin <plugin_format.html#packed-plugin>`__ extension (``.mcdr`` or ``.pyz``), then the included file extension will be used. Otherwise the default ``.mcdr`` file extension will be appended to the end

init_plugin
^^^^^^^^^^^

.. code-block::

    python -m mcdreforged [-q] init_plugin [-h] [-p PATH] [-i ID] [-n NAME] [-d DESCRIPTION] [-a AUTHOR] [-l LINK] [-r RESOURCES] [-e ENTRYPOINT] [-A ARCHIVE_NAME]

Prepare the workspace of MCDR plugin

See :doc:`metadata <metadata>` for more information.

quiet
"""""

    ``-q``, ``--quiet``

    If use quiet mode, then will disable any ask and output, it will use the argument value or the default value

path
""""

    ``-p PATH``, ``--path PATH``

    The workspace which the plugin will be in

    default: current directory

id
""

    ``-i ID``, ``--id ID``

    The identity string of your plugin. It should consist of lowercase letters, numbers and underscores with a length of 1 to 64

    default: current directory name (may not vaild)

name
""""

    ``-n NAME``, ``--name NAME``

    The name of your plugin.

    default: plugin id

description
"""""""""""

    ``-d DESCRIPTION``, ``--description DESCRIPTION``

    The description of you plugin.

    default: This is a plugin for MCDR

author
""""""

    ``-a AUTHOR``, ``--author AUTHOR``

    The author list of the plugins. split with ``:``

    For example:

    ``-a Fallen_Breath`` => ``"author": ["Fallen_Breath"]``

    ``-a Fallen_Breath:Author2`` => ``"author": ["Fallen_Breath", "Author2"]``

    default: None

link
""""

    ``-l LINK``, ``--link LINK``

    The url to your plugin.

    default: None

resources
"""""""""

    ``-r RESOURCES``, ``--resources RESOURCES``

    The resource list, split with ``:``

    For example:

    ``-r lang`` => ``"resources": ["lang"]``

    ``-r lang:example`` => ``"resources": ["lang", "example"]``

    default: None

entrypoint
""""""""""

    ``-e ENTRYPOINT``, ``--entrypoint ENTRYPOINT``

    The entrypoint module of your plugin

    default: None

archive_name
""""""""""""

    ``-A ARCHIVE_NAME``, ``--archive_name ARCHIVE_NAME``

    The file name of generated ``.mcdr`` packed plugin in command ``pack``

    default: None

Create commonly used folders and generate default configure files, including:

* <plugin_id>/<entrypoint>.py
* mcdreforged.plugin.json
* requirements.txt

Example:
""""""""

.. code-block::

    $ mkdir hello_world
    $ cd hello_world
    $ python3 -m mcdreforged init_plugin
    Plugin workspace (default "."): 
    Id (default "hello_world"): 
    Name (default "hello_world"): HelloWorldPlugin
    Description (default "This is a plugin for MCDR"): This is a hello world plugin for MCDR
    Author(s), split with ':': Your Name:Another Author
    Main page link (enter to skip): https://example.com/hello_world_plugin.html
    Resource(s), split with ':' (enter to skip): lang
    Entry point (enter to skip): hello_world.source
    Archive name (enter to skip): 
    Created meta file "./mcdreforged.plugin.json"
    Created entrypoint "./hello_world/source.py"
    $ ls -al
    total 16
    drwxr-xr-x   5 root  staff  160 29 Dec 13:57 .
    drwxr-xr-x  11 root  staff  352 29 Dec 13:55 ..
    drwxr-xr-x   3 root  staff   96 29 Dec 13:57 hello_world
    -rw-r--r--   1 root  staff  385 29 Dec 13:57 mcdreforged.plugin.json
    -rw-r--r--   1 root  staff   80 29 Dec 13:57 requirements.txt
    $ ls -al ./hello_world
    total 8
    drwxr-xr-x  3 root  staff   96 29 Dec 13:57 .
    drwxr-xr-x  5 root  staff  160 29 Dec 13:57 ..
    -rw-r--r--  1 root  staff   24 29 Dec 13:57 source.py
    $ cat ./mcdreforged.plugin.json
    {
        "id": "hello_world",
        "version": "1.0.0",
        "name": "HelloWorldPlugin",
        "description": "This is a hello world plugin for MCDR",
        "dependencies": {
            "mcdreforged": ">=2.0.0"
        },
        "entrypoint": "hello_world.source",
        "author": [
            "Your Name",
            "Another Author"
        ],
        "link": "https://example.com/hello_world_plugin.html",
        "resources": [
            "lang"
        ]
    }
    $ cat ./requirements.txt 
    # Add your python package requirements here, just like regular requirements.txt
    $ cat ./hello_world/source.py 
    # Write your codes here
