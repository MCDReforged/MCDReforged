
API Packages for Plugins
========================

When your plugin needs to import something from MCDR, rather than directly import the package you want, you can import the packages in ``mcdreforged.api``

``mcdreforged.api`` is the package for plugin developers to import. By only importing from the api package, the import of the target class in the plugin can be decoupled from the actual location of the target class. If MCDR refactors the target class and moves its location in the future, only importing from the api package can keep your plugin unaffected

all
---

Module path: ``mcdreforged.api.all``

.. code-block:: python

    from mcdreforged.api.all import *

This is the simplest way to import everything you want for plugin development. It's a life saver for lazy man

You can also use the following way as an approach with more security since it doesn't use ``*``

.. code-block:: python

    import mcdreforged.api.all as mcdr

    # access stuffs with mcdr.Something

Continue reading to see what it will actually import

command
-------

Module path: ``mcdreforged.api.command``

``command`` package contains the necessities for building a command tree or create your own command, including command tree node classes, command exceptions and some command utils

For example, if you want the class ``Literal`` and ``IllegalArgument`` for building your command tree ``on_error`` exception handling, you can do it like this

.. code-block:: python

    from mcdreforged.api.command import Literal, IllegalArgument

Of course if you are lazy enough you can just

.. code-block:: python

    from mcdreforged.api.command import *

Class references: :ref:`class-ref-command`

decorator
---------

Module path: ``mcdreforged.api.decorator``

``decorator`` package contains some useful function decorators for plugin development

Class references: :ref:`class-ref-decorators`

event
-----

Module path: ``mcdreforged.api.event``

``event`` package contains the classes for creating custom events, and classes of MCDR built-in events

You might already read the :meth:`~mcdreforged.plugin.si.server_interface.ServerInterface.dispatch_event` method in ``ServerInterface`` class.
It only accepts a ``PluginEvent`` instance as its first parameter. So if you want to dispatch your custom event,
create a ``LiteralEvent`` for simpleness or a custom event class inherited from ``PluginEvent``

exception
---------

Module path: ``mcdreforged.api.exception``

There some custom exceptions that is used in MCDR runtime e.g. :class:`~mcdreforged.plugin.si.server_interface.ServerInterface` methods. Here comes the way to import them

rcon
----

Module path: ``mcdreforged.api.rcon``

Package ``rcon`` contains a single class ``RconConnection``. It's is a simply rcon client for connect to any Minecraft servers that supports rcon protocol

Class references: :ref:`code_references/minecraft_tools:Rcon`

rtext
-----

Module path: ``mcdreforged.api.rtext``

Recommend to read the page `Raw JSON text format <https://minecraft.gamepedia.com/Raw_JSON_text_format>`__ in Minecraft Wiki first

This is an advanced text component library for Minecraft

Inspired by the `MCD stext API <https://github.com/TISUnion/rtext>`__ made by `Pandaria98 <https://github.com/Pandaria98>`__

Class references: :ref:`code_references/minecraft_tools:RText`

types
-----

Module path: ``mcdreforged.api.types``

Who doesn't want a complete type checking to help you reduce silly mistakes etc. when coding your plugin? If you want to add type hints to the server interface or command source parameter, here's the package for you to import those Usually-used classes

.. code-block:: python

    from mcdreforged.api.types import PluginServerInterface, Info

    def on_info(server: PluginServerInterface, info: Info):
        # Now auto completion for server and info parameters should be available for IDE
        pass


utils
-----

Some useful kits

Module path: ``mcdreforged.api.utils``

Class references: :ref:`class-ref-utilities`
