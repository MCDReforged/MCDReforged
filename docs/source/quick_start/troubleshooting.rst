
Troubleshooting
===============

Have problems to make things work? Here are some common issues and their solutions

The server won't start
----------------------

* Check out your start command
* Check if java is installed and added in PATH
* If you're directing the start command to a batch or shellscript, try the actual command instead of the script

Learn more in :ref:`configuration:start_command`


Garbled text / UnicodeDecodeError
---------------------------------

Usually, this is caused by the console encoding / decoding

MCDR use UTF-8 as default encoding and decoding, so try to use UTF-8 in everything related to the server. See :ref:`configuration:encoding, decoding`

Commands not working in game
----------------------------

MCDR handle commands by listening to the server's console output

Make sure you are using the correct :ref:`Server Handler <configuration:handler>`. If your server software is not supported by built-in handlers, you may need to :ref:`customize your own handler <customize/handler:Server Handler>`

If your server output is modified by mods or plugins, the handler may not be able to recognize the outputs. Try to disable all mods and plugins to see if the problem solved. If so, you may need to :ref:`customize your own handler <customize/handler:Server Handler>` to handle the modified outputs

Run with MCSManager
-------------------

.. warning::

    This part may not being up to date. If you encounter any problems, do not report them to MCDR

    For more infomations, get in touch with their community: `Github Repo <https://github.com/MCSManager/MCSManager>`__, `Documentation <https://docs.mcsmanager.com/>`__

MCDR did not specificly designed to adapt MCSManager

However, if you use UTF-8 everywhere, and enable ``Emulation Terminal`` in MCSManager, MCDR should work fine with full functionality

If ``Emulation Terminal`` is disabled, you should set :ref:`configuration:advanced_console` to ``false``
