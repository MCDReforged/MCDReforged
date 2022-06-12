
Server Handler
==============

Server handler is the object which parses server output and provides command interfaces to control the server

MCDR itself has already includes a number of server handlers for widely-used Minecraft related servers, but in case you have a server with custom output format, you can write you own server handler, and assign MCDR to use it.

To design a server handler, you need to inherit from an existed server handler class, or the base class ``AbstractServerHandler``

It's recommend to firstly have a look at the implementation of the server handlers in MCDR first and try to understand them 

Example
-------

In this example, we have a vanilla server, but some of the players have a prefix on their username, which result in some changes to the message format of the player chat message. For Example, A player with id ``Steve`` and prefix ``[Builder]`` might have following chat messages:

.. code-block::

   <[Builder]Steve> Hello
   <[Builder]Steve> !!MCDR status

For the default vanilla handler, ``[Builder]Steve`` is an illegal player name. Luckily all possible prefixes of the players in the server follows the same format ``[Prefix] PlayerName``. So it's possible to make a dedicated handler for the server

For example, the following codes above creates a handler than is able to handle player names in this server

.. code-block:: python

    from parse import parse

    from mcdreforged.handler.impl import VanillaHandler


    class MyHandler(VanillaHandler):
        def get_name(self) -> str:
            return 'the_handler_for_my_server'

        def parse_server_stdout(self, text: str):
            result = super().parse_server_stdout(text)
            if result.player is None:
                parsed = parse('<[{prefix}]{name}> {message}', result.content)
                if parsed is not None and self._verify_player_name(parsed['name']):
                    result.player, result.content = parsed['name'], parsed['message']
            return result

And then you are able to use this handler to handle the server. You need to do the following things in the configuration file


#. Set the ``handler`` option in the configuration file to ``the_handler_for_my_server``
#. Added the path to the custom handler in the `custom_handlers <../configure.html#custom-handlers>`__ option, e.g:

.. code-block::

   custom_handlers:
   - the.package.to.my.handler.MyHandler

That's all you need to do
