
First Run
=========

Now you have installed MCDR, it's time to run it for the first time...?

.. note::

    We assume you have basic knowledge of managing a Minecraft server with one of the common server software. Which means, you should know:

    * The Minecraft server software: what is it, how to configure it
    * Start command of Minecraft server: what is it, and what its arguments mean
    * Console of the server: what it prints, commands you can send to it
    * YAML and JSON files: what they are, how to edit them
    
    If you have not, Google is your friend.

Minecraft Server Software
-------------------------

Most common use of MCDR is to control a Minecraft server. In order to do that, you should have a well-configurated Minecraft server software


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

With this command to start it:

.. code-block:: bash

    java -Xmx1024M -Xms1024M -jar server.jar nogui

You can also use other server software, such as Fabric, Spigot, Paper, etc.

.. note::

    MCDR was born as a daemon for server softwares of Minecraft: Java Edition. Most plugins are predicated on that. If you want to run MCDR with a Bedrock Edition server, consider using Java Edition server software with `GeyserMC <https://geysermc.org/>`__ to provide Bedrock Edition compatibility

    Of course, if you don't need the MCDR plugin ecosystem, you can manage almost any cli program with MCDR

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

Then, edit the ``config.yml`` file to configure MCDR. You can find more information about this in :doc:`/configuration`

For most users, the configuration items that you need to be aware of are:

- :ref:`configuration:Basic Configuration`
- :ref:`configuration:Server Configuration`

As a simple example, this is all items you need to be aware of to run a vanilla Minecraft 1.21 server:

.. code-block:: yaml

    start_command: java -Dfile.encoding=UTF-8 -Dstdout.encoding=UTF-8 -Dstderr.encoding=UTF-8 -Xmx1024M -Xms1024M -jar server.jar nogui

    handler: vanilla_handler

    encoding: utf8
    decoding: utf8

Permissions
~~~~~~~~~~~

MCDR supports permissions. You can configure permissions in the ``permission.yml`` file. You can find more information about this in :doc:`/permission`

Run
---

Now, you should be able to launch MCDR, and it should start handling the server correctly

.. code-block:: bash

    mcdreforged
