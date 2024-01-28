
Docker
======

If you want to run MCDR in Docker, here's a list of official Docker images that might fit your needs

.. note::

    If you run MCDR in a docker container, the server started by MCDR will inevitably run in the same container.
    Therefore, you need to install the dependencies/runtime required for running the server in the container,
    to properly run MCDR and the server in the docker container.

    For example, if you want to run MCDR that manages a Minecraft server in a Docker container,
    you need to set up the Java runtime environment required for running the Minecraft server in the container

Common Usages
-------------

The following image usages are the same for all types of images listed in this page

Quick start
^^^^^^^^^^^

Quick test if docker and mcdreforged image works

.. code-block:: bash

    docker run -it --rm mcdreforged/mcdreforged

Example output:

.. code-block:: text

    MCDReforged 2.13.0 is starting up
    MCDReforged is open source, u can find it here: https://github.com/Fallen-Breath/MCDReforged
    [MCDR] [13:05:59] [MainThread/INFO]: Language has set to en_us
    [MCDR] [13:05:59] [MainThread/INFO]: Encoding / Decoding method has set to utf8 / utf8
    [MCDR] [13:05:59] [MainThread/INFO]: Plugin directory list:
    [MCDR] [13:05:59] [MainThread/INFO]: - plugins
    [MCDR] [13:05:59] [MainThread/INFO]: Handler has set to vanilla_handler
    [MCDR] [13:05:59] [MainThread/INFO]: MCDReforged is running on Python 3.11.7 environment
    [MCDR] [13:05:59] [TaskExecutor/INFO]: Refreshing all plugins
    [MCDR] [13:05:59] [TaskExecutor/INFO]: No plugin has changed; Active plugin amount: 2
    [MCDR] [13:05:59] [MainThread/INFO]: Starting the server with command "echo Hello world from MCDReforged"
    [MCDR] [13:05:59] [MainThread/INFO]: Server is running at PID 10
    [Server] Hello world from MCDReforged
    [MCDR] [13:05:59] [MainThread/INFO]: Server process stopped with code 0
    [MCDR] [13:05:59] [MainThread/INFO]: Server stopped
    [MCDR] [13:05:59] [MainThread/INFO]: Stopping MCDR
    [MCDR] [13:05:59] [MainThread/INFO]: Stopping advanced console
    [MCDR] [13:05:59] [MainThread/INFO]: bye

Persist your server data
^^^^^^^^^^^^^^^^^^^^^^^^

For a production usage, you need to persist the working directory: ``/mcdr``,
where all MCDR related files and the server folder is in

.. code-block:: bash

    docker run --name my_mcdr_container -v /path/to/my/server:/mcdr mcdreforged/mcdreforged


Python package installation
^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you want to installed custom python packages, here's the suggested steps:

1. Mount path /root/.local/lib/python${PYTHON_VERSION}/site-packages/ to a volume or a local directory

    - This step is optional. Installing without the directory mounted results in the loss of the new packages when the container is removed

    - PYTHON_VERSION is the major + minor version of the python interpreter, e.g. 3.11

2. Use pip3 to install whatever packages you want like usual. The --user argument is set automatically globally

    .. code-block:: bash

        docker exec -it my_mcdr_container pip3 install apscheduler

Image Variants
--------------

Base Image
^^^^^^^^^^

- Image: ``mcdreforged/mcdreforged``
- Docker Hub: https://hub.docker.com/r/mcdreforged/mcdreforged

This image contains the basic runtime environment of MCDReforged.
It can be used as the base image to build your custom runtime with MCDR, or

Tag format

Extra Images
^^^^^^^^^^^^

- Image: ``mcdreforged/mcdreforged-extra``
- Docker Hub: https://hub.docker.com/r/mcdreforged/mcdreforged-extra

Tag format: The same as :ref:`docker:Base Image`

OpenJDK Images
^^^^^^^^^^^^^^

Source codes
------------

https://github.com/Fallen-Breath/MCDReforged-Docker
