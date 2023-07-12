
Command Line Interface
======================

MCDR also provides some useful tool kits via command line interface (CLI). The usage is simple: Add some arguments at the end of the command you launch MCDR

Starting from v2.10, MCDR will generate a startup script under the Python executable path during installation.
Therefore, you can directly use the ``mcdreforged`` command to start MCDR

Have a try to display CLI help messages using following command

.. tab:: >= v2.10

    .. code-block:: bash

        mcdreforged -h

.. tab:: < v2.10 (Windows)

    .. code-block:: bash

        python -m mcdreforged -h

.. tab:: < v2.10 (Linux)

    .. code-block:: bash

        python3 -m mcdreforged -h

The following document will use ``mcdreforged`` as the command for demonstration.
For MCDR < v2.10, you need to add the ``python -m`` prefix to the commands used below

The overall CLI command format is:

.. code-block::

     mcdreforged [global_args] <sub_command> [sub_command_args]

Global Arguments
----------------

* ``-h``, ``--help``: Show help message and exit
* ``-V``, ``--version``: Print MCDR version and exit
* ``-q``, ``--quiet``: Disable CLI output

.. versionadded:: v2.8.0
    The ``-V`` and ``--version`` arguments

Sub Commands
------------

start
^^^^^

.. code-block:: bash

    mcdreforged start [-h]

The same as ``mcdreforged``, it launches MCDR

init
^^^^

.. code-block:: bash

    mcdreforged init [-h]

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

.. code-block:: bash

    mcdreforged gendefault [-h]

Generate default configuration and permission files at current working directory

Note that it will overwrite existing files

pack
^^^^

.. code-block:: bash

    mcdreforged pack [-h] [-i INPUT] [-o OUTPUT] [-n NAME]

Pack up your plugin source codes / resources files, from a batch of files, to a ``.mcdr`` :ref:`packed plugin file <plugin_dev/plugin_format:Packed Plugin>`

The packing is based on the ``mcdreforged.plugin.json`` metadata file in the input directory. It will pack and only pack the following files/folders into the packed plugin:

* Folder named by the plugin id
* File ``mcdreforged.plugin.json``
* File ``requirements.txt``, if it exists
* Files or folders listed in the :ref:`plugin_dev/metadata:resources` field in metadata

input
"""""

    ``-i INPUT``, ``--input INPUT``

    The input directory which the plugin is in

    For example, if you have following file structure

    .. code-block:: bash

        work_place/
           my_plugin/
               __init__.py
               my_lib.py
           mcdreforged.plugin.json
           requirements.txt

    Then the ``work_place/`` folder would be the input directory

    Default: current directory

output
""""""

    ``-o OUTPUT``, ``--output OUTPUT``

    The output directory to store the generated packed plugin

    Default: current directory

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

ignore patterns
"""""""""""""""

    ``--ignore-patterns IGNORE_PATTERN [IGNORE_PATTERN ...]``

    A list of gitignore-like pattern, indicating a set of files and directories to be excluded during plugin packing

    It supports a subset of `.gitignore syntax <https://git-scm.com/docs/gitignore#_pattern_format>`__. Here are some differences:

    *   When using normal patterns with  patterns, i.e. patterns starts with ``!``,
        whether a file is excluded depends on the type of the latest matching pattern in the pattern list
    *   Tailing space character escaping is not supported
    *   Heading hashtag character escaping is not supported

    It overwrites values from :ref:`-\\\\-ignore-file <plugin_dev/cli:ignore file>`. It will filter nothing if the value is empty, or the file doesn't exist or not readable

    Notes: The root directory when calculating related path is the current working directory, not the :ref:`plugin_dev/cli:input` directory

    Default: empty list

    Example:

    .. code-block:: bash

        --ignore-patterns __pycache__ foobar/*.txt **/trash/bin/

    .. versionadded:: v2.8.0

ignore file
"""""""""""

    ``--ignore-file IGNORE_FILE``

    The path to a utf8-encoded gitignore-like file. It's content will be used as the :ref:`-\\\\-ignore-patterns <plugin_dev/cli:ignore patterns>` parameter.

    Default: ``".gitignore"``, which means that it will automatically read the .gitignore file in the current working directory

    Here's a table of the eventually behavior for ``--ignore-patterns`` and ``--ignore-file``:

    .. list-table::
        :header-rows: 1

        * - ``--ignore-patterns``
          - ``--ignore-file``
          - Behavior
        * - Unset
          - Unset
          - Read the ignore list from .gitignore
        * - Unset
          - Set
          - Read the ignore list from given file
        * - Set
          - Unset
          - Use patterns from ``--ignore-patterns``
        * - Set
          - Set
          - Use patterns from ``--ignore-patterns``

    .. versionadded:: v2.8.0


shebang
"""""""

    ``--shebang SHEBANG``

    Add a ``#!``-prefixed `shebang <https://en.wikipedia.org/wiki/Shebang_(Unix)>`__ line at the beginning of the packed plugin.
    It will also make the packed plugin executable on POSIX

    By default no shebang line will be added, and not make the packed plugin file executable

    If your packed plugin is a valid python :external:doc:`zip app <library/zipapp>` archive, i,e. it contains a working ``__main__.py``,
    you can use this option to make your packed plugin executable in bash environment

    Example:

    .. code-block:: bash

        --shebang "/usr/bin/env python3"

    .. versionadded:: v2.8.0
