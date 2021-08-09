
Metadata
========

Declaration
-----------

As a single ``.py`` file only plugin, the metadata of `solo plugin <plugin_format.html#solo-plugin>`__ is declared in the global scope of the source file. It's a dict contains several key-value with the name ``PLUGIN_METADATA``

Here's a metadata field with all possible key-values

.. code-block:: python

    PLUGIN_METADATA = {
        'id': 'my_plugin_id',
        'version': '1.0.0',
        'name': 'My Plugin',
        'description': 'A plugin to do something cool',
        'author': 'myself',
        'link': 'https://github.com',
        'dependencies': {
            'mcdreforged': '>=1.0.0',
            'an_important_api': '*'
        }
    }

The following section `Fields <#fields>`__ will use metadata declared in python syntax as examples

---------

For packed plugin or directory plugin, the metadata is declared in file ``mcdreforged.plugin.json`` in json syntax

Here's an example

.. code-block:: json

    {
        "id": "example_plugin",
        "version": "1.0.0",
        "name": "Example Plugin",
        "description": "Example plugin for MCDR",
        "author": "Fallen_Breath",
        "link": "https://github.com/MCDReforged/MCDReforged-ExamplePlugin",
        "dependencies": {
            "mcdreforged": ">=2.0.0-alpha.1"
        }
    }


If a plugin doesn't not declare the meta data field, a warning will arise in the console and the fallback values will be used

Fields
------

id
^^

Id, or plugin id, is the identity string of your plugin. It should consist of lowercase letters, numbers and underscores with a length of 1 to 64

Here's some available plugin ids:


* ``my_plugin``
* ``anotherhelper123``
* ``__a_cool_plugin__``

But the following ids are not allowed:


* ``MyPlugin``
* ``another-helper-123``
* ``a cool plugin``

MCDR uses plugin id to distinguish between different plugins and check the dependencies. All loaded plugin in MCDR contain different plugin ids. If a newly loaded plugin has a plugin id exactly the same with an existed plugin, the new plugin will fail to load

Choose your plugin id wisely. It's highly suggested to keep your plugin id not changed after release your plugin


* Field key: ``id``
* Value type: str
* Fallback value: the file name without the ``.py`` extension

version
^^^^^^^

The version value indicates the version of your value. It's mostly in `semver <https://semver.org/>`__ format but it has less restriction such as you can have the core version with any length

Here's some available version:


* ``1.0.0``
* ``2.0``
* ``1.2.3-pre4``
* ``1.8.9-rc.8``
* ``1.14.1-beta.4+build.54``

Following `semver <https://semver.org/>`__ format for you version string is a good idea. It's easier to maintain and for people to understand


* Field key: ``version``
* Value type: str
* Fallback value: ``0.0.0``

name
^^^^

The name of your plugin. Give your plugin with a nice name with any kinds of characters

Try not to make the name too long. For more details of your plugin, you can put them into the ``description``


* Field key: ``name``
* Value type: str
* Fallback value: The plugin id

description
^^^^^^^^^^^

The description of you plugin. Put the details of your plugin here

This field is optional, you can just ignore it if you are lazy


* Field key: ``description``
* Value type: str
* Fallback value: None

author
^^^^^^

The authors of the plugins. If there's only a single author, you can also use a string instead of a list of string

This field is optional, you can just ignore it if you are lazy


* Field key: ``author``
* Value type: str or List[str]
* Fallback value: None

link
^^^^

The url to your plugin. You can put a link to the github repository of your plugin here. It should be an available url

This field is optional, you can just ignore it if you are lazy


* Field key: ``link``
* Value type: str
* Fallback value: None

dependencies
^^^^^^^^^^^^

A dict of dependencies you plugin relies on. It's a dict contains several key-value pairs. The key is the id of the plugin that your plugin is relies on, and the value is the version requirement of the plugin that your plugin is relies on

If your plugin has requirement to the version of MCDR, use ``mcdreforged`` as the plugin id

A version requirement is a string than contains several criterions of the version. Criterions are divided by space character, each criterion is made up of an operator and a base version string. Wildcard is allowed when describing the base version

List of the operators:

.. list-table::
   :header-rows: 1

   * - Operator
     - Example
     - Explanation for the example
     - Accepted
     - Unaccepted
   * - >=
     - >=1.2.3
     - The target version should be equal to or newer than 1.2.3
     - 1.2.3, 1.3.0
     - 1.2.0
   * - >
     - >1.2.3
     - The target version should be newer than 1.2.3
     - 1.2.4, 1.3.0
     - 1.2.0, 1.2.3
   * - <=
     - <=1.2.3
     - The target version should be equal to or older than 1.2.3
     - 1.2.3, 1.1.0
     - 1.2.4, 2.0.0
   * - <
     - <1.2.3
     - The target version should be older than 1.2.3
     - 1.1.0
     - 1.2.3, 1.5
   * - =
     - =1.2.3
     - The target version should equal to 1.2.3
     - 1.2.3
     - 1.2, 1.2.4
   * -
     - 1.2.3
     - If the operator is not specified, ``=`` is used as default. In this case the target version should equal to 1.2.3
     - 1.2.3
     - 1.2, 1.2.4
   * - ^
     - ^1.2.3
     - The target version should be equal to or newer than 1.2.3, and the first version segment of the target version should be equal to the base version
     - 1.2.3, 1.2.4, 1.4.4
     - 1.0.0, 2.0.0
   * - ~
     - ~1.2.3
     - The target version should be equal to or newer than 1.2.3, and the first and the second version segment of the target version should be equal to the base version
     - 1.2.3, 1.2.4
     - 1.0.0, 1.4.4, 2.0.0


Check `here <https://docs.npmjs.com/about-semantic-versioning>`__ for more detail to the version requirement

If there are multiple declared criterions, the target version is accepted only when it's accepted by all criterions

Here a dependencies example:

.. code-block:: python

    'dependencies': {
       'mcdreforged': '>=1.0.0 <2.0',
       'my_library': '>=1.0.0',
       'an_important_api': '*',
       'another_api_1': '1.0.*',
       'another_api_2': '2.7.x',
    }

MCDR will make sure only when all dependency requirements are satisfied your plugin will get loaded successfully. Missing dependency, dependency version not match or dependency loop will result in a dependency check failure

This field is optional, you can just ignore it if your plugin doesn't have any dependency


* Field key: ``dependencies``
* Value type: Dict[str, str]
* Fallback value: None

entrypoint
^^^^^^^^^^

**Not available in solo plugin**

The entrypoint module of your plugin

By default the value is the id of your plugin, which means ``my_plugin/__init__.py`` will be the entry point. If the value is ``my_plugin.my_entry`` then ``my_plugin/my_entry.py`` will be the entry point

MCDR will perform the same execution as a solo plugin to the entrypoint, like default listener registering

See `here <basic.html#entrypoint>`__ for entrypoint document

* Field key: ``entrypoint``
* Value type: str
* Fallback value: The plugin id

archive_name
^^^^^^^^^^^^

**Not available in solo plugin**

The file name of generated ``.mcdr`` packed plugin in CLI

See `here <cli.html#name>`__ for more information

* Field key: ``archive_name``
* Value type: str
* Fallback value: None

resources
^^^^^^^^^

**Not available in solo plugin**

A list of file or folder names that will be packed into the generated ``.mcdr`` packed plugin file in CLI

See `here <cli.html#pack>`__ for more information

* Field key: ``resources``
* Value type: List[str]
* Fallback value: None
