
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

MCDR is written and runs in Python 3. Make sure you have Python 3.8 or later, with `pip <https://github.com/pypa/pip>`__ installed

The detailed Python version requirements are as shown in the table below

.. list-table::
   :header-rows: 1

   * - MCDR version
     - Python requirement
   * - < 2.10
     - >= 3.6
   * - >= 2.10
     - >= 3.8

Wait a second
-------------

In some tutorials, you may learned to use MCDR by downloading a zip from Github and extract it

However, that's not the correct way to install MCDR - Those tutorials are outdated

.. caution::

    **DO NOT** download the source files of MCDR and execute them directly, unless you're a developer of MCDR and you know what you are doing

Install using pip
-----------------

MCDR is available in `PyPI <https://pypi.org/project/mcdreforged>`__, it's reasonably to be installed by:

.. tab:: Windows

    .. code-block:: bat

        pip install mcdreforged

.. tab:: Linux

    .. code-block:: bash

        pip3 install mcdreforged

And upgraded by:

.. tab:: Windows

    .. code-block:: bat

        pip install mcdreforged -U

.. tab:: Linux

    .. code-block:: bash

        pip3 install mcdreforged -U

Verify the installation with:

.. prompt-mcdr-version:: bash $ auto

    $ mcdreforged
    MCDReforged v@@MCDR_VERSION@@

Externally managed environment
------------------------------

If you're using Windows, the command above should work fine, and MCDR will be installed to the global environment - you may ignore this section

For Linux and Mac OS, it's not recommended to install MCDR system-wide (with root), because it can cause conflicts with other Python packages and affect system dependencies

System-wide installation also makes version management difficult 
and requires administrator privileges, increasing security risks

System-wide installation may even result in an ``externally-managed-environment`` error

See `PEP 668 <https://peps.python.org/pep-0668/>`__ for the detailed specification

It's safer to keep the installation isolated. As workarounds, there're multiple options for you. In conclusion:

.. list-table::
    :header-rows: 1

    * - Method
      - Pros
      - Cons
    * - pip
      - Native, always available
      - Not isolated, may affect global packages with root privileges
    * - pipx
      - Simplest
      - 3rd party, different command set
    * - venv
      - Native support
      - Requires manual environment activation
    * - docker
      - Reliable across environments
      - More dependencies and disk space, convoluted learning path
    * - system package
      - \-
      - Same as pip, **not recommended**

Using pipx
~~~~~~~~~~

It may be the simplest solution for most users, but it requires using the third-party tool `pipx <https://pipx.pypa.io/>`__, which is designed for installing and running Python applications in isolated environments

To install pipx, please refer to its `official documentation <https://pipx.pypa.io/stable/#install-pipx>`__

Then you can install MCDR using pipx:

.. prompt:: bash

    pipx install mcdreforged

When a new version of MCDR is available, you can upgrade by:

.. prompt:: bash

    pipx upgrade mcdreforged

.. asciinema:: resources/pipx.cast
    :rows: 8

|

.. note::

    In this way, MCDR will be installed in an isolated environment. Instead of using ``pip install <package_name>``, Python packages required by MCDR plugins should be installed by:

    * ``pipx inject mcdreforged <package_name>``, e.g. ``pipx inject mcdreforged requests``
    * or ``pipx inject mcdreforged -r requirements.txt``
    
    More conveniently, you can use the :ref:`\!!MCDR plg command <command/mcdr:Plugin management>` to install plugins with their dependencies


Using virtual environment
~~~~~~~~~~~~~~~~~~~~~~~~~

For the most native, but more complicated option, you can create a virtual environment and install MCDR in it

Create a virtual environment by:

.. prompt:: bash

    python3 -m venv <venv directory>

``venv`` for example:

.. prompt:: bash

    python3 -m venv venv

Activate it by:

+----------+------------+-----------------------------------------+
| Platform | Shell      | Command to activate virtual environment |
+==========+============+=========================================+
|  POSIX   | bash/zsh   | source venv/bin/activate                |
+          +------------+-----------------------------------------+
|          | fish       | source venv/bin/activate.fish           |
+          +------------+-----------------------------------------+
|          | csh/tcsh   | source venv/bin/activate.csh            |
+          +------------+-----------------------------------------+
|          | PowerShell | venv/bin/Activate.ps1                   |
+----------+------------+-----------------------------------------+
| Windows  | cmd.exe    | venv\\Scripts\\activate.bat             |
+          +------------+-----------------------------------------+
|          | PowerShell | venv\\Scripts\\Activate.ps1             |
+----------+------------+-----------------------------------------+

.. seealso ::

    Python Doc: `How venvs work <https://docs.python.org/3/library/venv.html#how-venvs-work>`__

Then, install MCDR using pip:

.. prompt:: bash
    :prompts: (venv) $

    pip install mcdreforged

When a new version of MCDR is available, you can upgrade MCDR by:

.. prompt:: bash
    :prompts: (venv) $

    pip install mcdreforged -U

An animated demo with bash:

.. asciinema:: resources/venv.cast
    :rows: 10

|

.. note::

    In this way, you must activate the virtual environment every time you want to use MCDR, or install packages for MCDR plugins

    For more information, see `venv <https://docs.python.org/en/3/library/venv.html>`__ in Python Doc

Using Docker
~~~~~~~~~~~~

MCDR also provides Docker images as an option. See :doc:`/docker` for more details

You can specify the version of MCDR by the tag of the Docker image

Compared to the two methods above, Docker has a more convoluted learning path, but convenient for some advanced usages

System package manager
~~~~~~~~~~~~~~~~~~~~~~

You may found MCDR in some package repositories, AUR for example. However, it's **definately not recommended** to use a system package manager to install MCDR. Not only it has all the same problem as the system-wide pip install, it's also hard to manage the dependencies of MCDR plugins

Accelerate the installation
---------------------------

For users in China, you may use a mirror, `Tsinghua University TUNA mirror <https://mirrors.tuna.tsinghua.edu.cn/help/pypi/>`__ for example, to accelerate ``pip`` and ``pipx``

To use the mirror, ``-i <index-url>`` to the commands:

.. prompt:: bash
    :prompts: $,(venv) $
    :modifiers: auto

    $ pipx install -i https://pypi.tuna.tsinghua.edu.cn/simple mcdreforged
    $ pipx upgrade -i https://pypi.tuna.tsinghua.edu.cn/simple mcdreforged
    (venv) $ pip install -i https://pypi.tuna.tsinghua.edu.cn/simple mcdreforged
    (venv) $ pip install -i https://pypi.tuna.tsinghua.edu.cn/simple mcdreforged -U 

Or simply set a global index-url by:

.. prompt:: bash

    pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
