
CLI Subcommand - pim
====================

.. code-block:: bash

    mcdreforged pim [-h] {browse,download,pipi} ...

.. versionadded:: v2.13.0

A simple version of Plugin Installer for MCDReforged

browse
------

.. code-block:: bash

    mcdreforged pim browse [-h] [keyword]

Browse plugins in the official plugin catalogue

keyword
~~~~~~~

    Search keyword to filter the plugins

    If not provided, list all plugins


download
--------

.. code-block:: bash

    mcdreforged pim download [-h] [-o OUTPUT] plugin_ids [plugin_ids ...]

    Download given plugins. No dependency resolution will be made, i.e. only the given plugins will be downloaded

plugin_ids
~~~~~~~~~~

    IDs of the plugins to be downloaded

    It can be supplied multiple times

-o, --output
~~~~~~~~~~~~

    Path of the directory to store the downloaded plugins

    Default: current directory


pipi
----

.. code-block:: bash

    mcdreforged pim pipi [-h] [-a ARGS] plugin_paths [plugin_paths ...]

pipi == pip-install

Call ``pip install`` with the requirements.txt file in the given packed plugin to install Python packages

Example usages:

.. code-block:: bash

    mcdreforged pipi MyPlugin.mcdr
    mcdreforged pipi MyPlugin.mcdr /path/to/AnotherPlugin.pyz
    mcdreforged pipi MyPlugin.mcdr --args "-i https://pypi.tuna.tsinghua.edu.cn/simple"

plugin_paths
~~~~~~~~~~~~

    The packed plugin files to be processed

    It can be supplied multiple times

-a, --args
~~~~~~~~~~

    Extra arguments passing to the pip process, e.g. ``--args "--proxy http://localhost:8080"``

