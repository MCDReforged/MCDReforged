
Metadata
========

Declaration
-----------

As a single ``.py`` file only plugin, the metadata of :ref:`plugin_dev/plugin_format:Solo Plugin` is declared in the global scope of the source file. It's a dict contains several key-value with the name ``PLUGIN_METADATA``

Here's a metadata example

.. code-block:: python

    PLUGIN_METADATA = {
        'id': 'my_plugin_id',
        'version': '1.0.0',
        'name': 'My Plugin',
        'description': 'A plugin to do something cool',
        'authors': ['myself'],
        'links': {
            'homepage': 'https://github.com',
        },
        'dependencies': {
            'mcdreforged': '>=2.16.0',
            'an_important_api': '*'
        }
    }

The following section `Fields <#fields>`__ will use metadata declared in python syntax as examples

---------

For multi file plugin, the metadata is declared in file ``mcdreforged.plugin.json`` in json syntax

Here's an example

.. code-block:: json

    {
        "schema_version": 1,
        "id": "example_plugin",
        "version": "1.0.0",
        "name": "Example Plugin",
        "description": "Example plugin for MCDR",
        "authors": [
            {"name": "Fallen_Breath"}
        ],
        "links": {
            "source": "https://github.com/MCDReforged/MCDReforged-ExamplePlugin"
        },
        "dependencies": {
            "mcdreforged": ">=2.16.0"
        }
    }


If a solo plugin doesn't declare the metadata field, a warning will arise in the console and the fallback values will be used

For multi file plugins, the metadata file and its ``id`` and ``version`` fields are required

.. tip::

    For python package requirements, it's suggested to declare them in a file named ``requirements.txt``, then :doc:`pack </cli/pack>` it into your packed plugin

Fields
------

schema_version
^^^^^^^^^^^^^^

The format version of ``mcdreforged.plugin.json``. Use ``1`` for the format introduced in v2.16.0.
Omitting this field means version ``0`` and remains supported.
If the version is newer than MCDR supports, MCDR will warn and attempt to read the known fields

This does not replace the plugin's ``version`` or its ``mcdreforged`` dependency requirement

.. attention::

    Only used in ``mcdreforged.plugin.json``, not in solo plugin metadata

.. versionadded:: v2.16.0

* Field key: ``schema_version``
* Value type: int
* Fallback value: ``0``

id
^^

ID, or plugin id, is the identity string of your plugin. It should start with a lowercase letter and consist of lowercase letters, numbers and underscores with a length of 1 to 64

Here's some available plugin ids:


* ``my_plugin``
* ``anotherhelper123``
* ``a_cool_plugin``

But the following ids are not allowed:


* ``MyPlugin``
* ``another-helper-123``
* ``a cool plugin``

MCDR uses plugin id to distinguish between different plugins and check the dependencies. All loaded plugin in MCDR contain different plugin ids. If a newly loaded plugin has a plugin id exactly the same with an existed plugin, the new plugin will fail to load

Choose your plugin id wisely. It's highly suggested to keep your plugin id not changed after release your plugin

.. attention::

    Be careful about potential package name conflict. It is not recommended to take an id that is the same as the
    standard library / third-party library name for your plugin, e.g. ``test``, otherwise MCDR might not able to load your plugin correctly


* Field key: ``id``
* Value type: str
* Fallback value: the file name without the ``.py`` extension if it's a solo plugin

version
^^^^^^^

The version value indicates the version of your plugin. It's mostly in `semver <https://semver.org/>`__ format but it has less restriction such as you can have the core version with any length

Here's some available version:


* ``1.0.0``
* ``2.0``
* ``1.2.3-pre4``
* ``1.8.9-rc.8``
* ``1.14.1-beta.4+build.54``

Following `semver <https://semver.org/>`__ format for you version string is a good idea. It's easier to maintain and for people to understand


* Field key: ``version``
* Value type: str
* Fallback value: ``0.0.0`` for solo plugins; required for multi file plugins

name
^^^^

The name of your plugin. Give your plugin with a nice name with any kinds of characters

Try not to make the name too long. For more details of your plugin, you can put them into the ``description``


* Field key: ``name``
* Value type: str
* Fallback value: The plugin id

description
^^^^^^^^^^^

The description of you plugin. Go write down the functionality summarize of your plugin here

This field is optional, you can just ignore it if you are lazy

For translation purpose, instead of using a ``str`` as the value, you can use a Dict[str, str] indicating a mapping from language to description as value, e.g.:

.. code-block:: json

    "description": {
        "en_us": "My description in English",
        "zh_cn": "我的中文简介"
    }


* Field key: ``description``
* Value type: Union[str, Dict[str, str]]
* Fallback value: None

author
^^^^^^

.. deprecated:: v2.16.0
    Use :ref:`plugin_dev/metadata:authors` instead. This field remains supported.
    When both fields are provided, names from ``author`` are appended to ``authors`` without deduplication

The authors of the plugins. If there's only a single author, you can also use a string instead of a list of string

This field is optional, you can just ignore it if you are lazy


* Field key: ``author``
* Value type: str or List[str]
* Fallback value: None

authors
^^^^^^^

The original authors and main creators of the plugin. Each person can be a string containing their name,
or a dict with a required ``name`` and optional ``email`` and ``homepage`` string fields.
You can provide a single person or a list of people, mixing strings and dicts

.. code-block:: python

    'authors': [
        'Alice',
        {
            'name': 'Bob',
            'email': 'bob@example.com',
            'homepage': 'https://example.com/bob',
        }
    ]

.. versionadded:: v2.16.0

* Field key: ``authors``
* Value type: str or Dict[str, str] or List[Union[str, Dict[str, str]]]
* Fallback value: None

maintainers
^^^^^^^^^^^

The people currently maintaining the plugin. This field uses the same format as :ref:`plugin_dev/metadata:authors`

.. versionadded:: v2.16.0

* Field key: ``maintainers``
* Value type: str or Dict[str, str] or List[Union[str, Dict[str, str]]]
* Fallback value: None

link
^^^^

.. deprecated:: v2.16.0
    Use :ref:`plugin_dev/metadata:links` instead. This field remains supported.
    Its value is used as ``links.homepage`` when that value is missing or None

The url to your plugin. You can put a link to the github repository of your plugin here. It should be an available url

This field is optional, you can just ignore it if you are lazy


* Field key: ``link``
* Value type: str
* Fallback value: None

links
^^^^^

Links related to the plugin. All of the following keys are optional:

* ``homepage``: The plugin homepage
* ``source``: The source code repository
* ``documentation``: The documentation page
* ``issues``: The issue tracker

.. code-block:: python

    'links': {
        'homepage': 'https://example.com',
        'source': 'https://github.com/example/my_plugin',
        'issues': 'https://github.com/example/my_plugin/issues'
    }

.. versionadded:: v2.16.0

* Field key: ``links``
* Value type: Dict[str, Optional[str]]
* Fallback value: None

license
^^^^^^^

The license of the plugin. An `SPDX license identifier <https://spdx.org/licenses/>`__, such as ``LGPL-3.0``, is recommended

.. versionadded:: v2.16.0

* Field key: ``license``
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
     - The same as ``==``
     - 1.2.3
     - 1.2, 1.2.4
   * - ==
     - ==1.2.3
     - The target version should equal to 1.2.3
     - 1.2.3
     - 1.2, 1.2.4
   * -
     - 1.2.3
     - If the operator is not specified, ``==`` is used as default. In this case the target version should equal to 1.2.3
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

requirements_file
^^^^^^^^^^^^^^^^^

The Python requirements file inside a multi file plugin. This field controls which file is used for dependency checks,
packing and Python dependency installation:

* If omitted, MCDR uses ``requirements.txt`` when it exists
* If set to ``null`` in JSON (``None`` in Python), no requirements file is used
* If set to a string, that file must exist, even when the value is ``"requirements.txt"``

The path is relative to the plugin root and must stay inside it. Absolute paths and ``..`` path components are not allowed.
For example, ``"requirements_file": "deps/runtime.txt"`` selects a file in the plugin's ``deps`` directory

.. attention::

    Not available in solo plugin

.. versionadded:: v2.16.0

* Field key: ``requirements_file``
* Value type: str or None
* Fallback value: Automatically use ``requirements.txt`` if present

entrypoint
^^^^^^^^^^

The :ref:`plugin_dev/basic:entrypoint` module of your plugin

By default the value is the id of your plugin, which means ``my_plugin/__init__.py`` will be the entry point. If the value is ``my_plugin.my_entry`` then ``my_plugin/my_entry.py`` will be the entry point

MCDR will perform the same execution as a solo plugin to the entrypoint, like default event listener registering

.. attention::

    Not available in solo plugin

* Field key: ``entrypoint``
* Value type: str
* Fallback value: The plugin id

archive_name
^^^^^^^^^^^^

The file name of generated ``.mcdr`` packed plugin in CLI

.. attention::

    Not available in solo plugin

.. seealso::

    :ref:`cli/pack:name` option in :doc:`/cli/pack` command in :doc:`/cli/index`

* Field key: ``archive_name``
* Value type: str
* Fallback value: None

resources
^^^^^^^^^

A list of file or folder names that will be packed into the generated ``.mcdr`` packed plugin file in CLI

.. attention::

    Not available in solo plugin

.. seealso::

    :doc:`/cli/pack` command in :doc:`/cli/index`

* Field key: ``resources``
* Value type: List[str]
* Fallback value: None
