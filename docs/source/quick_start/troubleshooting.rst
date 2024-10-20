
Troubleshooting
===============

Have problems making things work? Here are some common issues and their solutions

MCDR won't start
----------------

* **mcdreforged: command not found**
    * Try ``python -m mcdreforged``, which explicitly specifies the Python interpreter to start MCDR
    * If you installed MCDR via pipx, ensure the pipx apps directory is in your PATH
    * If you installed MCDR via pip globally, ensure that the directory where pip places the installed scripts is in your PATH
    * If you installed MCDR via pip within venv, make sure you have activated the venv
    * If you installed MCDR via system package manager... don't install MCDR via system package manager

* **Error raised by Python**
    * Install MCDR correctly. Don't start MCDR the source code
    * Try to re-install MCDR, see if the problem persists
    * If you installed MCDR via venv, make sure you have activated the venv
    * Use ``which mcdreforged`` (``where mcdreforged`` in Windows), see which executable is being called

The server won't start
----------------------

* Check out your start command
* Check if Java is installed and added to the PATH
* Try to run the server without MCDR, using the same command you configured
* If you're directing the start command to a batch or shellscript, try the actual command instead of the script

Learn more in :ref:`configuration:start_command`


Garbled text / UnicodeDecodeError
---------------------------------

Usually, this is caused by the console encoding / decoding

MCDR uses UTF-8 as the default encoding and decoding, so try to use UTF-8 in everything related to the server. See :ref:`configuration:encoding, decoding`

Commands not working
--------------------

- **All commands are not responding in game, but working in console**
- **Some commands perform incorrectly for specific players**

    MCDR handles commands by listening to the server's console output. Make sure you are using the correct :ref:`Server Handler <configuration:handler>`

    Your server may unexpectedly not compatible with handlers:
 
    Maybe your server is unique that not supported by built-in handlers

    Maybe your server output is different. For example, if you allow players that not following the Mojang naming rule (``[A-Za-z0-9_]{3,16}``), the handler will not recognize them. Examples:

    .. tab:: ❌

        .. code-block:: text

            [09:00:00] [Server thread/INFO]: <Steve.the.Warrior> Hello
            [09:00:00] [Server thread/INFO]: <史蒂夫> hello

    .. tab:: ✅

        .. code-block:: text

            [09:00:00] [Server thread/INFO]: <Steve> Hello

    Maybe your server output has been modified by mods or plugins (usually something like "player title/profession", "better console"), that the handler can't recognize them. To be confirmed, disable all mods and plugins and see if the problem is solved. Examples:
    
    .. tab:: ❌

        .. code-block:: text

            [09:00:00] [Server thread/INFO]: <[Warrior]Steve> Hello
            (09:00:00) INFO | Steve: hello
        
    .. tab:: ✅

        .. code-block:: text

            [09:00:00] [Server thread/INFO]: <Steve> Hello

    If your server has one of these problems, you may need to :ref:`customize your own handler <customize/handler:Server Handler>`

- **Some plugin commands work neither in game nor on the console**
- **Some plugin commands perform incorrectly in all conditions**

    Check if the plugin is enabled and loaded correctly. Check the logs to see if there are any errors or warnings related to the plugin. Check the plugin configuration

    Check the README or documentation of the plugin to see if it has any special requirements. Some plugins may require additional permissions or configurations

    Some plugins may have conflicts with others. Try to disable other plugins to see if the problem solved

    If the problem still exists, try to report it to the plugin's author or community

Run with MCSManager
-------------------

.. warning::

    This part may not being up to date. If you encounter any problems, do not report them to MCDR

    For more infomations, get in touch with their community: `Github Repo <https://github.com/MCSManager/MCSManager>`__, `Documentation <https://docs.mcsmanager.com/>`__

MCDR did not specificly designed to adapt MCSManager

However, if you use UTF-8 everywhere, and enable ``Emulation Terminal`` in MCSManager, MCDR should work fine with full functionality

If ``Emulation Terminal`` is disabled, you should set :ref:`configuration:advanced_console` to ``false``

Get in touch
------------

If these solutions do not solve your problem, please get in touch with :ref:`our kind community <quick_start/next_steps:Community>`

Still, before you ask questions or report bugs, please:

* Search, and research
* Write a title that summarizes the specific problem
* Help others reproduce the problem:

    * `Create a minimal reproducible example <https://stackoverflow.com/help/minimal-reproducible-example>`__
    * Provide your full logs and context, no unnecessary images. If the log file is long, send it as an attachment file or use services like `mclo.gs <https://mclo.gs/>`__ or `Pastebin <https://pastebin.com/>`__ to share it

* Proofread before posting
* Respond to feedback after posting

.. seealso::

    Stack Overflow: `How do I ask a good question? <https://stackoverflow.com/help/how-to-ask>`__
