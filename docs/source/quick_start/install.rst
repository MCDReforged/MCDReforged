
Installation
============

Requirements
------------

.. image:: https://img.shields.io/pypi/pyversions/mcdreforged.svg
   :alt: Python version

.. image:: https://img.shields.io/pypi/v/mcdreforged.svg
   :alt: PyPI version

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

Install using pip...?
----------------------

MCDR is available in `PyPI <https://pypi.org/project/mcdreforged>`__, which means it can be installed via the ``pip`` command:

.. code-block:: bash

    pip install mcdreforged

Externally managed environment
------------------------------

If you're using Windows, the command above should work fine - you may ignore this section.

However, on Linux and Mac OS, if you're using a newer version of Python, you'll get something like this when you run pip install:

.. code-block:: bash
    
    $ pip install mcdreforged
    error: externally-managed-environment

    × This environment is externally managed
    ╰─> To install Python packages system-wide, try apt install
        python3-xyz, where xyz is the package you are trying to
        install.
        
        If you wish to install a non packaged Python package,
        create a virtual environment using python3 -m venv path/to/venv.
        Then use path/to/venv/bin/python and path/to/venv/bin/pip. Make
        sure you have python3 full installed.
        
        If you wish to install a non packaged Python application,
        it may be easiest to use pipx install xyz, which will manage a
        virtual environment for you. Make sure you have pipx installed.
        
        See /usr/share/doc/python3.x/README.venv for more information.

    note: If you believe this is a mistake, please contact your Python installation or OS distribution provider. You can override this, at the risk of breaking your Python installation or OS, by passing --break-system-packages.
    hint: See PEP 668 for the detailed specification.

That's because of the `PEP 668 <https://peps.python.org/pep-0668/>`__, which was introduced to avoid pip conflicts with the system package manager (apt, yum, pacman, etc.)

As workaround, there're multiple options for you

Using pipx
~~~~~~~~~~

This is the simplest solution for most users, but requires the use of the third-party tool `pipx <https://pipx.pypa.io/>`__, a tool for installing and running Python applications in isolated environments.

Install pipx refer to its `official documentation <https://pipx.pypa.io/stable/#install-pipx>`__

Then install MCDR using pipx:

.. code-block:: bash

    $ pipx install mcdreforged

When a new version of MCDR available, you may upgrade MCDR by:

.. code-block:: bash

    $ pipx upgrade mcdreforged

.. note::

    In this way, MCDR will be installed in a isolated environment. Python packages required by MCDR plugins should be installed by:

    .. code-block:: bash

        $ pipx inject mcdreforged <package_name>
        $ pipx inject mcdreforged -r requirements.txt
    
    Or you may use the :ref:`\!!MCDR command <command/mcdr:Plugin management>` to install plugins with their dependencies


Using virtual environment
~~~~~~~~~~~~~~~~~~~~~~~~~

For the most native, but more complicated option, you can create a virtual environment and install MCDR in it.

Create a virtual environment by:

.. code-block:: bash

    $ python3 -m venv .venv

Activate it by: (`Reference <https://docs.python.org/3/library/venv.html#how-venvs-work>`__)

+----------+------------+-----------------------------------------+
| Platform | Shell      | Command to activate virtual environment |
+==========+============+=========================================+
|  POSIX   | bash/zsh   | $ source .venv/bin/activate             |
+          +------------+-----------------------------------------+
|          | fish       | $ source .venv/bin/activate.fish        |
+          +------------+-----------------------------------------+
|          | csh/tcsh   | $ source .venv/bin/activate.csh         |
+          +------------+-----------------------------------------+
|          | PowerShell | $ .venv/bin/Activate.ps1                |
+----------+------------+-----------------------------------------+
| Windows  | cmd.exe    | > .venv\\Scripts\\activate.bat          |
+          +------------+-----------------------------------------+
|          | PowerShell | PS > .venv\\Scripts\\Activate.ps1       |
+----------+------------+-----------------------------------------+

Then, install MCDR using pip:

.. code-block:: bash

    (.venv) $ pip install mcdreforged

When a new version of MCDR available, you may upgrade MCDR by:

.. code-block:: bash

    $ pip install mcdreforged -U

.. note::

    In this way, you must activate the virtual environment every time you want to use MCDR, or install packages for MCDR plugins

    For more information about virtual environments, See `Python Docs <https://docs.python.org/3/library/venv.html>`__

Using Docker
~~~~~~~~~~~~

MCDR provides Docker images for you to use. See :doc:`/docker` for more details

Compared to the two methods above, Docker has a more convoluted learning path though

System package manager?
~~~~~~~~~~~~~~~~~~~~~~~

You may found MCDR in some package repositories, AUR for example. However, it's **definately not recommended** to use system package manager to install MCDR, because it's hard to manage the dependencies of MCDR plugins in this way

Accelerate the installation
---------------------------

For users in China Mainland, ``pip`` and ``pipx`` may be very slow. You can use a mirror to accelerate the installation:

.. code-block:: bash

    $ pipx install -i https://pypi.tuna.tsinghua.edu.cn/simple mcdreforged
    $ pipx upgrade -i https://pypi.tuna.tsinghua.edu.cn/simple mcdreforged
    (.venv) $ pip install -i https://pypi.tuna.tsinghua.edu.cn/simple mcdreforged
    (.venv) $ pip install -i https://pypi.tuna.tsinghua.edu.cn/simple mcdreforged -U 
