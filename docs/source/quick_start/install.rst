
Installation
============

For the first step of our journey, let's install MCDR

.. note::

    We assume you have some really basic knowledge of Python and pip.

    If you have not, Google is your friend

Requirements
------------

.. image:: https://img.shields.io/pypi/pyversions/mcdreforged.svg
   :alt: Python version

.. image:: https://img.shields.io/pypi/v/mcdreforged.svg
   :alt: PyPI version

MCDR is written and runs in Python 3. Make sure you have Python 3.8 or later installed

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

If you're using Windows, the command above should work fine, MCDR will be installed to global environment - you may ignore this section

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

As workarounds, there're multiple options for you

Using pipx
~~~~~~~~~~

Maybe the simplest solution for most users, but requires to use the third-party tool `pipx <https://pipx.pypa.io/>`__, which is designed to installing and running Python applications in isolated environments

Install pipx refer to its `official documentation <https://pipx.pypa.io/stable/#install-pipx>`__

Then install MCDR using pipx:

.. code-block:: bash

    $ pipx install mcdreforged

When a new version of MCDR available, you may take the upgrade by:

.. code-block:: bash

    $ pipx upgrade mcdreforged

.. asciinema:: resources/pipx.cast
    :rows: 8

|

.. note::

    In this way, MCDR will be installed in an isolated environment. Python packages required by MCDR plugins should be installed by:

    * ``pipx inject mcdreforged <package_name>``
    * or ``pipx inject mcdreforged -r requirements.txt``
    
    More conveniently, use the :ref:`\!!MCDR plg command <command/mcdr:Plugin management>` to install plugins with their dependencies


Using virtual environment
~~~~~~~~~~~~~~~~~~~~~~~~~

For the most native, but more complicated option, you can create a virtual environment and install MCDR in it

Create a virtual environment, ``.venv`` for example, by:

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

    (.venv) $ pip install mcdreforged -U

An animated demo with bash:

.. asciinema:: resources/venv.cast
    :rows: 10

|

.. note::

    In this way, you must activate the virtual environment every time you want to use MCDR, or install packages for MCDR plugins

    For more information about virtual environments, See `Python Docs <https://docs.python.org/3/library/venv.html>`__

Using Docker
~~~~~~~~~~~~

MCDR also provides Docker images as an option. See :doc:`/docker` for more details

Specify MCDR version by specify the tag of Docker image. If you use ``latest``, MCDR should always being up to date

Compared to the two methods above, Docker has a more convoluted learning path, but convenient for some advanced usages

System package manager?
~~~~~~~~~~~~~~~~~~~~~~~

You may found MCDR in some package repositories, AUR for example. However, it's **definately not recommended** to use system package manager to install MCDR, because it's hard to manage the dependencies of MCDR plugins in this way

Accelerate the installation
---------------------------

For users in some areas, ``pip`` and ``pipx`` may be very slow. You can use a mirror to accelerate the installation. Here's an example for 
Tsinghua University TUNA mirror:

.. code-block:: bash

    $ pipx install -i https://pypi.tuna.tsinghua.edu.cn/simple mcdreforged
    $ pipx upgrade -i https://pypi.tuna.tsinghua.edu.cn/simple mcdreforged
    (.venv) $ pip install -i https://pypi.tuna.tsinghua.edu.cn/simple mcdreforged
    (.venv) $ pip install -i https://pypi.tuna.tsinghua.edu.cn/simple mcdreforged -U 

Or simply set a global index-url by:

.. code-block:: bash

    $ pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
