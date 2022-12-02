
Quick Start
===========

This is a quick start tutorial of `MCDReforged <https://github.com/Fallen-Breath/MCDReforged>`__ (abbreviated as MCDR, omitted below)

Requirements
------------

MCDR requires python3 runtime. The python version need to be at least 3.6

Install
-------

MCDR is available in `pypi <https://pypi.org/project/mcdreforged>`__. It can be installed via ``pip`` command

.. code-block:: bash

    pip install mcdreforged

For Chinese users, you can added a ``-i https://pypi.tuna.tsinghua.edu.cn/simple`` prefix to the command to use `Tsinghua tuna mirror <https://mirrors.tuna.tsinghua.edu.cn/help/pypi/>`__ to speed up the installation

.. code-block:: bash

    pip install mcdreforged -i https://pypi.tuna.tsinghua.edu.cn/simple

**DO NOT** download the source files of MCDR and execute them directly, unless you're a developer of MCDR and you know what you are doing

Start up
--------

Let's say your are going to start MCDR in a folder named ``my_mcdr_server``. Then you can run the following commands to initialize the environment for MCDR first:

.. code-block:: bash

    cd my_mcdr_server
    python -m mcdreforged init

MCDR will generated the default configuration and permission files, as well as some default folders. The file structure will be like this

.. code-block::

    my_mcdr_server/
     ├─ config/
     ├─ logs/
     │   └─ MCDR.log
     ├─ plugins/
     ├─ server/
     ├─ config.yml
     └─ permission.yml

Now put your server files into the server folder (``server`` by default), then modify the configuration file ``config.yml`` and permission file ``permission.yml`` correctly

After that you can launch MCDR, and it will start handling the server correctly

.. code-block:: bash

    python -m mcdreforged

Upgrade
-------

With the help of `pypi <https://pypi.org/project/mcdreforged/>`__, MCDR can be easily upgraded via a single command

.. code-block:: bash

    pip install mcdreforged -U

That's it! 

For Chinese users, you can use tuna mirror to speed up the upgrading too

.. code-block:: bash

    pip install mcdreforged -U -i https://pypi.tuna.tsinghua.edu.cn/simple

Development builds are available in `Test PyPi <https://test.pypi.org/project/mcdreforged/#history>`__, you can install them if you have special needs

