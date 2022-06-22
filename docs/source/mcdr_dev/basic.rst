
Basics
======

Launch from source
------------------

When you are developing MCDR, you may want to launch MCDR from its source file directly, and here's the way to do that

Download the source files of MCDR via cloning the repository or github action, and decompress the file if needed

.. code-block::

    my_mcdr_server_in_source/
     ├─ mcdreforged/
     │   └─ ..
     ├─ MCDReforged.py
     ├─ setup.py
     └─ ..

MCDR will delay to start and print some warnings if the ``mcdreforged`` python package is not detected, and this is a common thing if you are launching MCDR from source

This mechanism is designed to help those newbies who follow outdated tutorials and try to launch MCDR from source, and guide them to use the correct method to launch MCDR

Apparently we want to get rid of this warning and the startup delay things during our development on MCDR. We can bypass this by creating a local MCDR package information. Here's the way to do that:

Enter the directory ``my_mcdr_server_in_source/``, and run the following command to create egg_info

.. code-block:: bash

    python setup.py egg_info

That's it. After that command, MCDR can be launched normally

Don't forget to regenerate the egg_info by using the same command after you changed the information of the mcdreforged package, e.g. the version of MCDR

Launch via python script
------------------------

Besides using ``python -m mcdreforged`` to launch MCDR, you can also use python interpreter to execute ``MCDReforged.py`` to launch MCDR

.. code-block:: bash

    python MCDReforged.py

``MCDReforged.py`` is just a simple wrapper for launching MCDR with the following codes

.. code-block:: python

    import sys

    from mcdreforged.__main__ import main

    if __name__ == '__main__':
        sys.exit(main())

``MCDReforged.py`` also works for MCDR installed by ``pip`` command, which means that it works in production environment too

For windows users, if you have bound a correct python interpreter to ``*.py`` files you can also double click the ``MCDReforged.py`` to start MCDR
