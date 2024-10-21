
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

.. code-block:: bash

     mcdreforged [global_args] <sub_command> [sub_command_args]


.. note::

    You can always use ``python -m mcdreforged`` to run MCDR in all environment, in case the ``mcdreforged`` command does not work,
    e.g. environment variable ``PATH`` is not well configured

    .. tab:: Windows

        .. code-block:: bash

            python -m mcdreforged [global_args] <sub_command> [sub_command_args]

    .. tab:: Linux

        .. code-block:: bash

            python3 -m mcdreforged [global_args] <sub_command> [sub_command_args]

Direct Launch
-------------

.. code-block:: bash

    mcdreforged

If no argument is given, launch MCDR with default arguments


Global Arguments
----------------

* ``-h``, ``--help``: Show help message and exit
* ``-V``, ``--version``: Print MCDR version and exit
* ``-q``, ``--quiet``: Disable CLI output

.. versionadded:: v2.8.0
    The ``-V`` and ``--version`` arguments

.. prompt-mcdr-version:: bash $ auto

    $ mcdreforged -V
    MCDReforged @@MCDR_VERSION@@

Sub Commands
------------

.. code-block:: bash

    mcdreforged [-h] [-q] [-V] {gendefault,init,pack,pim,reformat-config,start} ...

.. toctree::
   :maxdepth: 1

   gen-default<gen_default.rst>
   init<init.rst>
   pack<pack.rst>
   pim<pim.rst>
   reformat-config<reformat_config.rst>
   start<start.rst>
