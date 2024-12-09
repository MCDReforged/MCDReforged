
Server Handler
==============

Server handler is the object which parses server output and provides command interfaces to control the server

MCDR itself has already includes a number of server handlers for widely-used Minecraft related servers,
but in case you have a server with custom output format, you can write you own server handler, and assign MCDR to use it.

To design a server handler, you need to inherit from an existed server handler class,
or the base class :class:`~mcdreforged.handler.impl.abstract_minecraft_handler.AbstractMinecraftHandler`

It's recommend to firstly have a look at the implementation of the server handlers in MCDR first and try to understand them 

For easier usage, management and possible distribution in the future,
it is recommended to provide server handlers by creating a :ref:`plugin_dev/basic:MCDR Plugin`
and using the :meth:`~mcdreforged.plugin.si.plugin_server_interface.PluginServerInterface.register_server_handler` API

Example
-------

In this example, we have a vanilla server, but some of the players have a prefix on their username, which result in some changes to the message format of the player chat message.
For Example, A player with id ``Steve`` and prefix ``[Builder]`` might have following chat messages:

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


Then you can start using the handler by loading or reloading the plugin that you've just created

.. dropdown:: Quick guide: Create a working solo plugin providing your custom handler

    The easiest way to create a plugin is to create a :ref:`plugin_dev/plugin_format:Solo Plugin`, which consists of a single ``.py`` file

    1.  Assuming the :ref:`configuration:plugin_directories` config contains the ``plugins/`` directory,
        you can create a new solo plugin by creating and editing the file ``plugins/handler_for_my_server.py``

        .. code-block:: python

            import re

            from mcdreforged.handler.impl import VanillaHandler

            PLUGIN_METADATA = {
                'id': 'handler_for_my_server',
                'version': '0.0.0',
            }

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

        Notes that the only difference between the following code and code above,
        is that it contains a ``PLUGIN_METADATA`` field in the global scope as its plugin metadata

        .. seealso::

            :doc:`/plugin_dev/metadata` document

    2.  Load your newly created plugin with command ``!!MCDR plugin load handler_for_my_server.py``
    3.  Now your custom server handler should be loaded. Test if it works as expected
    4.  (Optional) If it doesn't, edit the ``.py`` plugin file to suit your needs
    5.  (Optional) Reload the plugin with command ``!!MCDR plugin reload handler_for_my_server``

------

As a alternative but not recommended way, you may provide your handler by a single ``.py`` file, rather than a plugin

Put the same code as above, without the ``on_load`` method, into a ``.py`` file, ``my_handler.py`` for example, then use it as follows:

1.  Place it into a valid python package in the working directory of MCDR, e.g.:

    .. code-block:: diff

            my_mcdr_server/
        ++  ├─ handlers/
        ++  │   ├─ __init__.py
        ++  │   └─ my_handler.py
            │
            ├─ server/
            ├─ config.yml
            └─ permission.yml

    This make your handler class accessible with ``from handlers.my_handler import MyHandler``

2.  Add the path to the :ref:`configuration:custom_handlers` option,
    then set the :ref:`configuration:handler` option to what method ``get_name()`` of the handler returns, e.g.:

    .. code-block:: yaml

        handler: the_handler_for_my_server

        custom_handlers:
        - handlers.my_handler.MyHandler
