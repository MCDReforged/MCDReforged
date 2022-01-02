
Quick Start
===========

This is a quick start tutorial of `MCDReforged <https://github.com/Fallen-Breath/MCDReforged>`__ (abbreviated as MCDR, omitted below)

Preparation
------------

* MCDR requires python3 runtime. The python version need to be at least 3.6 with pip installed.
* Literally, MCDR is a daemon system for Minecraft. You need a full Minecraft server prepared to get the maxium power of MCDR.
* For Chinese users, you may need to set the pypi source to a mirror server to speed up the installing or upgrading. Here we recommend `Tsinghua tuna mirror <https://mirrors.tuna.tsinghua.edu.cn/help/pypi/>`__.

Install
-------

MCDR is available in `pypi <https://pypi.org/project/mcdreforged>`__. It can be installed via ``pip`` command

.. code-block:: bash

    pip install mcdreforged

Start up
--------

Let's say your are going to start MCDR in a folder named ``my_mcdr_server``. Then you can run the following commands to initialize the environment for MCDR first:

.. code-block:: bash

    cd my_mcdr_server
    python -m mcdreforged init

MCDR will generated the default configure and permission files, as well as some default folders. The file structure will be like this

.. code-block::

   my_mcdr_server/
    ├─ config/
    ├─ logs/
    │   └─ MCDR.log
    ├─ plugins/
    ├─ server/
    ├─ config.yml
    └─ permission.yml

Now put your server files into the server folder (``server`` by default), then modify the configuration file ``config.yml`` and permission file ``permission.yml`` correctly (see `Configure <configure.html>`__ and `Permission <permission.html>`__)

After that you can launch MCDR, and it will start handling the server correctly

.. code-block:: bash

    python -m mcdreforged

Plugins
-------

The power of MCDR is all about its plugin system.

`This <https://github.com/MCDReforged/PluginCatalogue>`__ is the official plugin catalogue for MCDR. You can find some really cool plugins there.

Some advice:

* The README or documentation is very important. Read it carefully before using something.
* Before asking a question, consider if it's your problem.
* `Ask questions in a smart way <http://www.catb.org/~esr/faqs/smart-questions.html>`__.
* Communicate in a friendly manner.

Upgrade
-------

With the help of `pypi <https://pypi.org/project/mcdreforged/>`__, MCDR can be easily upgraded via a single command

.. code-block:: bash

    pip install mcdreforged --upgrade

That's it!

Development builds are available in `Test PyPi <https://test.pypi.org/project/mcdreforged/#history>`__, you can install them if you have special needs

Launch from source
------------------

Instead of installing MCDR from pypi, you can execute the source file of MCDR directly. Notes: This is mostly for development purpose, **DO NOT USE IT FOR PRODUCTION ENVIRONMENTS!**

Download the source files of MCDR via cloning the repository or github action, and decompress the file if needed

.. code-block::

   my_mcdr_server_in_source/
    ├─ mcdreforged/
    │   └─ ..
    ├─ MCDReforged.py
    └─ ..

Enter directory ``my_mcdr_server_in_source/`` and you can start MCDR with the same command as above

.. code-block:: bash

    python -m mcdreforged

Alternatively you can execute ``MCDReforged.py`` with python to start MCDR

.. code-block:: bash

    python MCDReforged.py

``MCDReforged.py`` is just a simple wrapper for launching MCDR with the following codes

.. code-block:: python

    import sys

    from mcdreforged.__main__ import main

    if __name__ == '__main__':
        sys.exit(main())

``MCDReforged.py`` also works for MCDR installed by ``pip`` command

For windows users, if you have bound a correct python interpreter to ``*.py`` files you can also double click the ``MCDReforged.py`` to start MCDR
