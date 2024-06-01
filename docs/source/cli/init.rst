
CLI Subcommand - init
=====================

.. code-block:: bash

    mcdreforged init [-h] [--config CONFIG_FILE] [--permission PERMISSION_FILE]

Prepare the working environment of MCDR

Create commonly used folders and generate default configuration and permission files, including:

* logs/
* configs/
* plugins/
* server/
* config.yml (can be altered by argument)
* permission.yml (can be altered by argument)

--config
--------

    Path to the MCDReforged configuration file

    Default: ``config.yml``

    .. versionadded:: v2.13.0

--permission
------------

    Path to the MCDReforged permission file

    Default: ``permission.yml``

    .. versionadded:: v2.13.0
