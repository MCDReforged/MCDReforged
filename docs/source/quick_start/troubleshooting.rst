
Troubleshooting
===============

Have problems to make things work? Here are some common issues and their solutions

The server won't start
----------------------

* Check out your start command
* Check if java is installed and added in PATH
* Try to run the server without MCDR, using the same command you configured
* If you're directing the start command to a batch or shellscript, try the actual command instead of the script

Learn more in :ref:`configuration:start_command`


Garbled text / UnicodeDecodeError
---------------------------------

Usually, this is caused by the console encoding / decoding

MCDR use UTF-8 as default encoding and decoding, so try to use UTF-8 in everything related to the server. See :ref:`configuration:encoding, decoding`

Commands not working
--------------------

- **All commands are not responding in game, but working in console**
- **Some commands perform incorrectly for specific players**

    MCDR handle commands by listening to the server's console output. Make sure you are using the correct :ref:`Server Handler <configuration:handler>`

    Your server may unexpectedly not compatible with handlers:
 
    Maybe our server software is unique that not supported by built-in handlers

    Maybe your server output is different. For example, if you allow players that not following the Mojang naming rule (``[A-Za-z0-9_]{3,16}``), the handler will not recognize them

    Maybe your server output have been modified by mods or plugins (usually something like "player title/profession", "better console"), that the handler can't recognize them. To be confirmed, disable all mods and plugins and see if the problem solved

    If your server has one of these problems, you may need to :ref:`customize your own handler <customize/handler:Server Handler>`

- **Some plugin commands work neither in game nor the console**
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
