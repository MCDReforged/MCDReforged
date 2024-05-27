
CLI Subcommand - pim
====================

.. code-block:: bash

    mcdreforged pim [-h] {browse,download,pipi} ...

.. versionadded:: v2.13.0

browse
------

.. code-block:: bash

    mcdreforged pim browse [-h] [keyword]

download
--------

.. code-block:: bash

    mcdreforged pim download [-h] [-o OUTPUT] plugin_ids [plugin_ids ...]

pipi
----

pipi == pip-install

.. code-block:: bash

    mcdreforged pim pipi [-h] [-a ARGS] plugin_paths [plugin_paths ...]

Call ``pip install`` with the requirements.txt file in the given packed plugin to install Python packages

Example usages:

.. code-block:: bash

    mcdreforged pipi MyPlugin.mcdr
    mcdreforged pipi MyPlugin.mcdr /path/to/AnotherPlugin.pyz
    mcdreforged pipi MyPlugin.mcdr --args "-i https://pypi.tuna.tsinghua.edu.cn/simple"

plugin_paths
~~~~~~~~~~~~

    The packed plugin files to be processed

args
~~~~

    Extra arguments passing to the pip process, e.g. ``--args "--proxy http://localhost:8080"``

start
^^^^^

.. code-block:: bash

    mcdreforged start [-h] [--auto-init] [--config CONFIG_FILE] [--permission PERMISSION_FILE]

The same as ``mcdreforged``, it launches MCDR

auto-init
"""""""""

    Automatically initialize the working environment if needed
