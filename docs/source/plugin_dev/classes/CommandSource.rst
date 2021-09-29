
CommandSource
=============

CommandSource is an abstracted command executor model. It provides several methods for command execution

Class inheriting tree:

.. code-block::

   CommandSource
    ├─ InfoCommandSource
    │   ├─ PlayerCommandSource
    │   └─ ConsoleCommandSource
    └─ PluginCommandSource

Plugins can declare a class inherited from ``CommandSource`` to create their own command source

Property
--------

is_player
^^^^^^^^^

An ``@property`` decorated method

If the command source is a player command source

Type: bool

is_console
^^^^^^^^^^

An ``@property`` decorated method

If the command source is a console command source

Type: bool

player
^^^^^^

**Only in PlayerCommandSource**

The name of the player

Type: str

Method
------

get_server
^^^^^^^^^^

.. code-block:: python

    def get_server(self) -> ServerInterface

Return the server interface instance

get_info
^^^^^^^^

.. code-block:: python

    def get_info(self) -> Info

**Only in InfoCommandSource**

Return the Info instance that this command source is created from

It's only available in command source originated from an info created by MCDR

get_permission_level
^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    def get_permission_level(self) -> int

Return the permission level representing by an int that the command source has

get_preference
^^^^^^^^^^^^^^

.. code-block:: python

    def get_preference(self) -> PreferenceItem

Return the preference of the command source

See `get_preference <ServerInterface.html#get-preference>`__ for related information

preferred_language_context
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    @contextmanager
    def preferred_language_context(self)

A quick helper method to use the language value in preference to create a context with ``RTextMCDRTranslation.language_context``

See `RTextMCDRTranslation <../api.html#rtextmcdrtranslation>`__ for related information

Example usage:

.. code-block:: python

    with source.preferred_language_context():
        text.set_click_event(RAction.suggest_command, source.get_server().rtr('my_plugin.placeholder').to_plain_text())

has_permission
^^^^^^^^^^^^^^

.. code-block:: python

    def has_permission(self, level: int) -> bool:
        return self.get_permission_level() >= level

Return if the command source has not less level than the given permission level

has_permission_higher_than
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    def has_permission_higher_than(self, level: int) -> bool:
        return self.get_permission_level() > level

Just like the `has_permission <#has-permission>`__, but this time it is a greater than judgment

reply
^^^^^

.. code-block:: python

    def reply(self, message: Any, **kwargs) -> None

Send a message to the command source. The message can be anything including RTexts

The message will be converted to str using ``str()`` function unless it's a RTextBase object

Keyword Parameter *encoding*: The encoding method for the text. It's only used in PlayerCommandSource to optionally specify the encoding method. Check `here <ServerInterface.html#execute>`__ for more details
