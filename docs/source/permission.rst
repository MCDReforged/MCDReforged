
Permission
==========

Overview
--------

There is a simple built-in permission system in MCDR. It can be used by MCDR commands and plugins

There are 5 different levels of permission in total:

.. list-table::
   :header-rows: 1

   * - Name
     - Value
     - Description
   * - owner
     - 4
     - Highest level for those who have the ability to access the physical server. e.g. Server owner
   * - admin
     - 3
     - People with power to control the MCDR and the Minecraft server. e.g. Minecraft OPs
   * - helper
     - 2
     - A group of helper of admin. e.g. Trusted members
   * - user
     - 1
     - A group that normal player will be in
   * - guest
     - 0
     - The lowest level for guest or trollers


The permission level of console input is always the highest level ``owner``

.. seealso::
  
    :ref:`command/mcdr:Permission management`, to learn how to manage permissions using MCDR commands

Permission File
---------------

Permission file ``permission.yml`` is the config and storage file for the system


* `default_level`: The default permission level a new player will get. Default: ``user``
* ``owner``: Names of players with permission ``owner``
* ``admin``: Names of players with permission ``admin``
* ``helper``: Names of players with permission ``helper``
* ``user``: Names of players with permission ``user``
* ``guest``: Names of players with permission ``guest``

Player name list of permission levels can be filled like this:

.. code-block:: yaml

    owner:
    - Notch
    admin:
    - Dinnerbone
    helper:
    - Steve
    - Alex
    user:
    guest:
    - Noob

Permission file supports hot-reload. You can use ``!!MCDR reload permission`` to reload the permission file in-game

.. seealso::

    :ref:`command/mcdr:Hot reloads` command, for more detail about hot reloads
