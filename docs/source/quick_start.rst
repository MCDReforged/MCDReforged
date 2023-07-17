
Quick Start
===========

This is a quick start tutorial of `MCDReforged <https://github.com/Fallen-Breath/MCDReforged>`__ (abbreviated as MCDR, omitted below)

Requirements
------------

MCDR requires Python3 runtime. The Python version need to be at least 3.8.
The detailed Python version requirements are as shown in the table below

.. list-table::
   :header-rows: 1

   * - MCDR version
     - Python requirement
   * - < 2.10
     - >= 3.6
   * - >= 2.10
     - >= 3.8

Install
-------

MCDR is available in `pypi <https://pypi.org/project/mcdreforged>`__, which means it can be installed via the ``pip`` command:

.. tab:: Windows

    .. code-block:: bat

        pip install mcdreforged

.. tab:: Linux

    .. code-block:: bash

        pip3 install mcdreforged

For Chinese users, you can added a ``-i https://pypi.tuna.tsinghua.edu.cn/simple`` prefix to the command to use `Tsinghua tuna mirror <https://mirrors.tuna.tsinghua.edu.cn/help/pypi/>`__ to speed up the installation:

.. tab:: Windows

    .. code-block:: bat

        pip install mcdreforged -i https://pypi.tuna.tsinghua.edu.cn/simple

.. tab:: Linux

    .. code-block:: bash

        pip3 install mcdreforged -i https://pypi.tuna.tsinghua.edu.cn/simple

**DO NOT** download the source files of MCDR and execute them directly, unless you're a developer of MCDR and you know what you are doing

After MCDR has been installed using pip, you can verify the installation with the following command:

.. code-block-mcdr-version:: bash

    $ mcdreforged
    MCDReforged v@@MCDR_VERSION@@

Start up
--------

Let's say your are going to start MCDR in a folder named ``my_mcdr_server``. Then you can run the following commands to initialize the environment for MCDR first:

.. code-block:: bash

    cd my_mcdr_server
    mcdreforged init

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

    mcdreforged

Upgrade
-------

With the help of `pypi <https://pypi.org/project/mcdreforged/>`__, MCDR can be easily upgraded via a single command

.. tab:: Windows

    .. code-block:: bat

        pip install mcdreforged -U

.. tab:: Linux

    .. code-block:: bash

        pip3 install mcdreforged -U

That's it! 

For Chinese users, you can use tuna mirror to speed up the upgrading too

.. tab:: Windows

    .. code-block:: bat

        pip install mcdreforged -U -i https://pypi.tuna.tsinghua.edu.cn/simple

.. tab:: Linux

    .. code-block:: bash

        pip3 install mcdreforged -U -i https://pypi.tuna.tsinghua.edu.cn/simple

Development builds are available in `Test PyPi <https://test.pypi.org/project/mcdreforged/#history>`__, you can install them if you have special needs

Next
----

Now, you've got the basics of how to set up, run, and upgrade MCDR. What's next? Feel free to check out other parts of the documentation

* Check how to configure MCDR: :doc:`/configuration`
* Discover the MCDR command system: :doc:`/command`
* Take a look at MCDR's built-in permission system: :doc:`/permission`
* Learn more about MCDR command line interface: :doc:`/plugin_dev/cli`
* Dive into the document to explore more about MCDR ...

