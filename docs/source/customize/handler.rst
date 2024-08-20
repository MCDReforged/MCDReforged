
Server Handler
==============

Server handler is the object which parses server output and provides command interfaces to control the server

MCDR itself has already includes a number of server handlers for widely-used Minecraft related servers, but in case you have a server with custom output format, you can write you own server handler, and assign MCDR to use it.

To design a server handler, you need to inherit from an existed server handler class, or the base class :class:`~mcdreforged.handler.impl.abstract_minecraft_handler.AbstractMinecraftHandler`

It's recommend to firstly have a look at the implementation of the server handlers in MCDR first and try to understand them 

For easier use and distribution, it is recommended to provide server handlers by creating a MCDR Plugin.

Example
-------

In this example, we have a vanilla server, but some of the players have a prefix on their username, which result in some changes to the message format of the player chat message. For Example, A player with id ``Steve`` and prefix ``[Builder]`` might have following chat messages:

.. code-block::

    <[Builder]Steve> Hello
    <[Builder]Steve> !!MCDR status

For the default vanilla handler, ``[Builder]Steve`` is an illegal player name. Luckily all possible prefixes of the players in the server follows the same format ``[Prefix]PlayerName``. So it's possible to make a dedicated handler for the server

For example, we create a MCDR plugin and write the following codes as its entrypoint, which creates and registers a handler to handle player names in this server correctly 

.. code-block:: python

    import re

    from mcdreforged.handler.impl import VanillaHandler


    class MyHandler(VanillaHandler):
        def get_name(self) -> str:
            return 'the_handler_for_my_server'

        def parse_server_stdout(self, text: str):
            info = super().parse_server_stdout(text)
            if info.player is None:
                m = re.fullmatch(r'<\[\w+](?P<name>[^>]+)> (?P<message>.*)', info.content)
                if m is not None and self._verify_player_name(m['name']):
                    info.player, info.content = m['name'], m['message']
            return info
    

    def on_load(server, prev_module):
        server.register_server_handler(MyHandler())


Then we can start using the handler:


1.  Load or reload the plugin you've just created
2.  Set the :ref:`configuration:handler` option to what method ``get_name()`` of your handler returns, e.g.:

    .. code-block:: yaml

        handler: the_handler_for_my_server

That's all you need to do
