
Server Handler
==============

Server handler is the object which parses server output and provides command interfaces to control the server

MCDR itself already includes a number of server handlers for widely-used Minecraft related servers, see the :ref:`configuration:handler` option.
But in case you have a server with custom output format, you can customize your own server handler, and assign MCDR to use it

There are 2 ways to customize a server handler:

* :ref:`customize/handler:Customize with Handler Spec`: Describe the handler in YAML, mostly with regular expressions, no programming required.
  It covers most of the cases, e.g. a different output format, a different player name rule, or a prefix in player chat messages
* :ref:`customize/handler:Customize with Python`: Write a server handler class in Python, for the cases that cannot be described by a handler spec

Customize with Handler Spec
---------------------------

.. versionadded:: v2.17.0

A handler spec describes how MCDR controls the server, and how MCDR parses the server output.
All built-in handlers, except ``basic_handler``, are defined by handler specs. See :ref:`customize/handler:Built-in Handler Specs` for their contents

You can define handlers with handler specs in the :ref:`configuration:custom_handlers` option of the MCDR configuration.
See :class:`~mcdreforged.handler.handler_spec.HandlerSpec` for the full reference of the fields in a handler spec

Handler Spec Example
^^^^^^^^^^^^^^^^^^^^

In this example, we have a vanilla server, but some of the players have a prefix on their username, which result in some changes to the message format of the player chat message.
For Example, A player with id ``Steve`` and prefix ``[Builder]`` might have following chat messages:

.. code-block::

    <[Builder]Steve> Hello
    <[Builder]Steve> !!MCDR status

For the default vanilla handler, ``[Builder]Steve`` is an illegal player name. Luckily all possible prefixes of the players in the server follows the same format ``[Prefix]PlayerName``.
So we can extend the built-in ``vanilla_handler``, and add a player message rule for it in the MCDR configuration:

.. code-block:: yaml

    handler: my_vanilla_handler

    custom_handlers:
      - name: my_vanilla_handler
        extends: vanilla_handler
        overrides:
          parsing:
            player_message:
              # the original rule of vanilla_handler
              - '(\[Not Secure] )?<(?P<name>[^>]+)> (?P<message>.*)'
              # the new rule for players with prefix
              - '(\[Not Secure] )?<\[\w+](?P<name>[^>]+)> (?P<message>.*)'

* ``name``: The name of the new handler. It cannot be the same as any existing handler.
  Set the :ref:`configuration:handler` option to it to use the handler
* ``extends``: The built-in handler to extend
* ``overrides``: The parts of the handler spec to change. Everything not mentioned is inherited from the built-in handler

Some notes on the ``player_message`` rules:

* Lists are replaced as a whole, so the original rule of ``vanilla_handler`` needs to be copied along with the new rule.
  See :meth:`HandlerSpec.extend() <mcdreforged.handler.handler_spec.HandlerSpec.extend>` for the merging rules
* For ``<[Builder]Steve> Hello``, the first rule matches with player name ``[Builder]Steve``, which is not a valid player name,
  so the rule is skipped, and the second rule matches with player name ``Steve``

Then use command ``!!MCDR reload config`` to apply the changes, and test if it works as expected

Define a Handler from Scratch
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If the server is quite different from all built-in handlers, you can provide a complete handler spec with the ``spec`` key,
instead of extending a built-in handler. For example, a non-Minecraft server that is stopped by the ``SIGINT`` signal:

.. code-block:: yaml

    handler: my_app_handler

    custom_handlers:
      - name: my_app_handler
        spec:
          control:
            stop:
              signal: SIGINT
          parsing:
            line:
              # 2026-01-01 09:00:00 [INFO] Server started
              - '[\d-]+ (?P<hour>\d+):(?P<min>\d+):(?P<sec>\d+) \[(?P<logging>\w+)] (?P<content>.*)'
            player_name: '[a-zA-Z0-9_]{3,16}'
          events:
            server_startup_done:
              - 'Server started'

Load from a File
^^^^^^^^^^^^^^^^

A handler spec entry can also be placed in a separate YAML file, and referenced with the ``file`` key:

.. code-block:: yaml

    custom_handlers:
      - file: handlers/my_vanilla_handler.yml

The content of the file is an ``extends`` or ``spec`` entry, e.g.:

.. code-block:: yaml

    name: my_vanilla_handler
    extends: vanilla_handler
    overrides:
      parsing:
        player_name: '\.?[a-zA-Z0-9_]{3,16}'

The file path is relative to the working directory of MCDR, i.e. where the ``config.yml`` is located.
The file is read when the MCDR configuration is loaded, so use ``!!MCDR reload config`` to apply the changes in the file

Built-in Handler Specs
^^^^^^^^^^^^^^^^^^^^^^

Here are the handler specs of the built-in handlers. You can copy rules from them when writing your own handler spec

.. dropdown:: vanilla_handler

    .. literalinclude:: /../../mcdreforged/resources/handler/vanilla_handler.yml
        :language: yaml

.. dropdown:: beta18_handler

    .. literalinclude:: /../../mcdreforged/resources/handler/beta18_handler.yml
        :language: yaml

.. dropdown:: bukkit_handler

    .. literalinclude:: /../../mcdreforged/resources/handler/bukkit_handler.yml
        :language: yaml

.. dropdown:: bukkit14_handler

    .. literalinclude:: /../../mcdreforged/resources/handler/bukkit14_handler.yml
        :language: yaml

.. dropdown:: forge_handler

    .. literalinclude:: /../../mcdreforged/resources/handler/forge_handler.yml
        :language: yaml

.. dropdown:: cat_server_handler

    .. literalinclude:: /../../mcdreforged/resources/handler/cat_server_handler.yml
        :language: yaml

.. dropdown:: arclight_handler

    .. literalinclude:: /../../mcdreforged/resources/handler/arclight_handler.yml
        :language: yaml

.. dropdown:: bungeecord_handler

    .. literalinclude:: /../../mcdreforged/resources/handler/bungeecord_handler.yml
        :language: yaml

.. dropdown:: waterfall_handler

    .. literalinclude:: /../../mcdreforged/resources/handler/waterfall_handler.yml
        :language: yaml

.. dropdown:: velocity_handler

    .. literalinclude:: /../../mcdreforged/resources/handler/velocity_handler.yml
        :language: yaml

Customize with Python
---------------------

If a handler spec is not enough, e.g. the parsing needs some program logic, you can write a server handler class in Python

To design a server handler, you need to inherit from an existed server handler class,
or the base class :class:`~mcdreforged.handler.server_handler.ServerHandler`. Common choices are:

* A built-in handler class, e.g. :class:`~mcdreforged.handler.impl.VanillaHandler`, and override some of its methods to add extra logic
* :class:`~mcdreforged.handler.impl.SpecServerHandler`, with your own :class:`~mcdreforged.handler.handler_spec.HandlerSpec`
* :class:`~mcdreforged.handler.server_handler.ServerHandler`, and implement everything by yourself.
  To stop the server, implement :meth:`~mcdreforged.handler.server_handler.ServerHandler.get_stop_method`

For easier usage, management and possible distribution in the future,
it is recommended to provide server handlers by creating a :ref:`plugin_dev/basic:MCDR Plugin`
and using the :meth:`~mcdreforged.plugin.si.plugin_server_interface.PluginServerInterface.register_server_handler` API

Python Example
^^^^^^^^^^^^^^

Here's the same example as the :ref:`customize/handler:Handler Spec Example`, implemented in Python:
create a MCDR plugin with the following code as its entrypoint, which registers a handler that recognizes player names with prefixes

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
                if m is not None and self.validate_player_name(m['name']):
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
                        if m is not None and self.validate_player_name(m['name']):
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

As a alternative but **not recommended** way, you may provide your handler by a single ``.py`` file, rather than a plugin

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
