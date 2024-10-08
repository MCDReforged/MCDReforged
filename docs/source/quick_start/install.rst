
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

Install using pip
-----------------

MCDR is available in `PyPI <https://pypi.org/project/mcdreforged>`__, it can reasonably be installed via the ``pip`` command:

.. tab:: Windows

    .. code-block:: bat

        pip install mcdreforged

.. tab:: Linux

    .. code-block:: bash

        pip3 install mcdreforged

Externally managed environment
------------------------------

If you're using Windows, the command above should work fine, MCDR will be installed to global environment - you may ignore this section

For Linux and Mac OS, it's not recommended to install MCDR system-wide, because it can cause conflicts with other Python packages and affect system dependencies

System-wide install also makes version management difficult 
and requires administrator privileges, increasing security risks

For the same reason, you may get a ``externally-managed-environment`` error on pip install

See `PEP 668 <https://peps.python.org/pep-0668/>`__ for the detailed specification

It's safer to keep the installation isolated. As workarounds, there're multiple options for you

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

    In this way, MCDR will be installed in an isolated environment. Instead of ``pip install <package_name>``, Python packages required by MCDR plugins should be installed by:

    * ``pipx inject mcdreforged <package_name>``
    * or ``pipx inject mcdreforged -r requirements.txt``
    
    More conveniently, use the :ref:`\!!MCDR plg command <command/mcdr:Plugin management>` to install plugins with their dependencies


Using virtual environment
~~~~~~~~~~~~~~~~~~~~~~~~~

For the most native, but more complicated option, you can create a virtual environment and install MCDR in it

Create a virtual environment by:

.. code-block:: bash

    $ python3 -m venv <venv directory>

``venv`` for example:

.. code-block:: bash

    $ python3 -m venv venv

Activate it by: (`Reference <https://docs.python.org/3/library/venv.html#how-venvs-work>`__)

+----------+------------+-----------------------------------------+
| Platform | Shell      | Command to activate virtual environment |
+==========+============+=========================================+
|  POSIX   | bash/zsh   | $ source venv/bin/activate              |
+          +------------+-----------------------------------------+
|          | fish       | $ source venv/bin/activate.fish         |
+          +------------+-----------------------------------------+
|          | csh/tcsh   | $ source venv/bin/activate.csh          |
+          +------------+-----------------------------------------+
|          | PowerShell | $ venv/bin/Activate.ps1                 |
+----------+------------+-----------------------------------------+
| Windows  | cmd.exe    | > venv\\Scripts\\activate.bat           |
+          +------------+-----------------------------------------+
|          | PowerShell | PS > venv\\Scripts\\Activate.ps1        |
+----------+------------+-----------------------------------------+

Then, install MCDR using pip:

.. code-block:: bash

    (venv) $ pip install mcdreforged

When a new version of MCDR available, you may upgrade MCDR by:

.. code-block:: bash

    (venv) $ pip install mcdreforged -U

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
    (venv) $ pip install -i https://pypi.tuna.tsinghua.edu.cn/simple mcdreforged
    (venv) $ pip install -i https://pypi.tuna.tsinghua.edu.cn/simple mcdreforged -U 

Or simply set a global index-url by:

.. code-block:: bash

    $ pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
