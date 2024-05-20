
Docker
======

If you want to run MCDR in Docker, here's a list of official Docker images that might fit your needs

Check the mcdreforged docker organization page for the full image list: https://hub.docker.com/r/mcdreforged

.. note::

    If you run MCDR in a docker container, the server started by MCDR will inevitably run in the same container.
    Therefore, you need to install the dependencies/runtime required for running the server in the container,
    to properly run MCDR and the server in the docker container.

    For example, if you want to run MCDR that manages a Minecraft server in a Docker container,
    you need to set up the Java runtime environment required for running the Minecraft server in the container

Image Usages
------------

The following image usages are the same for all types of images listed in this page

Basic Information
^^^^^^^^^^^^^^^^^

- OS distribution: debian (The same as what the official `python <https://hub.docker.com/_/python>`__ image use by default)
- Image user: root
- Working directory: ``/mcdr``
- Python package installation location:

Quick test
^^^^^^^^^^

Quick test if docker and mcdreforged image works

.. code-block:: bash

    docker run -it --rm mcdreforged/mcdreforged

Example output:

.. code-block:: text

    MCDReforged 2.13.0 is starting up
    MCDReforged is open source, u can find it here: https://github.com/Fallen-Breath/MCDReforged
    [MCDR] [13:05:59] [MainThread/INFO]: Language is set to en_us
    [MCDR] [13:05:59] [MainThread/INFO]: Encoding / Decoding method is set to utf8 / utf8
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

1. Mount path ``/root/.local/lib/python${PYTHON_VERSION}/site-packages/`` to a volume or a local directory,
   so installed python packages can be persist between container recreations

    - This step is optional if you don't care about package loss on container removal

    - ``PYTHON_VERSION`` is the major + minor version of the python interpreter, e.g. ``3.11``

    - You can confirm the path by executing the following command

        .. code-block:: bash

            docker run -it --rm mcdreforged/mcdreforged ls -l /root/.local/lib

2. Use pip3 to install whatever packages you want like usual. The ``--user`` argument is set automatically globally

    .. code-block:: bash

        docker exec -it my_mcdr_container pip3 install apscheduler

Image Variants
--------------

Base Image
^^^^^^^^^^

- Image: ``mcdreforged/mcdreforged``
- Docker Hub: https://hub.docker.com/r/mcdreforged/mcdreforged
- Source code: https://github.com/Fallen-Breath/MCDReforged/tree/master/docker

This image contains the basic runtime environment of MCDReforged, built based on the official `python <https://hub.docker.com/_/python>`__ image

It can be used as the base image to build your custom runtime with MCDR

.. code-block:: dockerfile

    FROM mcdreforged/mcdreforged
    RUN <<EOT
    # Install system packages
    apt-get update
    apt-get install -y curl
    # Install Python packages
    pip3 install apscheduler
    # Do whatever you want for customization
    EOF

Tag prefixes:

- ``latest`` means the latest MCDR version
- ``2.13.0``, ``2.13`` mean the specified MCDR version
- ``master``, ``dev`` mean the development build from the specified GitHub git branches

Tag suffixes:

- ``-slim`` means it's based on the ``-slim`` variant of the official `python <https://hub.docker.com/_/python>`__ image
- ``-py3.12`` means the python version used by the image, accurate to the minor version number. Default: ``3.11``, which is usually the second newest python version

.. code-block:: text

    mcdreforged/mcdreforged:latest
    mcdreforged/mcdreforged:latest-slim
    mcdreforged/mcdreforged:2.13.0
    mcdreforged/mcdreforged:2.13.0-slim
    mcdreforged/mcdreforged:2.13.0-py3.11
    mcdreforged/mcdreforged:2.13.0-py3.11-slim

Extra Image
^^^^^^^^^^^^

Image with extra python packages installed

- Image: ``mcdreforged/mcdreforged-extra``
- Docker Hub: https://hub.docker.com/r/mcdreforged/mcdreforged-extra
- Source code: https://github.com/MCDReforged/docker/blob/master/src/Dockerfile-extra

Theses extra packages are collected from the `Plugin Catalogue <https://github.com/MCDReforged/PluginCatalogue>`__,
covering almost all required packages of the plugins in the catalogue

.. note::

    To ensure the feasibility of python package installation during extra image build,
    the actual installed version of those python package in the Extra Image might not be exactly what the plugin wants

.. tip::

    For production environments, it's suggested to maintain your own set of python package installation instead of simply use the Extra Image

    It's for ensuring that all of your plugins run within the python package environment they claim to be compatible with

    You can manually install what your plugins need on a :ref:`docker:Base Image`,
    and mount the ``site-packages`` directory following the guide in the :ref:`docker:Python package installation` above.
    The ``site-packages`` mount can even be shared across multiple containers as long as their python versions are the same

Tag format: The same as :ref:`docker:Base Image`

OpenJDK Images
^^^^^^^^^^^^^^

Images with OpenJDK installed. If you want to run MCDR with a Minecraft server, then here's what you want

- Image: ``mcdreforged/mcdreforged-${jdk_distribution}``. See below for all available JDK distributions
- Source code: https://github.com/MCDReforged/docker/blob/master/src

Supported OpenJDK distributions:

- `corretoo <https://aws.amazon.com/corretto/>`__
- `liberica <https://bell-sw.com/libericajdk>`__
- `temurin <https://adoptium.net/temurin/>`__ (suggested)
- `zulu <https://www.azul.com/downloads/?package=jdk#zulu>`__

Supported java version: 8, 11, 17, 21 (default: 17)

Additional tag suffixes:

- ``-jdk17`` suffix explicitly specify the JDK version to use
- ``-extra`` suffix means the image is built based on the :ref:`extra <docker:Extra Image>` variant

Example docker tags (using temurin JDK distribution as demonstration):

.. code-block:: text

    mcdreforged/mcdreforged-temurin:latest
    mcdreforged/mcdreforged-temurin:latest-extra
    mcdreforged/mcdreforged-temurin:latest-jdk17
    mcdreforged/mcdreforged-temurin:latest-jdk17-extra
    mcdreforged/mcdreforged-temurin:latest-slim
    mcdreforged/mcdreforged-temurin:latest-slim-extra
    mcdreforged/mcdreforged-temurin:latest-slim-jdk17
    mcdreforged/mcdreforged-temurin:latest-slim-jdk17-extra

    mcdreforged/mcdreforged-temurin:2.13.0
    mcdreforged/mcdreforged-temurin:2.13.0-extra
    mcdreforged/mcdreforged-temurin:2.13.0-jdk17
    mcdreforged/mcdreforged-temurin:2.13.0-jdk17-extra
    mcdreforged/mcdreforged-temurin:2.13.0-slim
    mcdreforged/mcdreforged-temurin:2.13.0-slim-extra
    mcdreforged/mcdreforged-temurin:2.13.0-slim-jdk17
    mcdreforged/mcdreforged-temurin:2.13.0-slim-jdk17-extra

    mcdreforged/mcdreforged-temurin:2.13.0-py3.11
    mcdreforged/mcdreforged-temurin:2.13.0-py3.11-extra
    mcdreforged/mcdreforged-temurin:2.13.0-py3.11-jdk17
    mcdreforged/mcdreforged-temurin:2.13.0-py3.11-jdk17-extra
    mcdreforged/mcdreforged-temurin:2.13.0-py3.11-slim
    mcdreforged/mcdreforged-temurin:2.13.0-py3.11-slim-extra
    mcdreforged/mcdreforged-temurin:2.13.0-py3.11-slim-jdk17
    mcdreforged/mcdreforged-temurin:2.13.0-py3.11-slim-jdk17-extra
