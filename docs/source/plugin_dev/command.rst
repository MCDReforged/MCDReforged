
Command Tree
============

Tired of manually splitting argument and parsing commands? Being annoyed by the complicated argument conditions? Go try the MCDR command building system!

MCDR contains a command tree building system for plugins to build their commands. It behaves like a lite version of Mojang's `brigadier <https://github.com/Mojang/brigadier>`__

Workflow
--------

MCDR maintains a dict to store registered commands. Any value in the storage dict is a list of literal node as a root node of a command tree, and the related key is the literal value of the root literal node. With it, MCDR can quickly find the possible command tree that might accept the incoming command

Every time when a user info is being processed, MCDR will try to parse the user input as a command. It will takes the first segment of the user input as a key to query the command tree storage dict. **If it gets any, it will prevent the info to be sent to the standard input stream of the server** by invoking ``info.cancel_send_to_server()``, then it will let the found command trees to handle the command.

If an command error occurs and the error has not been set to handled, MCDR will sent the default translated command error message to the command source

.. _cmd-tree-quick-peek:

A Quick Peek
------------

Let's peek into the actual operation of a command tree. As an example, let's say that there are 3 kinds of commands:


* ``!!email list``
* ``!!email remove <email_id>``
* ``!!email send <player> <message>``

To implement these commands, we can build a command tree with MCDR like this:

.. code-block::

    Literal('!!email')
     ├─ Literal('list')
     ├─ Literal('remove')
     │   └─ Integer('email_id')
     └─ Literal('send')
         └─ Text('player')
             └─ GreedyText('message')

When MCDR executes the command ``!!email remove 21``, the following things will happen


#. Parsing at node ``Literal('!!email')`` with command ``!!email remove 21``

   #. Literal Node ``Literal('!!email')`` gets the first element of ``!!email remove 21``, it's ``!!email`` and it matches the literal node  
   #. Now the remaining command is ``remove 21``
   #. And then, it searches through its literal children, found the child node ``Literal('remove')`` matches the next literal element ``remove``  
   #. Then it let that child node to handle the rest of the command

#. Parsing at node ``Literal('remove')`` with command ``remove 21``

   #. Literal Node ``Literal('remove')`` gets the first element of ``remove 21``, it's ``remove`` and it matches the literal node
   #. Now the remaining command is ``21``
   #. And then it searches through its literal children, but doesn't found any literal child matches the next element ``21``
   #. So it let its non-literal child ``Integer('email_id')`` to handle the rest of the command

#. Parsing at node ``Integer('email_id')`` with command ``21``

   #. Integer Node ``Integer('email_id')`` gets the first element of ``21``, it's a legal integer
   #. It store the value ``21`` to the context dict with key ``email_id``
   #. And then it finds that the command parsing is already finished so it invokes the callback function with the command source and the context dict as the argument.
   #. The command parsing finishes

This is a quick overview of the implantation logic part of command building system. It's mainly for help you build a perceptual understanding of the command tree based command building system

Matching the literal nodes, parsing the remaining command, storing the parsed value inside the context dict, this is how the command system works

Ways to build your command tree
-------------------------------

If you are familiar with Mojang's `brigadier <https://github.com/Mojang/brigadier>`__ which is used in Minecraft,
or if you need to access the full features of MCDR's command tree building system, check the related :ref:`class references<class-ref-command>` to see how to create command nodes, adding children nodes and setting node attributes

If you are new to this kind of tree based command building system and don't know how to handle with command tree, you can try the :ref:`cmd-tree-builder` tool for easier command tree building

Rather than reading this document, anther good way to learn to use the MCDR command building system is to refer and imitate existing codes
You can also find the command building code of ``!!MCDR`` command in the ``__register_commands`` method of class ``mcdreforged.plugin.permanent.mcdreforged_plugin.MCDReforgedPlugin``

Context
^^^^^^^

Context stores the information of current command parsing. It's a class inherited from dict

Parsed values are stored inside context using the dict method, which means you can use ``context['arg_name']`` to access them

.. _cmd-tree-builder:

Simple Command Builder
----------------------

.. versionadded:: v2.6.0

Being confused about the command tree? Get tired of tree-based command building? Try this tree-free command builder and experience a nice and clean command building process

Declare & Define, that's all you need

Usage
^^^^^

The command tree in the :ref:`cmd-tree-quick-peek` section can be built with the following codes

.. code-block:: python

    from mcdreforged.api.command import SimpleCommandBuilder

    def on_load(server: PluginServerInterface, prev_module):
        builder = SimpleCommandBuilder()

        # declare your commands
        builder.command('!!email list', list_email)
        builder.command('!!email remove <email_id>', remove_email)
        builder.command('!!email send <player> <message>', send_email)

        # define your command nodes
        builder.arg('email_id', Integer)
        builder.arg('player', Text)
        builder.arg('message', GreedyText)

        # done, now register the commands to the server
        builder.register(server)

Where ``list_email``, ``remove_email`` and ``send_email`` are callback functions of the corresponding commands

That's it!

.. seealso::

    Reference of class :class:`~mcdreforged.command.builder.tools.SimpleCommandBuilder`

Customize
---------

MCDR also supports customize an argument node. It might save you same repeated work on building your command

To create a custom a argument node, you need to declare a class inherited from ``AbstractNode``, and then implement the ``parse`` method logic. That's it, the custom node class is ready to be used

Custom exception provides a precise way to handle your exception with ``on_error`` method. If you want to raise a custom exception when your argument node fails to parsing the text, you need to have the custom exception inherited from ``CommandSyntaxError``

Here's a quick example of a custom Argument node, ``PointArgument``. It accepts continuous 3 float input as a coordinate and batch them in to a list as a point. It raises ``IllegalPoint`` if it gets a non-float input, or ``IncompletePoint`` if the command ends before it finishes reading 3 floats

.. code-block:: python

    class IllegalPoint(CommandSyntaxError):
        def __init__(self, char_read: int):
            super().__init__('Invalid Point', char_read)


    class IncompletePoint(CommandSyntaxError):
        def __init__(self, char_read: int):
            super().__init__('Incomplete Point', char_read)


    class PointArgument(ArgumentNode):
        def parse(self, text: str) -> ParseResult:
            total_read = 0
            coords = []
            for i in range(3):
                total_read += len(text[total_read:]) - len(command_builder_util.remove_divider_prefix(text[total_read:]))
                value, read = command_builder_util.get_float(text[total_read:])
                if read == 0:
                    raise IncompletePoint(total_read)
                total_read += read
                if value is None:
                    raise IllegalPoint(total_read)
                coords.append(value)
            return ParseResult(coords, total_read)

For its usage, here's a simple example as well as an input/output table:

.. code-block:: python

    def on_load(server, prev):
        server.register_command(
            Literal('!!mypoint').then(
                PointArgument('pt').
                runs(lambda src, ctx: src.reply('You have input a point ({}, {}, {})'.format(*ctx['pt'])))
            )
        )

.. list-table::
   :header-rows: 1

   * - Input
     - Output
   * - !!mypoint 1 2 3
     - You have input a point (1.0, 2.0, 3.0)
   * - !!mypoint 1 2
     - Incomplete Point: !!mypoint 1 2<--
   * - !!mypoint xxx
     - Invalid Point: !!mypoint xxx<--
   * - !!mypoint 1 2 x
     - Invalid Point: !!mypoint 1 2 x<--

