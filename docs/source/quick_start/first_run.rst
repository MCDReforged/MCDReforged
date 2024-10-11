
First Run
=========

Now you have installed MCDR, it's time to run it for the first time

.. note::

    Most common use of MCDR is to control a Minecraft server, so we also take this as the demonstrated use case here

.. tip::

    To manage Minecraft server with MCDR, It is recommended to have basic knowledge of common Minecraft server softwares
    
    Which means, you should know:

    * The Minecraft server softwares: what they are, how to configure (one of) them
    * Start command of Minecraft server: what it is, what its arguments mean
    * Console of the server: what it prints, what command can you send to it
    * YAML and JSON files: what they are, how to edit them
    
    If you have not, Google is your friend

Prepare
-------

To manage a Minecraft server with MCDR, you should have a **well-configured** Minecraft server software

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
    ├── minecraft_server.jar
    ├── server.properties
    ├── usercache.json
    └── whitelist.json

With this command to start it:

.. code-block:: bash

    java -Xms1G -Xmx2G -jar minecraft_server.jar nogui

You can also use other server software, such as Fabric, Spigot, Paper, etc.

.. tip::

    Configure and troubleshoot your server software **BEFORE** you introduce MCDR. Otherwise, you can't distinguish whether a problem is caused by MCDR or your server software

    MCDR was born as a daemon for common server softwares of Minecraft: Java Edition. Most plugins are predicated on that. If you want to run MCDR with a Bedrock Edition server, consider using Java Edition server software with `GeyserMC <https://geysermc.org/>`__ to provide Bedrock Edition compatibility

    Of course, if you don't need to make use of the plugin ecosystem designed for Java Edition server, you can run any programs you want with MCDR

Initialize
----------

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

Animated demo:

.. asciinema:: resources/init.cast
    :rows: 10

|

Configure
---------

Server Software
~~~~~~~~~~~~~~~

Remember the server software you have prepared? Put it into the ``server`` folder. The directory structure should be something like this:

.. code-block:: diff

        my_mcdr_server/
        ├─ config/
        ├─ logs/
        │   └─ MCDR.log
        ├─ plugins/
        ├─ server/
    ++  │   ├─ ...
    ++  │   ├─ minecraft_server.jar
    ++  │   └─ server.properties
        ├─ config.yml
        └─ permission.yml

Config File
~~~~~~~~~~~

Then, edit the ``config.yml`` file to configure MCDR. You can find more information about this in :doc:`/configuration`

For most users, there are 4 parts of the configuration that you need to be aware of

- :ref:`configuration:language`: the language using in MCDR
- :ref:`configuration:start_command`: how MCDR starts your server
- :ref:`configuration:handler`: how MCDR read your server outputs
- :ref:`configuration:encoding, decoding`: how MCDR handles the server IO stream

Read each section carefully and make sure you filled in the correct values.

As a simple example, this is the ones you need to aware for a vanilla Minecraft 1.21 server with Java 21:

.. code-block:: yaml

    start_command: java -Dfile.encoding=UTF-8 -Dstdout.encoding=UTF-8 -Dstderr.encoding=UTF-8 -Xms1G -Xmx2G -jar minecraft_server.jar nogui

    handler: vanilla_handler

    encoding: utf8
    decoding: utf8

If you're confusing why this command is much logner than we mentioned earlier, read the **encoding, decoding** section again

RCON
~~~~

Optionally, you may enable RCON protocol to make some specific plugins work properly or more efficiently. Check the details in :ref:`configuration:rcon`

Run
---

Now, you should be able to launch MCDR, and it should start handling the server correctly

.. prompt:: bash

    mcdreforged

An animated demo configured as above:

.. asciinema:: resources/run.cast

|

Also, test MCDR in game:

.. asciinema:: resources/ingame.cast
    :rows: 2
    :theme: nord

|
