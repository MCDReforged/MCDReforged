
Quick Start
===========

This is a quick start tutorial of `MCDReforged <https://github.com/MCDReforged/MCDReforged>`__ (abbreviated as MCDR, omitted below)

Requirements
------------

MCDR is written and runs in Python 3. The Python version need to be at least 3.8.
The detailed Python version requirements are as shown in the table below

.. list-table::
   :header-rows: 1

   * - MCDR version
     - Python requirement
   * - < 2.10
     - >= 3.6
   * - >= 2.10
     - >= 3.8

Common use of MCDR is to control a Minecraft server. In order to do that, you should have a configurated Minecraft server software

For example, this is a typical directory structure of vanilla Minecraft server:

.. code-block:: text

    server/
    ├── libraries/
    ├── logs/
    ├── versions/
    ├── world/
    ├── banned-ips.json
    ├── banned-players.json
    ├── eula.txt
    ├── ops.json
    ├── server.jar
    ├── server.properties
    ├── usercache.json
    └── whitelist.json

With a command to start it:

.. code-block:: bash

    java -Xmx1024M -Xms1024M -jar server.jar nogui

You can also use other server software, such as Fabric, Spigot, Paper, etc

.. note::

    MCDR was born as a daemon for server softwares of Minecraft: Java Edition. Most plugins are predicated on this

    If you want to build a Bedrock Edition server with MCDR, consider using `GeyserMC <https://geysermc.org/>`__ with a Java Edition server software

    Of course, if you don't need the MCDR plugin ecology, then you can manage almost any cli program with MCDR

Install or Upgrade
------------------

**DO NOT** download the source files of MCDR and execute them directly, unless you're a developer of MCDR and you know what you are doing

Using pipx
~~~~~~~~~~

Since `PEP 668 <https://peps.python.org/pep-0668/>`__, globally installing MCDR using pip is not available on Linux and Mac OS. As a workaround, we recommend using `pipx <https://pipx.pypa.io/>`__ if you want MCDR globally installed

.. code-block:: bash

    $ pipx install mcdreforged

When a new version available, you may upgrade MCDR by:

.. code-block:: bash

    $ pipx upgrade mcdreforged

.. note::

    In this way, MCDR will be installed in a virtual environment. Python packages required by MCDR plugins should be installed by:

    .. code-block:: bash

        $ pipx inject mcdreforged <package_name>
        $ pipx inject mcdreforged -r requirements.txt
    
    Or you may use the :ref:`\!!MCDR command <command/mcdr:Plugin management>` to install plugins with their dependencies


Using pip
~~~~~~~~~

If you're on Windows, or in a virtual environment you created, you may use pip to install MCDR:

.. tab:: Windows

    .. code-block:: bat

        pip install mcdreforged

.. tab:: Linux

    .. code-block:: bash

        (venv) $ pip3 install mcdreforged

When a new version available, you may upgrade MCDR by:

.. tab:: Windows

    .. code-block:: bat

        pip install mcdreforged -U

.. tab:: Linux

    .. code-block:: bash

        (venv) $ pip3 install mcdreforged -U

Index Urls
~~~~~~~~~~

For Chinese users, you can added a ``-i https://pypi.tuna.tsinghua.edu.cn/simple`` prefix to the command above, to speed up the installation by using `Tsinghua tuna mirror <https://mirrors.tuna.tsinghua.edu.cn/help/pypi/>`__. For example:

.. code-block:: bash

    pipx install -i https://pypi.tuna.tsinghua.edu.cn/simple mcdreforged
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple mcdreforged

Using Docker
~~~~~~~~~~~~

You may also use Docker to run MCDR. See :doc:`docker` for more details

Development Builds
~~~~~~~~~~~~~~~~~~

Development builds are available in `Test PyPI <https://test.pypi.org/project/mcdreforged/#history>`__, you can install them if you have special needs

Initialize
----------

After MCDR has been installed, you can verify the installation with the following command:

.. code-block-mcdr-version:: bash

    $ mcdreforged
    MCDReforged v@@MCDR_VERSION@@

Let's say your are going to start MCDR in a folder named ``my_mcdr_server``. Then you can run the following commands to initialize the environment for MCDR:

.. code-block:: bash

    cd my_mcdr_server
    mcdreforged init

MCDR will generate its default structure like this:

.. code-block::

    my_mcdr_server/
     ├─ config/
     ├─ logs/
     │   └─ MCDR.log
     ├─ plugins/
     ├─ server/
     ├─ config.yml
     └─ permission.yml

Configure
---------

Server Software
~~~~~~~~~~~~~~~

Remember the server software you have prepared? Put it into the ``server`` folder. The directory structure should be something like this:

.. code-block::

    my_mcdr_server/
     ├─ config/
     ├─ logs/
     │   └─ MCDR.log
     ├─ plugins/
     ├─ server/
     │   ├─ ...
     │   ├─ server.jar
     │   └─ server.properties
     ├─ config.yml
     └─ permission.yml

Config File
~~~~~~~~~~~

Then, edit the ``config.yml`` file to configure MCDR. You can find more information about this in :doc:`configuration`

For most users, the configuration items that you need to be aware of are:

- :ref:`configuration:Basic Configuration`
- :ref:`configuration:Server Configuration`

Permissions
~~~~~~~~~~~

MCDR supports permissions. You can configure permissions in the ``permission.yml`` file. You can find more information about this in :doc:`/permission`

Run
---

Now, you should be able to launch MCDR, and it should start handling the server correctly

.. code-block:: bash

    mcdreforged

Next
----

Now, you've got the basic knowledges of MCDR. What's next? Feel free to check out other parts of the documentation

* MCDR has its own command system: :doc:`/command/index`
* MCDR has a fancy plugin ecosystem: `Plugin Catalogue <https://github.com/MCDReforged/PluginCatalogue>`__
* MCDR's CLI provide some tools for you: :doc:`/cli/index`
* Create your first plugin: :doc:`/plugin_dev/index`

Dive into the documentation to explore more about MCDR!

Troubleshooting
---------------

Here listed some common problems and their solutions

- **MCDR outputs garbled text in game.**

    Usually, this is caused by the console encoding. MCDR use your system encoding as default, but it may fail. Try to use UTF-8 in everything related to the server. See :ref:`configuration:encoding, decoding`

- **Commands not working in game.**

    MCDR handle commands by listening to the server's console output.

    Make sure you are using the correct :ref:`Server Handler <configuration:handler>`. If your server software is not supported by built-in handlers, you may need to :ref:`customize your own handler <customize/handler:Server Handler>`

    If your server output is modified by mods or plugins, the handler may not be able to recognize the outputs. Try to disable all mods and plugins to see if the problem solved. If so, you may need to :ref:`customize your own handler <customize/handler:Server Handler>` to handle the modified outputs


